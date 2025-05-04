# filepath: infra/queue/celery_app.py
# Sets up Celery application for async prediction processing
import os
from celery import Celery

# Broker URL (use Redis by default)
redis_url = os.getenv("REDIS_BROKER_URL", "redis://localhost:6379/0")
app = Celery("simple_billing_llm", broker=redis_url, backend=redis_url)

# Autodiscover tasks modules
app.autodiscover_tasks(["infra.queue.tasks"])
