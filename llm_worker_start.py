#
""" LLM worker starter
"""
if __name__ == "__main__":
    print("Starting Celery worker for async prediction processing...")
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from infra.queue.celery_app import app
