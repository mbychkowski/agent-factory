import os

import google.auth
from dotenv import load_dotenv

# Load environment variables first so .env is the single source of truth
load_dotenv()

if "GOOGLE_CLOUD_PROJECT" not in os.environ:
    try:
        _, project_id = google.auth.default()
        if project_id:
            os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
    except Exception:
        pass

from . import agent
