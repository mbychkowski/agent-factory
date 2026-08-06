import logging

from fastapi import FastAPI

from gateway.app.routes.github import router as github_router
from gateway.app.routes.health import router as health_router
from gateway.app.routes.tasks import router as tasks_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gateway")

app = FastAPI(
    title="Spec Deliberator Omnichannel Webhook Gateway",
    description="Inbound webhook proxy for GitHub, Slack, Discord, and Gemini Enterprise. Handles signature validation, bot self-loop filtering, and Cloud Tasks/Pub/Sub event dispatching.",
    version="1.0.0",
)

app.include_router(health_router)
app.include_router(github_router)
app.include_router(tasks_router)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
