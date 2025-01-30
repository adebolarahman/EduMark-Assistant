# Streamlit Web Application for EduMark
import sys
import streamlit as st
import asyncio
import os
from datetime import datetime
from pathlib import Path
from streamlit_option_menu import option_menu
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.orchestrator import OrchestratorAgent


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
    </style>
""",
    unsafe_allow_html=True,
)


async def process_submission(file_path: str) -> dict:
    """Process student submission through the AI grading pipeline."""
    try:
        orchestrator = OrchestratorAgent()
        submission_data = {
            "file_path": file_path,
            "submission_timestamp": datetime.now().isoformat(),
        }
        return await orchestrator.process_student_submission(submission_data)
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
            options=["Upload Submission", "About"],
            icons=["cloud-upload", "info-circle"],
            menu_icon="cast",
            default_index=0,
        )

    if selected == "Upload Submission":
        st.header("📄 Student Submission Analysis")
        st.write("Upload your work to receive detailed feedback on strengths, weaknesses, and recommendations.")

        uploaded_file = st.file_uploader(
            "Choose a file (PDF only)",
            type=["pdf"],
            help="Upload a PDF file to analyze.",
        )

        if uploaded_file:
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
                    result = asyncio.run(process_submission(file_path))

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
                            st.write(result["analysis_results"].get("content_analysis", "No analysis available."))
                            st.metric(
                                "Overall Score",
                                f"{result['analysis_results'].get('score', 0)}/100",
                            )

                        # Strengths & Weaknesses tab
                        with tab2:
                            st.subheader("Strengths & Weaknesses")
                            strengths = result.get("analysis_results", {}).get("strengths", [])
                            weaknesses = result.get("analysis_results", {}).get("weaknesses", [])

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
                            recommendations = result.get("recommendations", [])
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
                            #output_dir.mkdir(parents=True, exist_ok=True)  # Create if it doesn't exist
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
