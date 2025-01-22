import os
from pathlib import Path
import logging
from typing import List, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s]: %(message)s:')


list_of_files = [
    "agents/__init__.py",
    "agents/analyzer_agent.py",
    "agents/base_agent.py",
    "agents/extractor_agent.py",
    "agents/grader_agent.py",
    "agents/orchestrator.py",
    "agents/profile_enhancer_agent.py",
    "agents/recommender_agent.py",
    "agents/screener_agent.py",
    "data/__init__.py",
    "data/grade_database.py",
    "db/__init__.py",
    "db/database.py",
    "db/jobs.sqlite",
    "db/schema.sql",
    "db/seed_jobs.py",
    "results/",
    "utils/.DS_Store",
    "utils/app.py", 
    "utils/requirements.txt", 
    ".env",
    "setup.py",
]


def create_directory_and_files(list_of_files: List[Union[str, Path]]) -> None:
    """
    Creates directories and empty files if they don't exist for given file paths.
    
    This function performs the following operations:
    1. Creates necessary directories for each file path if they don't exist
    2. Creates empty files if they don't exist or are empty
    3. Logs the creation of directories and files
    
    Args:
        list_of_files (List[Union[str, Path]]): List of file paths as strings or Path objects
        
    Returns:
        None
    """
    try:
        for filepath in list_of_files:
            # Convert to Path object if string
            filepath = Path(filepath)
            filedir, filename = os.path.split(filepath)

            # Create directory if it doesn't exist and isn't empty
            if filedir != "":
                os.makedirs(filedir, exist_ok=True)
                logging.info(f"Creating directory: {filedir} for the file {filename}")

            # Create empty file if it doesn't exist or is empty
            if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
                with open(filepath, 'w') as f:
                    pass
                logging.info(f"Creating empty file: {filepath}")
            else:
                logging.info(f"{filename} is already created")
                
    except TypeError as e:
        logging.error(f"Invalid input type: {e}")
        raise
    except OSError as e:
        logging.error(f"Error creating directory or file: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    create_directory_and_files(list_of_files)
      
      
    