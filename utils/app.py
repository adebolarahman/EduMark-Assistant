# Streamlit Web Application for EduMark
import sys
import streamlit as st
import asyncio
import os
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from streamlit_option_menu import option_menu
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.orchestrator import OrchestratorAgent
from db.database import EduMarkDatabase


# Configure Streamlit page
st.set_page_config(
    page_title="EduMark Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for styling
st.markdown(
    """
    <style>
        .stProgress .st-bo {
            background-color: #00a0dc;
        }
        .success-text {
            color: #00c853;
        }
        .warning-text {
            color: #ffd700;
        }
        .error-text {
            color: #ff5252;
        }
        .st-emotion-cache-1v0mbdj.e115fcil1 {
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 20px;
        }
        .student-table {
            width: 100%;
            border-collapse: collapse;
        }
        .student-table th, .student-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        .student-table tr:hover {
            background-color: rgba(0, 0, 0, 0.05);
        }
    </style>
""",
    unsafe_allow_html=True,
)


async def process_submission(file_path: str, student_name: str, student_id: str) -> dict:
    """Process student submission through the AI grading pipeline."""
    try:
        orchestrator = OrchestratorAgent()
        submission_data = {
            "file_path": file_path,
            "submission_timestamp": datetime.now().isoformat(),
            "student_name": student_name,
            "student_id": student_id
        }
        result = await orchestrator.process_student_submission(submission_data)
        
        # Save submission to database
        try:
            db = EduMarkDatabase()
            print(f"Database path: {db.db_path}")
            print("Database connection established")
            
            # Extract necessary data for database storage
            score = result.get("analysis_results", {}).get("student_analysis", {}).get("total_score", 0)
            grade = result.get("analysis_results", {}).get("student_analysis", {}).get("grade", "F")
            strengths = result.get("analysis_results", {}).get("student_analysis", {}).get("strengths", [])
            weaknesses = result.get("analysis_results", {}).get("student_analysis", {}).get("weaknesses", [])
            recommendations = result.get("analysis_results", {}).get("student_analysis", {}).get("recommendations", [])
            
            # Extract text content
            extracted_text = result.get("extracted_data", {}).get("raw_text", "")
            topics_covered = ["AI in Education", "Personalized Learning"]  # Default topics
            
            print(f"About to save submission for {student_name} with ID {student_id}")
            print(f"Score: {score}, Grade: {grade}")
            
            # Prepare feedback text
            feedback_text = f"Score: {score}/100, Grade: {grade}. "
            if recommendations:
                feedback_text += f"Recommendations: {'; '.join(recommendations)}"
            
            try:
                # Check for existing student ID before inserting
                with sqlite3.connect(db.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM submissions WHERE student_id = ?", (student_id,))
                    existing_record = cursor.fetchone()

                    if existing_record:
                        # Update existing record instead of creating a duplicate
                        cursor.execute(
                            """
                            UPDATE submissions SET 
                                student_name = ?,
                                submission_text = ?,
                                topics_covered = ?,
                                strengths = ?,
                                weaknesses = ?,
                                feedback = ?,
                                created_at = CURRENT_TIMESTAMP
                            WHERE student_id = ?
                            """,
                            (
                                student_name,
                                extracted_text,
                                json.dumps(topics_covered),
                                json.dumps(strengths),
                                json.dumps(weaknesses),
                                feedback_text,
                                student_id
                            )
                        )
                        conn.commit()
                        submission_id = existing_record[0]
                        print(f"✅ Updated existing submission for student ID {student_id} with submission ID: {submission_id}")
                    else:
                        # No duplicate, insert new record
                        cursor.execute(
                            """
                            INSERT INTO submissions (
                                student_name, student_id, submission_text, 
                                topics_covered, strengths, weaknesses, feedback
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                student_name,
                                student_id,
                                extracted_text,
                                json.dumps(topics_covered),
                                json.dumps(strengths),
                                json.dumps(weaknesses),
                                feedback_text
                            )
                        )
                        conn.commit()
                        submission_id = cursor.lastrowid
                        print(f"✅ Successfully saved new submission to database with ID: {submission_id}")
                
            except Exception as direct_db_error:
                print(f"Error on direct DB operation: {direct_db_error}")
                # Fall back to the class method if necessary
                try:
                    # First check if record exists using the database class
                    submissions = db.search_submissions([], [])
                    existing_submission = next((s for s in submissions if s["student_id"] == student_id), None)
                    
                    if existing_submission:
                        # Update feedback for existing record
                        db.add_feedback(existing_submission["id"], feedback_text)
                        print(f"✅ Updated feedback for existing submission via class method")
                    else:
                        # Create new record
                        submission_id = db.add_submission(student_name, student_id, extracted_text)
                        print(f"✅ Created new submission via class method with ID: {submission_id}")
                except Exception as class_method_error:
                    print(f"Error using class methods: {class_method_error}")
                    raise
                    
        except Exception as e:
            print(f"❌ Error saving to database: {e}")
            import traceback
            traceback.print_exc()
            # Continue even if database save fails
        
        return result
    except Exception as e:
        raise


def save_uploaded_file(uploaded_file) -> str:
    """Save uploaded file and return the file path."""
    try:
        # Create uploads directory if it doesn't exist
        save_dir = Path("uploads")
        save_dir.mkdir(exist_ok=True)

        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = save_dir / f"submission_{timestamp}_{uploaded_file.name}"

        # Save the file
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        return str(file_path)
    except Exception as e:
        st.error(f"Error saving file: {str(e)}")
        raise


def format_date(date_str):
    """Format date from database for display"""
    if not date_str:
        return "Unknown date"
        
    try:
        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return date_obj.strftime("%Y-%m-%d %H:%M")
    except:
        return str(date_str)


def json_deserialize(json_str):
    """Safely deserialize JSON string to Python object"""
    if not json_str:
        return []
    
    try:
        return json.loads(json_str)
    except:
        try:
            # Try to evaluate as a Python literal
            import ast
            return ast.literal_eval(json_str)
        except:
            # Return as is if all else fails
            return json_str


def display_students_tab():
    """Display the students tab with all submissions"""
    st.header("📚 Student Submissions")
    
    try:
        # Create database connection
        db = EduMarkDatabase()
        
        # Get all submissions directly from the database to ensure we get all fields
        try:
            with sqlite3.connect(db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM submissions ORDER BY created_at DESC")
                rows = cursor.fetchall()
                
                submissions = []
                for row in rows:
                    row_dict = dict(row)
                    # Process JSON fields if needed
                    for field in ['topics_covered', 'strengths', 'weaknesses']:
                        if field in row_dict and row_dict[field]:
                            row_dict[field] = json_deserialize(row_dict[field])
                        else:
                            row_dict[field] = []
                    submissions.append(row_dict)
        except Exception as db_error:
            print(f"Error directly querying database: {db_error}")
            # Fall back to the class method
            submissions = db.get_all_submissions()
        
        if not submissions:
            st.info("No student submissions found in the database.")
            return
        
        # Display submissions in a table
        st.write(f"**Total Submissions:** {len(submissions)}")
        
        # Create columns for table
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 3, 1])
        
        with col1:
            st.write("**Student Name**")
        with col2:
            st.write("**Student ID**")
        with col3:
            st.write("**Score**")
        with col4:
            st.write("**Strengths**")
        with col5:
            st.write("**Submission Date**")
        
        # Display each submission row
        for submission in submissions:
            # Add null checks for all fields
            submission_name = submission.get("student_name", "Unknown")
            submission_id = submission.get("student_id", "Unknown")
            submission_feedback = submission.get("feedback", "")
            submission_strengths = submission.get("strengths", [])
            submission_created_at = submission.get("created_at", "")
            submission_text = submission.get("submission_text", "")
            submission_topics = submission.get("topics_covered", [])
            submission_weaknesses = submission.get("weaknesses", [])
            
            # Extract just the score from feedback - simplified display
            score_display = "N/A"
            if submission_feedback and isinstance(submission_feedback, str):
                if "Score:" in submission_feedback:
                    try:
                        # Extract just the score (e.g., "55/100")
                        score_part = submission_feedback.split("Score:")[1].split(",")[0].strip()
                        score_display = score_part
                    except:
                        pass
            
            # Format strengths for display
            strengths_display = "None"
            if submission_strengths and isinstance(submission_strengths, list) and len(submission_strengths) > 0:
                try:
                    strengths_display = ", ".join(submission_strengths[:2])
                    if len(submission_strengths) > 2:
                        strengths_display += "..."
                except:
                    pass
            
            # Format date
            submission_date = format_date(submission_created_at)
            
            # Display row with columns
            col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 3, 1])
            
            with col1:
                st.write(submission_name)
            with col2:
                st.write(submission_id)
            with col3:
                st.write(score_display)
            with col4:
                st.write(strengths_display)
            with col5:
                st.write(submission_date)
            
            # Add expandable details section
            with st.expander("View Details"):
                st.subheader(f"Submission from {submission_name}")
                
                # Create tabs for details
                detail_tab1, detail_tab2, detail_tab3 = st.tabs(
                    ["📝 Content", "💪 Strengths & Weaknesses", "📊 Feedback"]
                )
                
                with detail_tab1:
                    st.write("**Content Preview:**")
                    if submission_text and isinstance(submission_text, str):
                        st.write(submission_text[:500] + "..." if len(submission_text) > 500 else submission_text)
                    else:
                        st.write("No content available")
                    
                    st.write("**Topics Covered:**")
                    if submission_topics and isinstance(submission_topics, list) and len(submission_topics) > 0:
                        for topic in submission_topics:
                            st.write(f"- {topic}")
                    else:
                        st.write("No topics available")
                
                with detail_tab2:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Strengths:**")
                        if submission_strengths and isinstance(submission_strengths, list) and len(submission_strengths) > 0:
                            for strength in submission_strengths:
                                st.success(f"- {strength}")
                        else:
                            st.write("No strengths available")
                    
                    with col2:
                        st.write("**Areas for Improvement:**")
                        if submission_weaknesses and isinstance(submission_weaknesses, list) and len(submission_weaknesses) > 0:
                            for weakness in submission_weaknesses:
                                st.error(f"- {weakness}")
                        else:
                            st.write("No areas for improvement available")
                
                with detail_tab3:
                    st.write("**Feedback:**")
                    if submission_feedback and isinstance(submission_feedback, str):
                        st.info(submission_feedback)
                    else:
                        st.write("No feedback available")
    except Exception as e:
        st.error(f"Error displaying student records: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    # Sidebar navigation
    with st.sidebar:
        st.image(
            "https://img.icons8.com/graduation-cap",
            width=50,
        )
        st.title("EduMark Assistant")
        selected = option_menu(
            menu_title="Navigation",
            options=["Upload Submission", "Student Records", "About"],
            icons=["cloud-upload", "table", "info-circle"],
            menu_icon="cast",
            default_index=0,
        )

    if selected == "Upload Submission":
        st.header("📄 Student Submission Analysis")
        st.write("Upload your work to receive detailed feedback on strengths, weaknesses, and recommendations.")

        # Get student information
        col1, col2 = st.columns(2)
        with col1:
            student_name = st.text_input("Student Name", placeholder="Enter your full name")
        with col2:
            student_id = st.text_input("Student ID", placeholder="Enter your student ID")

        uploaded_file = st.file_uploader(
            "Choose a file (PDF only)",
            type=["pdf"],
            help="Upload a PDF file to analyze.",
        )

        if uploaded_file and student_name and student_id:
            try:
                with st.spinner("Saving uploaded file..."):
                    file_path = save_uploaded_file(uploaded_file)

                st.info("File uploaded successfully! Processing...")

                # Create placeholders for progress bar and status
                progress_bar = st.progress(0)
                status_text = st.empty()

                # Process submission
                try:
                    status_text.text("Analyzing submission...")
                    progress_bar.progress(25)

                    # Run analysis asynchronously
                    result = asyncio.run(process_submission(file_path, student_name, student_id))

                    # Check if the process was successful
                    if result.get("status") == "completed":
                        progress_bar.progress(100)
                        status_text.text("Analysis complete!")

                        # Display results in tabs
                        tab1, tab2, tab3 = st.tabs(
                            ["📊 Analysis", "📈 Strengths & Weaknesses", "💡 Recommendations"]
                        )

                        # Analysis tab
                        with tab1:
                            st.subheader("Submission Analysis")
                            extracted_data = result.get("extracted_data", {}).get("structured_data", {})
                            st.write(extracted_data.get("content", "No analysis available."))
                            
                            score = result.get("analysis_results", {}).get("student_analysis", {}).get("total_score", 0)
                            grade = result.get("analysis_results", {}).get("student_analysis", {}).get("grade", "F")
                            st.metric(
                                "Overall Score",
                                f"{score}/100",
                                f"Grade: {grade}"
                            )

                        # Strengths & Weaknesses tab
                        with tab2:
                            st.subheader("Strengths & Weaknesses")
                            strengths = result.get("analysis_results", {}).get("student_analysis", {}).get("strengths", [])
                            weaknesses = result.get("analysis_results", {}).get("student_analysis", {}).get("weaknesses", [])

                            if strengths:
                                st.success("### Strengths")
                                for item in strengths:
                                    st.write(f"- {item}")
                            else:
                                st.warning("No strengths identified.")

                            if weaknesses:
                                st.error("### Weaknesses")
                                for item in weaknesses:
                                    st.write(f"- {item}")
                            else:
                                st.warning("No weaknesses identified.")

                        # Recommendations tab
                        with tab3:
                            st.subheader("Recommendations")
                            recommendations = result.get("analysis_results", {}).get("student_analysis", {}).get("recommendations", [])
                            if recommendations:
                                for rec in recommendations:
                                    st.info(f"- {rec}", icon="💡")
                            else:
                                st.warning("No specific recommendations available.")

                        # Save results
                        output_dir = Path("results")
                        if not output_dir.exists():  # Check if directory exists
                            try:
                                output_dir.mkdir(parents=True, exist_ok=True)
                                print(f"✅ Created directory: {output_dir}")  # Debugging log
                            except Exception as e:
                                print(f"❌ Error creating results directory: {e}")  # Debugging log
                                st.error(f"Error creating results directory: {str(e)}")
                        output_file = output_dir / f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                        # Try saving the result
                        try:
                            with open(output_file, "w") as f:
                                f.write(str(result))  # Make sure 'result' is a string
                            st.success(f"Results saved to: {output_file}")
                            print(f"✅ Successfully saved results to: {output_file}")  # Debugging log
                        except Exception as e:
                            print(f"❌ Error saving results: {e}")  # Debugging log
                            st.error(f"Error saving results: {str(e)}")

                finally:
                    # Cleanup uploaded file
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        st.error(f"Error removing temporary file: {str(e)}")

            except Exception as e:
                st.error(f"Error handling file upload: {str(e)}")
        elif uploaded_file and (not student_name or not student_id):
            st.warning("Please provide both student name and ID to continue.")

    elif selected == "Student Records":
        display_students_tab()

    elif selected == "About":
        st.header("About EduMark Assistant")
        st.write(
            """
        Welcome to **EduMark Assistant**, your AI-powered submission grading and feedback tool! 🎓
        
        Our system helps you:
        - Analyze submissions for content quality.
        - Identify strengths and weaknesses.
        - Receive personalized recommendations.

        Powered by:
        - **Llama 3.2**: Advanced natural language processing.
        - **Swarm AI Framework**: Specialized AI agents for grading and analysis.
        - **Streamlit**: Modern, interactive web interface.

        Upload a submission to experience the power of AI in education!
        """
        )


if __name__ == "__main__":
    main()