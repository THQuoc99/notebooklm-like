from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter
from app.api import routes_upload, routes_ws
from app.graphql.schema import schema
from app.config import settings
import os

# Ensure data directories exist
os.makedirs(os.path.dirname(settings.FAISS_INDEX_PATH), exist_ok=True)

app = FastAPI(title="NotebookLM-like API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(routes_upload.router, tags=["files"])
app.include_router(routes_ws.router, tags=["websocket"])

# GraphQL
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql", tags=["graphql"])


@app.get("/")
async def root():
    return {"message": "NotebookLM-like API", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
