from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..models import (
    ComparisonResponse,
    IdeaCreationRequest,
    Link,
    Node,
    Opinion,
    OpinionRequest,
    User,
)
from .utils import generate_node_id, slugify

PALETTE = [
    "#c23531",
    "#2f4554",
    "#61a0a8",
    "#d48265",
    "#91c7ae",
    "#749f83",
    "#ca8622",
    "#bda29a",
    "#6e7074",
    "#546570",
]


class StateManager:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        base_path = Path(__file__).resolve().parent.parent
        self._data_dir = base_path / "data"
        self._initial_state_path = self._data_dir / "initial_state.json"
        self._state_path = self._data_dir / "runtime_state.json"
        self._state: Dict[str, List[Dict]] = self._load_state()

    def _load_state(self) -> Dict[str, List[Dict]]:
        self._data_dir.mkdir(parents=True, exist_ok=True)
        if self._state_path.exists():
            with self._state_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        else:
            with self._initial_state_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
            self._save_state(data)
        data.setdefault("nodes", [])
        data.setdefault("links", [])
        data.setdefault("users", [])
        return data

    def _save_state(self, state: Dict) -> None:
        with self._state_path.open("w", encoding="utf-8") as file:
            json.dump(state, file, indent=2)

    def reset(self) -> None:
        with self._lock:
            with self._initial_state_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
            self._state = data
            self._save_state(data)

    def get_state(self) -> Dict:
        with self._lock:
            return json.loads(json.dumps(self._state))

    # User management
    def _allocate_color(self) -> Optional[str]:
        used_colors = {user.get("color") for user in self._state.get("users", []) if user.get("color")}
        for color in PALETTE:
            if color not in used_colors:
                return color
        return None

    def upsert_user(self, name: str) -> User:
        normalized = slugify(name)
        with self._lock:
            for entry in self._state["users"]:
                if entry["id"] == normalized:
                    if name and entry.get("name") != name:
                        entry["name"] = name
                        self._save_state(self._state)
                    return User(**entry)
            user = User(id=normalized, name=name, color=self._allocate_color())
            self._state["users"].append(user.model_dump())
            self._save_state(self._state)
            return user

    def _find_node_index(self, node_id: str) -> Optional[int]:
        for idx, node in enumerate(self._state.get("nodes", [])):
            if node.get("id") == node_id:
                return idx
        return None

    def add_node(self, node: Node) -> Node:
        with self._lock:
            self._state["nodes"].append(node.model_dump())
            self._save_state(self._state)
        return node

    def add_link(self, link: Link) -> Link:
        with self._lock:
            existing = {tuple(sorted((entry.get("source"), entry.get("target")))) for entry in self._state["links"]}
            key = tuple(sorted((link.source, link.target)))
            if key in existing:
                return link
            self._state["links"].append(link.model_dump())
            self._save_state(self._state)
        return link

    def add_opinion(self, request: OpinionRequest) -> Opinion:
        user = self.upsert_user(request.user_name)
        opinion = Opinion(
            user_id=user.id,
            agreement=request.agreement,
            confidence=request.confidence,
            stance=request.stance,
            weight=request.weight,
        )
        with self._lock:
            index = self._find_node_index(request.node_id)
            if index is None:
                raise ValueError(f"Node {request.node_id} not found")
            node = self._state["nodes"][index]
            node.setdefault("opinions", [])
            updated = False
            for entry in node["opinions"]:
                if entry.get("user_id") == user.id:
                    entry.update(opinion.model_dump())
                    updated = True
                    break
            if not updated:
                node["opinions"].append(opinion.model_dump())
            self._save_state(self._state)
        return opinion

    def add_idea(self, request: IdeaCreationRequest) -> Tuple[Node, Optional[Link], Opinion]:
        user = self.upsert_user(request.user_name)
        node_id = generate_node_id("idea", request.title)
        node = Node(
            id=node_id,
            title=request.title,
            summary=request.summary,
            type="idea",
            tags=request.tags,
            importance=request.importance,
            creator_user_id=user.id,
            opinions=[
                Opinion(
                    user_id=user.id,
                    agreement=request.agreement,
                    confidence=request.confidence,
                    stance=request.stance,
                    weight=1.0,
                )
            ],
        )
        link_obj: Optional[Link] = None
        if request.link_target_id:
            link_obj = Link(
                id=generate_node_id("link", node_id, request.link_target_id),
                source=node_id,
                target=request.link_target_id,
                relationship=request.link_type,
                weight=request.link_weight if request.link_weight is not None else 0.5,
                user_id=user.id,
            )
        with self._lock:
            self._state["nodes"].append(node.model_dump())
            if link_obj:
                self._state["links"].append(link_obj.model_dump())
            self._save_state(self._state)
        return node, link_obj, node.opinions[0]

    def extend_with_news(self, nodes: List[Node], links: List[Link]) -> Tuple[List[Node], List[Link]]:
        new_nodes: List[Node] = []
        new_links: List[Link] = []
        with self._lock:
            existing_ids = {entry["id"] for entry in self._state["nodes"]}
            existing_pairs = {tuple(sorted((entry.get("source"), entry.get("target")))) for entry in self._state["links"]}
            for node in nodes:
                if node.id not in existing_ids:
                    self._state["nodes"].append(node.model_dump())
                    new_nodes.append(node)
            for link in links:
                key = tuple(sorted((link.source, link.target)))
                if key not in existing_pairs:
                    self._state["links"].append(link.model_dump())
                    new_links.append(link)
            if new_nodes or new_links:
                self._save_state(self._state)
        return new_nodes, new_links

    def get_user_state(self, user_id: str) -> ComparisonResponse:
        with self._lock:
            nodes = [Node(**node) for node in self._state["nodes"] if node.get("creator_user_id") == user_id or any(
                opinion.get("user_id") == user_id for opinion in node.get("opinions", [])
            )]
            relevant_node_ids = {node.id for node in nodes}
            links = [
                Link(**link)
                for link in self._state["links"]
                if link.get("source") in relevant_node_ids and link.get("target") in relevant_node_ids
            ]
        return ComparisonResponse(user_id=user_id, nodes=nodes, links=links)

    def list_users(self) -> List[User]:
        with self._lock:
            return [User(**user) for user in self._state.get("users", [])]
