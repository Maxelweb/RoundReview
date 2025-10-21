from datetime import datetime

class Log: 
    """ Standard log format """
    DATE_FORMAT = "%Y-%m-%d, %H:%M:%S"

    id: int
    user_id: str
    action: str
    date: datetime

    def __init__(self, db_row:str=None) -> None:
        if db_row is not None:
            if len(db_row) != 4:
                raise ValueError("Unable to unserialize db row in a Log object")
            else:
                self.id = db_row[0]
                self._date = datetime.fromisoformat(db_row[1])
                self.user_id = db_row[2]
                self.action = db_row[3]
    @property
    def date(self) -> str:
        return self._date.strftime(self.DATE_FORMAT)
    
    @property
    def date_obj(self) -> datetime:
        return self._date
    