from enum import Enum
from ..database import Database
from ..config import log

class Property(Enum):
    API_KEY = "api_key"
    WEBHOOK_URL = "webhook_url"

class User:
    id: int
    name: str
    email: str
    deleted: bool
    admin: bool
    _password: str
    properties: dict

    def __init__(self, db_row:dict=None) -> None:
        if db_row is not None:
            if len(db_row) != 6:
                raise ValueError("Unable to unserialize db row in a User object")
            else:
                self.id = db_row[0]
                self.name = db_row[1]
                self.email = db_row[2]
                self._password = db_row[3]
                self.admin = (True if db_row[4]==1 else False)
                self.deleted = (True if db_row[5]==1 else False)
                self._system = db_row[4]==-1
                self.properties = {}

    def reload_from_db(self, db:Database, with_properties:bool=True) -> bool:
        """ Reload user profile and properties """
        try:
            result = db.c.execute(
                "SELECT id, name, email, password, admin, deleted FROM user WHERE id = ?", (self.id,)
            ).fetchone()
            if result is None:
                return False
            self.id, self.name, self.email, self._password, admin, deleted = result
            self.admin = (True if admin == 1 else False)
            self.deleted = (True if deleted == 1 else False)
            self._system = admin == -1
            if with_properties:
                self.load_properties_from_db(db)
            return True
        except Exception as e:
            log.warning(e)
            return False

    def load_properties_from_db(self, db:Database) -> None:
        """ Load user properties """
        result = db.c.execute(
            "SELECT key, value FROM user_property WHERE user_id = ?", (self.id,)
        ).fetchall()
        self.properties = {row[0]: row[1] for row in result}

    def has_prop(self, key:Property|str) -> bool: 
        """ Check if user has property and return true or false """
        prop_key = key.value if isinstance(key, Property) else key
        return self.properties.get(prop_key, None) is not None

    def prop(self, key:Property|str) -> str | None: 
        """ Check if user has property and return it, otherwise None """
        prop_key = key.value if isinstance(key, Property) else key
        return self.properties.get(prop_key, None)

    @property
    def is_system(self) -> bool:
        return self._system
    