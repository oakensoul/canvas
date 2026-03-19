"""Data models for canvas sessions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Self


class SessionStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


@dataclass
class Session:
    slug: str
    org: str
    created: str  # ISO 8601 date: YYYY-MM-DD
    status: SessionStatus
    label: str | None = None

    def to_dict(self) -> dict:
        return {
            "slug": self.slug,
            "org": self.org,
            "created": self.created,
            "label": self.label,
            "status": str(self.status),
        }

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        # Validate created is ISO 8601 date format
        import datetime

        try:
            datetime.date.fromisoformat(data["created"])
        except (ValueError, KeyError) as e:
            raise ValueError(f"Invalid or missing 'created' date: {e}") from e

        return cls(
            slug=data["slug"],
            org=data["org"],
            created=data["created"],
            status=SessionStatus(data["status"]),
            label=data.get("label"),
        )
