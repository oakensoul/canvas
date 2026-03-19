# SPDX-FileCopyrightText: 2025 Oakensoul Studios LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Data models for canvas sessions."""

from __future__ import annotations

import dataclasses
import datetime
from enum import StrEnum
from typing import Any, Self


class SessionStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


_KNOWN_FIELDS = frozenset({"slug", "org", "created", "status", "label", "archived_at"})


@dataclasses.dataclass(frozen=True)
class Session:
    slug: str
    org: str
    created: datetime.date
    status: SessionStatus
    label: str | None = None
    archived_at: datetime.date | None = None
    extra: dict = dataclasses.field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result = dict(self.extra)
        result.update(
            {
                "slug": self.slug,
                "org": self.org,
                "created": self.created.isoformat(),
                "label": self.label,
                "archived_at": self.archived_at.isoformat() if self.archived_at else None,
                "status": str(self.status),
            }
        )
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        # Validate all required fields
        for field in ("slug", "org", "created", "status"):
            if field not in data:
                raise ValueError(f"Missing required field '{field}'")

        # Validate slug and org are strings
        for field in ("slug", "org"):
            if not isinstance(data[field], str):
                raise ValueError(
                    f"Field '{field}' must be a string, got {type(data[field]).__name__}"
                )

        # Validate and parse created date
        try:
            created = datetime.date.fromisoformat(data["created"])  # type: ignore[arg-type]
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid 'created' date: {e}") from e

        # Parse optional archived_at date
        archived_at = None
        if data.get("archived_at"):
            try:
                archived_at = datetime.date.fromisoformat(data["archived_at"])  # type: ignore[arg-type]
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid 'archived_at' date: {e}") from e

        # Collect unknown fields into extra
        extra = {k: v for k, v in data.items() if k not in _KNOWN_FIELDS}

        return cls(
            slug=data["slug"],  # type: ignore[arg-type]
            org=data["org"],  # type: ignore[arg-type]
            created=created,
            status=SessionStatus(data["status"]),  # type: ignore[arg-type]
            label=data.get("label"),  # type: ignore[arg-type]
            archived_at=archived_at,
            extra=extra,
        )
