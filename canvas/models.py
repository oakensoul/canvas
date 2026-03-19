"""Data models for canvas sessions."""

from __future__ import annotations

import dataclasses
import datetime
from enum import StrEnum
from typing import Self


class SessionStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


@dataclasses.dataclass(frozen=True)
class Session:
    slug: str
    org: str
    created: datetime.date
    status: SessionStatus
    label: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "slug": self.slug,
            "org": self.org,
            "created": self.created.isoformat(),
            "label": self.label,
            "status": str(self.status),
        }

    @classmethod
    def from_dict(cls, data: dict[str, str | None]) -> Self:
        # Validate all required fields
        for field in ("slug", "org", "created", "status"):
            if field not in data:
                raise ValueError(f"Missing required field '{field}'")

        # Validate and parse created date
        try:
            created = datetime.date.fromisoformat(data["created"])  # type: ignore[arg-type]
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid 'created' date: {e}") from e

        return cls(
            slug=data["slug"],  # type: ignore[arg-type]
            org=data["org"],  # type: ignore[arg-type]
            created=created,
            status=SessionStatus(data["status"]),  # type: ignore[arg-type]
            label=data.get("label"),  # type: ignore[arg-type]
        )
