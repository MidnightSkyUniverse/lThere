import os
from datetime import datetime

from langchain.vectorstores import Chroma


###################
# Chroma
###################
def db_connect(db_pth: str, embedding):
    """Return handler to existing Chroma DB"""
    return Chroma(persist_directory=db_pth, embedding_function=embedding)

###################
# Supportive functions
###################
def get_path(*args):
    """get path to the config file"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, *args)

def date_today():
    today = datetime.now().strftime('%Y%m%d')
    # Create a table for today
    return f"{today}"

