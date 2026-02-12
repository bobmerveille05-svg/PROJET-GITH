"""Data models for intent graph."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class EdgeType(Enum):
    """Types of relationships between specs."""

    DEPENDS_ON = "depends_on"  # Implementation order dependency
    REFINES = "refines"  # Elaboration relationship
    CONFLICTS_WITH = "conflicts_with"  # Mutually exclusive
    ENABLES = "enables"  # Unlocks new capabilities


@dataclass
class IntentNode:
    """Represents a spec in the intent graph."""

    id: str
    name: str
    intent: str
    ceremony_level: int = 0
    lifecycle_state: str = "DRAFT"
    trust_score: float = 0.5
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert node to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "intent": self.intent,
            "ceremony_level": self.ceremony_level,
            "lifecycle_state": self.lifecycle_state,
            "trust_score": self.trust_score,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IntentNode":
        """Create node from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            intent=data["intent"],
            ceremony_level=data.get("ceremony_level", 0),
            lifecycle_state=data.get("lifecycle_state", "DRAFT"),
            trust_score=data.get("trust_score", 0.5),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data
            else datetime.utcnow(),
        )

    @classmethod
    def from_db_row(cls, row: Any) -> "IntentNode":
        """Create node from database row."""
        return cls(
            id=row["id"],
            name=row["name"],
            intent=row["intent"],
            ceremony_level=row["ceremony_level"],
            lifecycle_state=row["lifecycle_state"],
            trust_score=row["trust_score"] if row["trust_score"] else 0.5,
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            created_at=datetime.fromisoformat(row["created_at"]),
        )


@dataclass
class Edge:
    """Represents a relationship between two specs."""

    source_id: str
    target_id: str
    edge_type: EdgeType
    weight: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        """Convert edge to dictionary."""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "edge_type": self.edge_type.value,
            "weight": self.weight,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Edge":
        """Create edge from dictionary."""
        return cls(
            source_id=data["source_id"],
            target_id=data["target_id"],
            edge_type=EdgeType(data["edge_type"]),
            weight=data.get("weight", 1.0),
        )

    @classmethod
    def from_db_row(cls, row: Any) -> "Edge":
        """Create edge from database row."""
        return cls(
            source_id=row["source_id"],
            target_id=row["target_id"],
            edge_type=EdgeType(row["edge_type"]),
            weight=row["weight"] if row["weight"] else 1.0,
        )


@dataclass
class GraphQuery:
    """Parameters for graph queries."""

    root_id: Optional[str] = None
    edge_types: list[EdgeType] = field(default_factory=list)
    max_depth: Optional[int] = None
    include_metadata: bool = True


@dataclass
class ImpactReport:
    """Results of impact analysis."""

    spec_id: str
    direct_dependents: list[str] = field(default_factory=list)
    transitive_dependents: list[str] = field(default_factory=list)
    affected_count: int = 0
    risk_level: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL

    def __post_init__(self) -> None:
        """Calculate derived fields."""
        self.affected_count = len(
            set(self.direct_dependents) | set(self.transitive_dependents)
        )

        # Determine risk level based on affected count
        if self.affected_count == 0:
            self.risk_level = "LOW"
        elif self.affected_count <= 3:
            self.risk_level = "MEDIUM"
        elif self.affected_count <= 10:
            self.risk_level = "HIGH"
        else:
            self.risk_level = "CRITICAL"
