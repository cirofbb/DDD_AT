from fastapi import FastAPI
from rotas import *

app = FastAPI()

app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Aplicação tá ON!"}