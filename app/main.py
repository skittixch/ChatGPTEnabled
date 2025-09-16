from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .models import (
    IdeaCreationRequest,
    IngestRequest,
    Link,
    Node,
    OpinionRequest,
    User,
    WorldviewResponse,
)
from .services import ingestion
from .services.state_manager import StateManager
from .services.worldview import build_worldview_response

app = FastAPI(title="Causal Blob System", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

state_manager = StateManager()
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
def serve_index() -> HTMLResponse:
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend index not found")
    return HTMLResponse(index_path.read_text(encoding="utf-8"))


@app.get("/api/state")
def get_state() -> dict:
    return state_manager.get_state()


@app.get("/api/users")
def get_users() -> dict:
    users = [user.model_dump() for user in state_manager.list_users()]
    return {"users": users}


@app.post("/api/ideas")
def create_idea(request: IdeaCreationRequest) -> dict:
    node, link, opinion = state_manager.add_idea(request)
    payload = {"node": node.model_dump(), "opinion": opinion.model_dump()}
    if link:
        payload["link"] = link.model_dump()
    return payload


@app.post("/api/opinions")
def update_opinion(request: OpinionRequest) -> dict:
    try:
        opinion = state_manager.add_opinion(request)
    except ValueError as exc:  # pragma: no cover - FastAPI handles HTTP conversion
        raise HTTPException(status_code=404, detail=str(exc))
    return {"opinion": opinion.model_dump()}


@app.post("/api/ingest")
def ingest_news(request: IngestRequest) -> dict:
    state = state_manager.get_state()
    existing_nodes = [Node(**node) for node in state.get("nodes", [])]
    nodes, links = ingestion.fetch_feed(request.feed_url, limit=request.limit, existing_nodes=existing_nodes)
    nodes_added, links_added = state_manager.extend_with_news(nodes, links)
    return {
        "nodes_added": [node.model_dump() for node in nodes_added],
        "links_added": [link.model_dump() for link in links_added],
    }


@app.get("/api/comparison")
def compare_users(user_ids: str) -> dict:
    ids = [value.strip() for value in user_ids.split(",") if value.strip()]
    comparisons = []
    for user_id in ids:
        comparison = state_manager.get_user_state(user_id)
        comparisons.append(comparison.model_dump())
    return {"comparisons": comparisons}


@app.get("/api/worldview", response_model=WorldviewResponse)
def get_worldview() -> WorldviewResponse:
    state = state_manager.get_state()
    users = [User(**user) for user in state.get("users", [])]
    nodes = [Node(**node) for node in state.get("nodes", [])]
    links = [Link(**link) for link in state.get("links", [])]
    return build_worldview_response(users, nodes, links)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
