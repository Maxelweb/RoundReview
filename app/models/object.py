from enum import Enum
from .user import User
from ..database import Database

class ObjectStatus(Enum):
    """ Status enumerator for Objects """
    NO_REVIEW = "No Review"
    PENDING_REVIEW = "Pending Review"
    UNDER_REVIEW = "Under Review"
    REQUIRE_CHANGES = "Require Changes"
    APPROVED = "Approved"

    @staticmethod
    def values() -> list:
        return list(map(lambda t: t.value, ObjectStatus))
    
    @staticmethod
    def keys() -> list:
        return list(map(lambda t: t, ObjectStatus))
    
    @staticmethod
    def get_color(status:'ObjectStatus') -> str:
        if status == status.NO_REVIEW: return "#868b99"
        if status == status.PENDING_REVIEW: return "#3958b6"
        if status == status.UNDER_REVIEW: return "#ba863a"
        if status == status.REQUIRE_CHANGES: return "#b43939"
        if status == status.APPROVED: return "#60a531"

class Object:
    """ Object model """
    DATE_FORMAT = "%Y-%m-%d, %H:%M"

    def __init__(self, id: str, path: int, user_id: int, project_id: int, name: str, 
                 description: str, comments: str, version: str, status: str, upload_date:str, update_date:str, raw: bytes | None = None) -> None:
        self.id = id
        self.path = path
        self.user_id = user_id
        self.project_id = project_id
        self.name = name
        self.description = description
        self.comments = comments
        self.version = version
        self.status = ObjectStatus(status) if status in ObjectStatus.values() else None
        self.upload_date = upload_date
        self.update_date = update_date
        self.raw:bytes|None = raw  # Placeholder for raw data, to be loaded separately if needed
        self.user:User = None

    @classmethod
    def from_db_row(cls, db_row: tuple) -> "Object":
        if len(db_row) != 11:
            raise ValueError("Unable to unserialize db row into an Object instance")
        return cls(
            id=db_row[0],
            path=db_row[1],
            user_id=db_row[2],
            project_id=db_row[3],
            name=db_row[4],
            description=db_row[5],
            comments=db_row[6],
            version=db_row[7],
            status=db_row[8],
            upload_date=db_row[9],
            update_date=db_row[10],
        )
    
    @classmethod
    def from_dict(cls, data: dict) -> "Object":
        required_keys = {"id", "path", "user_id", "project_id", "name", "description", "comments", "version", "status", "update_date", "upload_date"}
        if not required_keys.issubset(data.keys()):
            raise ValueError(f"Missing required keys: {required_keys - data.keys()}")
        
        return cls(
            id=data["id"],
            path=data["path"],
            user_id=data["user_id"],
            project_id=data["project_id"],
            name=data["name"],
            description=data["description"],
            comments=data["comments"],
            version=data["version"],
            status=data["status"],
            raw=data.get("raw", None), # Optional raw data in base64
            upload_date=data["upload_date"],
            update_date=data["update_date"],
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
    
    def load_user(self, db:Database) -> bool:
        result = db.c.execute(
            "SELECT * FROM user WHERE id = ?;",
            (self.user_id,)
        ).fetchone()
        if result is None:
            return False
        self.user = User(db_row=result)
        return True

    def to_dict(self) -> dict:
        output:dict = {
            "id": self.id,
            "path": self.path,
            "user_id": self.user_id,
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "comments": self.comments,
            "version": self.version,
            "status": self.status.value if self.status else None,
            "upload_date": self.upload_date,
            "update_date": self.update_date,
        }
        if self.raw is not None:
            output["raw"] = self.raw
        return output
                
    
    