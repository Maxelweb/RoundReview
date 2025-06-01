from datetime import datetime
from enum import Enum
from ..database import Database

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
                 description: str, comments: str, version: str, status: str) -> None:
        self.id = id
        self.parent_id = parent_id
        self.user_id = user_id
        self.project_id = project_id
        self.name = name
        self.description = description
        self.comments = comments
        self.version = version
        self.status = ObjectStatus(status) if status in ObjectStatus.values() else None

    @classmethod
    def from_db_row(cls, db_row: tuple) -> "Object":
        if len(db_row) != 9:
            raise ValueError("Unable to unserialize db row into an Object instance")
        return cls(
            id=db_row[0],
            parent_id=db_row[1],
            user_id=db_row[2],
            project_id=db_row[3],
            name=db_row[4],
            description=db_row[5],
            comments=db_row[6],
            version=db_row[7],
            status=db_row[8]
        )
    
    @classmethod
    def from_dict(cls, data: dict) -> "Object":
        required_keys = {"id", "parent_id", "user_id", "project_id", "name", 
                         "description", "comments", "version", "status"}
        if not required_keys.issubset(data.keys()):
            raise ValueError(f"Missing required keys: {required_keys - data.keys()}")
        
        return cls(
            id=data["id"],
            parent_id=data["parent_id"],
            user_id=data["user_id"],
            project_id=data["project_id"],
            name=data["name"],
            description=data["description"],
            comments=data["comments"],
            version=data["version"],
            status=data["status"]
        )

    def load_raw(self, db:Database) -> bool:
        result = db.c.execute(
            "SELECT raw FROM object WHERE id = ?;",
            (self.id,)
        ).fetchone()

        if result is None:
            return False

        self.raw = result[0]
        return True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "user_id": self.user_id,
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "comments": self.comments,
            "version": self.version,
            "status": self.status.value if self.status else None
        }
                
    
    