from fastapi import FastAPI
from app.api import router
from app.server import manager

app = FastAPI(title="Quick Commands Starter")
app.include_router(router)
