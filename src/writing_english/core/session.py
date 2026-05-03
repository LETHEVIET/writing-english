from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Session:
    document_path: Optional[str] = None
    prompt: Optional[str] = None
    id: Optional[int] = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    duration_seconds: int = 0
    words_written: int = 0
