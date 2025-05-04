# Result fixes

Result fixes after the review

## SUGGESTED FIXES AND PIPELINE

1. All calculations are done by workers. We defined Celery workers. [IMPLEMENTED]
2. All tasks are put into Redis Async Broker Queue via Celery. [IMPLEMENTED]
3. We changed logic to use inner system classes with queues, repositories, etc. [IMPLEMENTED]
    - Inner system classes with queues, repositories and everything other logic (easy pythonic methods for all user interaction, authrorization, etc)
      - Telegram bot using this inner system like repository.create_user, NOT WITH HTTP API!!!
      - Separate HTTP API (FastAPI) using this inner system like repository.create_user WITH AUTH with password!

##  We need to have next logic

1. User auth (or create) [IMPLEMENTED via user_controller]

2. User makes prediction -> [PARTIALLY IMPLEMENTED]
    - creates task that goes to DB with status 'pending' (balance unchanged) [IMPLEMENTED]
    - refuse when balance empty [IMPLEMENTED]
3. Worker takes task when available (Celery). [IMPLEMENTED]
4. Worker completes tasks and updates DB including user balance. [IMPLEMENTED]
5. Task result is retrieved via GET endpoint; there is no explicit unfreeze since balance updated on completion. [IMPLEMENTED]


## Need to do NOW

Create docker image

RQ worker on docker
(with LLM pipeline with VLLM image installed)
Need to be:
- support vllm (vllm docker image can be used as base for example)
- support CUDA to run LLM's
- shared volume for app code and model weights (huggingface envs path and others big cache paths should lead to shared volume NOT copy to the docker)
If it's possible use the same container for both RQ worker and Redis server itself

HTTP client API and telegram bot apps can be not on docker (for now) but if we have troubles we move it too. For now we will try to use it directly from host os (windows)