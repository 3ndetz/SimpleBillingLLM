FROM vllm/vllm-openai:latest

# Install Python dependencies
WORKDIR /workspace
COPY pyproject.toml ./
RUN pip install celery redis rq fastapi uvicorn

# Default command: start worker (can override in docker-compose)
CMD ["celery", "-A", "infra.queue.celery_app.app", "worker", "--loglevel=info"]