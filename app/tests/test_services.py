from __future__ import annotations

from pathlib import Path

import pytest

from app.models import IdeaCreationRequest, Link, Node, User
from app.services import ingestion
from app.services.state_manager import StateManager
from app.services.worldview import build_worldview_response


@pytest.fixture(scope="function")
def sample_manager() -> StateManager:
    manager = StateManager()
    manager.reset()
    yield manager
    manager.reset()


def test_add_idea_creates_node_and_link(sample_manager: StateManager) -> None:
    state = sample_manager.get_state()
    initial_nodes = len(state["nodes"])
    request = IdeaCreationRequest(
        user_name="Taylor Researcher",
        title="Decentralized storage accelerates adaptation",
        summary="Combining microgrids with local storage unlocks community resilience",
        tags=["resilience", "storage"],
        agreement=0.82,
        confidence=0.7,
        stance="support",
        importance=0.75,
        link_target_id="news-ipcc-warning",
        link_type="supports",
        link_weight=0.6,
    )
    node, link, opinion = sample_manager.add_idea(request)
    updated_state = sample_manager.get_state()
    assert len(updated_state["nodes"]) == initial_nodes + 1
    assert node.title == request.title
    assert opinion.user_id == sample_manager.upsert_user("Taylor Researcher").id
    if link:
        assert link.source == node.id
        assert link.target == request.link_target_id


def test_fetch_feed_from_sample(monkeypatch: pytest.MonkeyPatch) -> None:
    sample_path = Path(__file__).parent / "sample_feed.xml"
    base_nodes = [
        Node(
            id="news-foundation",
            title="Baseline climate finance story",
            summary="",
            type="news",
            tags=["climate", "finance"],
            importance=0.6,
        )
    ]
    nodes, links = ingestion.fetch_feed(str(sample_path), limit=2, existing_nodes=base_nodes)
    assert len(nodes) == 2
    assert all(node.type == "news" for node in nodes)
    assert any(link.relationship in {"supports", "relates"} for link in links)


def test_worldview_projection(sample_manager: StateManager) -> None:
    state = sample_manager.get_state()
    users = [User(**user) for user in state["users"]]
    nodes = [Node(**node) for node in state["nodes"]]
    links = [Link(**link) for link in state["links"]]
    response = build_worldview_response(users, nodes, links)
    assert response.axes
    assert response.projections
    user_ids = {projection.user_id for projection in response.projections}
    assert user_ids.issubset({user.id for user in users})
