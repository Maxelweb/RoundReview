from dataclasses import dataclass
from typing import Optional

@dataclass
class Project:
    id: Optional[int]
    title: str
    deleted: int = 0

    def __init__(self, id: Optional[int], title: str, deleted: int = 0) -> None:
        self.id = id
        self.title = title
        self.deleted = deleted

    @classmethod
    def from_db_row(cls, db_row: tuple) -> "Project":
        if len(db_row) != 3:
            raise ValueError("Unable to unserialize db row into a Project instance")
        return cls(
            id=db_row[0],
            title=db_row[1],
            deleted=db_row[2]
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "deleted": self.deleted
        }

