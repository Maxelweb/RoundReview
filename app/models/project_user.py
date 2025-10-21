from dataclasses import dataclass
from .role import Role


@dataclass
class ProjectUser:
    """ Project User Model """
    project_id: int
    user_id: int
    role: Role | None

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