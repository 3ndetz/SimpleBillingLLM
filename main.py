from fastapi import FastAPI
from infra.web.controllers.user_controller import router as user_router
from infra.web.controllers.prediction_controller import router as prediction_router

app = FastAPI(debug=True,
              title="SimpleBillingLLM API",
              version="0.0.1",
              description="Telegram billing LLM",
)


@app.get("/")
def health():
    return "ok"

@app.get("/version")
def version():
    return app.version

app.include_router(user_router, prefix="/api/v1", tags=["Users"])
app.include_router(prediction_router, prefix="/api/v1", tags=["Predictions"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
    print("Server started at http://127.0.0.1:8000/docs")
# OR fastapi dev main.py
