from __future__ import annotations

import datetime as dt
from typing import Iterable, List, Sequence, Tuple

import feedparser

from ..models import Link, Node
from .utils import generate_node_id, slugify

DEFAULT_FEEDS: Sequence[str] = (
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
)


def _normalize_tags(entry: feedparser.FeedParserDict) -> List[str]:
    tags: List[str] = []
    raw_tags = entry.get("tags", [])
    for tag in raw_tags:
        name = tag.get("term") if isinstance(tag, dict) else tag
        if name:
            tags.append(slugify(str(name)))
    summary = entry.get("summary") or entry.get("description") or ""
    keywords = [word for word in summary.split() if len(word) > 5]
    tags.extend(slugify(word) for word in keywords[:4])
    title_keywords = [word for word in (entry.get("title") or "").split() if len(word) > 5]
    tags.extend(slugify(word) for word in title_keywords[:4])
    return sorted(set(tag for tag in tags if tag))


def _build_node_id(entry: feedparser.FeedParserDict) -> str:
    reference = entry.get("id") or entry.get("guid") or entry.get("link") or entry.get("title")
    if reference:
        return f"news-{slugify(str(reference))}"
    return generate_node_id("news")


def _extract_summary(entry: feedparser.FeedParserDict) -> str:
    summary = entry.get("summary") or entry.get("description") or ""
    return summary.strip()


def _parse_published(entry: feedparser.FeedParserDict) -> str:
    published = entry.get("published_parsed") or entry.get("updated_parsed")
    if published:
        return dt.datetime(*published[:6]).isoformat()
    return dt.datetime.utcnow().isoformat()


def _find_related_nodes(new_tags: Iterable[str], existing_nodes: Sequence[Node]) -> List[Tuple[Node, float]]:
    related: List[Tuple[Node, float]] = []
    new_tag_set = set(new_tags)
    if not new_tag_set:
        return related
    for node in existing_nodes:
        existing_tags = set(node.tags)
        if not existing_tags:
            continue
        overlap = len(new_tag_set & existing_tags)
        if overlap:
            weight = overlap / len(new_tag_set | existing_tags)
            related.append((node, weight))
    related.sort(key=lambda item: item[1], reverse=True)
    return related[:3]


def fetch_feed(
    feed_url: str | None,
    *,
    limit: int = 6,
    existing_nodes: Sequence[Node] | None = None,
) -> Tuple[List[Node], List[Link]]:
    """Fetch RSS/Atom feed entries and transform them into nodes/links."""

    urls = [feed_url] if feed_url else list(DEFAULT_FEEDS)
    nodes: List[Node] = []
    links: List[Link] = []
    existing_nodes = list(existing_nodes or [])

    for url in urls:
        try:
            parsed = feedparser.parse(url)
        except Exception:  # pragma: no cover - feedparser handles errors gracefully
            continue
        feed_title = parsed.feed.get("title", "News Feed") if parsed.feed else "News Feed"
        for entry in parsed.entries[:limit]:
            node_id = _build_node_id(entry)
            if any(node.id == node_id for node in nodes) or any(node.id == node_id for node in existing_nodes):
                continue
            tags = _normalize_tags(entry)
            node = Node(
                id=node_id,
                title=entry.get("title", "Untitled"),
                summary=_extract_summary(entry),
                type="news",
                source=feed_title,
                created_at=_parse_published(entry),
                tags=tags,
                importance=0.6,
                url=entry.get("link"),
                metadata={
                    "author": entry.get("author"),
                    "feed_url": url,
                },
            )
            related_nodes = _find_related_nodes(node.tags, existing_nodes + nodes)
            for related_node, weight in related_nodes:
                link = Link(
                    id=generate_node_id("link", node_id, related_node.id),
                    source=node_id,
                    target=related_node.id,
                    relationship="relates" if related_node.type == "news" else "supports",
                    weight=min(0.9, max(0.2, weight)),
                )
                links.append(link)
            nodes.append(node)
    return nodes, links
