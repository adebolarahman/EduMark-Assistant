import os
from pathlib import Path
import logging

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


for filepath in list_of_files:
   filepath = Path(filepath)
   filedir, filename = os.path.split(filepath)

   if filedir !="":
      os.makedirs(filedir, exist_ok=True)
      logging.info(f"Creating directory; {filedir} for the file {filename}")

   if (not os.path.exists(filepath)) or (os.path.getsize(filepath) == 0):
      with open(filepath, 'w') as f:
         pass
         logging.info(f"Creating empty file: {filepath}")

   else:
      logging.info(f"{filename} is already created")
      
      
    