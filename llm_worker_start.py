#
"""
LLM worker starter
This script is used to start the Celery worker for async prediction processing.
"""

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting Celery worker for async prediction processing...")
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from infra.queue.celery_app import app
