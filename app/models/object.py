from datetime import datetime
from enum import Enum

class ObjectStatus(Enum):
    NO_REVIEW = "No Review"
    PENDING_REVIEW = "Pending Review"
    UNDER_REVIEW = "Under Review"
    REQUIRE_CHANGES = "Require Changes"
    APPROVED = "Approved"

    @staticmethod
    def values() -> list:
        return list(map(lambda t: t.value, ObjectStatus))

class Object:

    DATE_FORMAT = "%Y-%m-%d, %H:%M"

    def __init__(self, id: str, parent_id: int, user_id: int, project_id: int, name: str, 
                 description: str, raw: bytes, comments: str, version: str, status: str) -> None:
        self.id = id
        self.parent_id = parent_id
        self.user_id = user_id
        self.project_id = project_id
        self.name = name
        self.description = description
        self.raw = raw
        self.comments = comments
        self.version = version
        self.status = ObjectStatus(status) if status in ObjectStatus.values() else None

    @classmethod
    def from_db_row(cls, db_row: tuple) -> "Object":
        if len(db_row) != 10:
            raise ValueError("Unable to unserialize db row into an Object instance")
        return cls(
            id=db_row[0],
            parent_id=db_row[1],
            user_id=db_row[2],
            project_id=db_row[3],
            name=db_row[4],
            description=db_row[5],
            raw=db_row[6],
            comments=db_row[7],
            version=db_row[8],
            status=db_row[9]
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "user_id": self.user_id,
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "raw": self.raw,
            "comments": self.comments,
            "version": self.version,
            "status": self.status.value if self.status else None
        }
                
    
    