from datetime import datetime
from enum import Enum

class DocumentStatus(Enum):
    UNDER_REVIEW = "Under Review"
    REQUIRE_CHANGES = "Require Changes"
    APPROVED = "Approved"

    @staticmethod
    def values() -> list:
        return list(map(lambda t: t.value, DocumentStatus))

# FIXME: to refactor
class Document:

    DATE_FORMAT = "%Y-%m-%d, %H:%M"

    id: str
    parent_id: str
    user_id: int
    object_path: str
    title: str
    version: str
    status: DocumentStatus

    def __init__(self, db_row:str=None) -> None:
        if db_row is not None:
            if len(db_row) != 9:
                raise ValueError("Unable to unserialize db row in a document object")
            else:
                raise NotImplementedError()
                # self.id = db_row[0]
                
    
    