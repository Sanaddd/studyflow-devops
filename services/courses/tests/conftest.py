import os
import tempfile

# Point the service at a throwaway database before app.py is imported,
# because app.py creates the tables at import time.
os.environ.setdefault("DATA_DIR", tempfile.mkdtemp())
