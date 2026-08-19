"""The one domain object, and the vocabulary the rest of the service uses."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

# Enforced at the API boundary, not in the database: SQLite has no CHECK worth
# relying on here, and a rejected request is a clearer failure than a truncated
# row. See adr-001-storage.
MAX_TITLE_LENGTH = 200


class Status(StrEnum):
    OPEN = 'open'
    DONE = 'done'


@dataclass(frozen=True)
class Task:
    id: int
    title: str
    status: Status = Status.OPEN
    owner_key: str = ''
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'status': str(self.status),
            'created_at': self.created_at.isoformat(),
        }
