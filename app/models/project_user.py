from dataclasses import dataclass
from enum import Enum

class Role(Enum):
    REVIEWER = "Reviewer"
    EDITOR = "Editor"
    OWNER = "Owner"

    @staticmethod
    def values() -> list:
        return list(map(lambda t: t.value, Role))

@dataclass
class ProjectUser:
    project_id: int
    user_id: int
    role: str

    def __init__(self, project_id: int, user_id: int, role: str) -> None:
        self.project_id = project_id
        self.user_id = user_id
        self.role = Role(role) if role in Role.values() else None

    @classmethod
    def from_db_row(cls, db_row: tuple) -> "ProjectUser":
        if len(db_row) != 3:
            raise ValueError("Unable to unserialize db row into a ProjectUser instance")
        return cls(
            project_id=db_row[0],
            user_id=db_row[1],
            role=db_row[2]
        )

    def to_dict(self) -> dict:
        return {
            "project_id": self.project_id,
            "user_id": self.user_id,
            "role": self.role
        }