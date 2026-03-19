"""Data models for canvas sessions."""

from __future__ import annotations

import datetime
import re
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

    def to_dict(self) -> dict[str, str | None]:
        return {
            "slug": self.slug,
            "org": self.org,
            "created": self.created,
            "label": self.label,
            "status": str(self.status),
        }

    @classmethod
    def from_dict(cls, data: dict[str, str | None]) -> Self:
        # Validate all required fields
        for field in ("slug", "org", "created", "status"):
            if field not in data:
                raise ValueError(f"Missing required field '{field}'")

        # Validate created is ISO 8601 date format
        try:
            datetime.date.fromisoformat(data["created"])  # type: ignore[arg-type]
        except ValueError as e:
            raise ValueError(f"Invalid 'created' date: {e}") from e

        return cls(
            slug=data["slug"],  # type: ignore[arg-type]
            org=data["org"],  # type: ignore[arg-type]
            created=data["created"],  # type: ignore[arg-type]
            status=SessionStatus(data["status"]),  # type: ignore[arg-type]
            label=data.get("label"),  # type: ignore[arg-type]
        )
