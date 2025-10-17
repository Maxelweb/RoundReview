
class Review:
    """ Review model to use for objects """
    def __init__(self, 
                id: str, 
                name: str,
                value: str,
                created_at: str,
                user_id: int,
                object_id: str,
                icon: str = None,
                url: str = None,
                url_text: str = None,
        ) -> None:
        self.id = id
        self.name = name
        self.value = value
        self.created_at = created_at
        self.user_id = user_id
        self.object_id = object_id
        self.icon = icon
        self.url = url
        self.url_text = url_text

    @classmethod
    def from_db_row(cls, db_row: tuple) -> "Review":
        if len(db_row) != 9:
            raise ValueError("Unable to unserialize db row into an Object Integration Review instance")
        return cls(
            id=db_row[0],
            name=db_row[1],
            icon=db_row[2],
            url=db_row[3],
            url_text=db_row[4],
            value=db_row[5],
            created_at=db_row[6],
            user_id=db_row[7],
            object_id=db_row[8],
        )

    def to_dict(self) -> dict:
        output:dict = {
            "id": self.id,
            "name": self.name,
            "icon": self.icon,
            "url": self.url,
            "url_text": self.url_text,
            "value": self.value,
            "created_at": self.created_at,
            "user_id": self.user_id,
            "object_id": self.object_id,
        }
        return output
    
    @classmethod
    def from_dict(cls, data: dict) -> "Review":
        required_keys = ["id", "name", "value", "created_at", "user_id", "object_id"]
        if not all(key in data for key in required_keys):
            raise ValueError("Unable to unserialize dict into an Object Integration Review instance")
        return cls(
            id=data["id"],
            name=data["name"],
            icon=data.get("icon"),
            url=data.get("url"),
            url_text=data.get("url_text"),
            value=data["value"],
            created_at=data["created_at"],
            user_id=data["user_id"],
            object_id=data["object_id"],
        )
    
    