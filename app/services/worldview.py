from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

import numpy as np

from ..models import Link, Node, Opinion, User, WorldviewProjection, WorldviewResponse


def _collect_user_nodes(nodes: Iterable[Node], user_id: str) -> List[Node]:
    owned: List[Node] = []
    for node in nodes:
        if node.creator_user_id == user_id:
            owned.append(node)
            continue
        if any(opinion.user_id == user_id for opinion in node.opinions):
            owned.append(node)
    return owned


def _collect_user_opinions(node: Node, user_id: str) -> List[Opinion]:
    return [opinion for opinion in node.opinions if opinion.user_id == user_id]


def _compute_feature_vector(user: User, nodes: List[Node], links: List[Link]) -> Tuple[Dict[str, float], bool]:
    if not nodes:
        return {}, False
    all_opinions: List[Opinion] = []
    link_touch_count = 0
    node_ids = {node.id for node in nodes}
    for node in nodes:
        opinions = _collect_user_opinions(node, user.id)
        all_opinions.extend(opinions)
    for link in links:
        if link.user_id == user.id or (link.source in node_ids and link.target in node_ids):
            link_touch_count += 1
    opinion_count = max(1, len(all_opinions))
    tag_diversity = len({tag for node in nodes for tag in node.tags}) / max(1, len(nodes))
    idea_nodes = [node for node in nodes if node.type == "idea"]
    news_nodes = [node for node in nodes if node.type == "news"]

    support_count = sum(1 for opinion in all_opinions if opinion.stance == "support")
    contradict_count = sum(1 for opinion in all_opinions if opinion.stance == "contradict")
    neutral_count = sum(1 for opinion in all_opinions if opinion.stance == "neutral")

    agreement = sum(opinion.agreement for opinion in all_opinions) / opinion_count
    confidence = sum(opinion.confidence for opinion in all_opinions) / opinion_count

    features = {
        "agreement": agreement,
        "confidence": confidence,
        "support_ratio": support_count / opinion_count,
        "contradiction_ratio": contradict_count / opinion_count,
        "neutral_ratio": neutral_count / opinion_count,
        "originality_ratio": len(idea_nodes) / max(1, len(nodes)),
        "evidence_ratio": len(news_nodes) / max(1, len(nodes)),
        "tag_diversity": tag_diversity,
        "link_density": link_touch_count / max(1, len(nodes)),
    }
    return features, True


def compute_user_features(users: Iterable[User], nodes: Iterable[Node], links: Iterable[Link]) -> Dict[str, Dict[str, float]]:
    features: Dict[str, Dict[str, float]] = {}
    node_list = list(nodes)
    link_list = list(links)
    for user in users:
        owned_nodes = _collect_user_nodes(node_list, user.id)
        vector, ok = _compute_feature_vector(user, owned_nodes, link_list)
        if ok:
            features[user.id] = vector
    return features


def project_features(feature_map: Dict[str, Dict[str, float]]) -> Tuple[List[str], Dict[str, List[float]], List[float]]:
    if not feature_map:
        return [], {}, []
    user_ids = list(feature_map.keys())
    feature_names = list(next(iter(feature_map.values())).keys())
    matrix = np.array([[feature_map[user_id][name] for name in feature_names] for user_id in user_ids])

    if matrix.shape[0] == 1:
        dim_count = min(3, matrix.shape[1])
        coords = np.zeros((1, dim_count))
        explained = [1.0] + [0.0] * (dim_count - 1)
        axes = [f"Axis {idx+1}" for idx in range(dim_count)]
    else:
        mean = matrix.mean(axis=0)
        centered = matrix - mean
        cov = np.cov(centered, rowvar=False)
        eigvals, eigvecs = np.linalg.eigh(cov)
        order = np.argsort(eigvals)[::-1]
        eigvals = eigvals[order]
        eigvecs = eigvecs[:, order]
        components = eigvecs[:, : min(3, eigvecs.shape[1])]
        coords = centered @ components
        total = float(eigvals.sum()) or 1.0
        explained = [float(val / total) for val in eigvals[: components.shape[1]]]
        axes = [f"Dimension {idx+1}" for idx in range(components.shape[1])]

    projection_map = {user_id: coords[idx].tolist() for idx, user_id in enumerate(user_ids)}
    return axes, projection_map, explained


def build_worldview_response(users: Iterable[User], nodes: Iterable[Node], links: Iterable[Link]) -> WorldviewResponse:
    users = list(users)
    nodes = [node if isinstance(node, Node) else Node(**node) for node in nodes]
    links = [link if isinstance(link, Link) else Link(**link) for link in links]
    feature_map = compute_user_features(users, nodes, links)
    axes, projection_map, explained = project_features(feature_map)

    projections: List[WorldviewProjection] = []
    for user in users:
        if user.id not in projection_map:
            continue
        projections.append(
            WorldviewProjection(
                user_id=user.id,
                name=user.name,
                coordinates=projection_map[user.id],
                features=feature_map[user.id],
            )
        )
    return WorldviewResponse(axes=axes, projections=projections, explained_variance=explained)
