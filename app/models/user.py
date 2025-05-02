class User:
    id: int
    name: str
    email: str
    deleted: bool
    admin: bool
    _password: str

    def __init__(self, db_row:str=None) -> None:
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
    @property
    def is_system(self) -> bool:
        return self._system
    