from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class Opinion(BaseModel):
    user_id: str = Field(..., description="ID of the user expressing the opinion")
    agreement: float = Field(..., ge=0.0, le=1.0, description="Agreement score between 0 and 1")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    stance: Literal["support", "contradict", "neutral"] = Field(
        ..., description="Whether the opinion supports, contradicts, or is neutral"
    )
    weight: float = Field(0.5, ge=0.0, le=1.0, description="Relative importance of this opinion")


class Node(BaseModel):
    id: str
    title: str
    summary: str = ""
    type: Literal["news", "idea", "analysis"] = "idea"
    source: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    tags: List[str] = Field(default_factory=list)
    importance: float = Field(0.5, ge=0.0, le=1.0)
    creator_user_id: Optional[str] = None
    url: Optional[str] = None
    opinions: List[Opinion] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("tags", mode="before")
    @classmethod
    def _normalize_tags(cls, value: Optional[List[str]]) -> List[str]:
        if not value:
            return []
        return [tag.strip().lower() for tag in value if tag]


class Link(BaseModel):
    id: str
    source: str
    target: str
    relationship: Literal["supports", "contradicts", "relates"] = "relates"
    weight: float = Field(0.5, ge=0.0, le=1.0)
    description: Optional[str] = None
    user_id: Optional[str] = None


class User(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class IdeaCreationRequest(BaseModel):
    user_name: str
    title: str
    summary: str
    tags: List[str] = Field(default_factory=list)
    agreement: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    stance: Literal["support", "contradict", "neutral"]
    importance: float = Field(0.5, ge=0.0, le=1.0)
    link_target_id: Optional[str] = None
    link_type: Literal["supports", "contradicts", "relates"] = "relates"
    link_weight: Optional[float] = Field(0.5, ge=0.0, le=1.0)


class OpinionRequest(BaseModel):
    user_name: str
    node_id: str
    agreement: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    stance: Literal["support", "contradict", "neutral"]
    weight: float = Field(0.5, ge=0.0, le=1.0)


class IngestRequest(BaseModel):
    feed_url: Optional[str] = None
    limit: int = Field(6, ge=1, le=20)


class ComparisonResponse(BaseModel):
    user_id: str
    nodes: List[Node]
    links: List[Link]


class WorldviewProjection(BaseModel):
    user_id: str
    name: str
    coordinates: List[float] = Field(description="Projected coordinates in worldview space")
    features: Dict[str, float]


class WorldviewResponse(BaseModel):
    axes: List[str]
    projections: List[WorldviewProjection]
    explained_variance: List[float]
