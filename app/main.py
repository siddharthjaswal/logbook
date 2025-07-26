from fastapi import FastAPI

from .api import trips

app = FastAPI()

app.include_router(trips.router)