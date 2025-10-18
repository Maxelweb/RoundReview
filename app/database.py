import hashlib
import random
import datetime
import re
from pathlib import Path
from sqlite3 import connect, Cursor, Error
from .config import (
    log, 
    USER_SYSTEM_ID,
    USER_SYSTEM_NAME,
    USER_SYSTEM_EMAIL,
    USER_ADMIN_NAME,
    USER_ADMIN_EMAIL,
    USER_DEFAULT_PASSWORD,
    SYSTEM_MAX_UPLOAD_SIZE_MB
)

class Database:

    def __init__(self, file_path:str="database/roundreview.db") -> None:
        self._file_path = file_path
        try:
            self._client = connect(self._file_path)
        except Error as error:
            log.fatal(f"Unable to connect to DB: {error}")
            exit(1)
        self._cursor = self._client.cursor()
    
    def initialize(self) -> None:
        if self.__update_db_schema_version():
            log.info("Database schema version initialized / updated correctly!")
        else:
            log.fatal("Unable to update schema in the database. Please check the logs.")
            exit(1)
        
        if self.c.execute("SELECT name FROM user WHERE admin = -1").fetchone() is None:
            self.__create_user_system()
            self.log(USER_SYSTEM_ID, f"user add (user_id={USER_SYSTEM_ID})")
        else: 
            log.info("System user already created")

        if self.c.execute("SELECT name FROM user WHERE admin = 1").fetchone() is None:
            self.__create_user_admin()
            self.log(USER_SYSTEM_ID, f"user add (user_id={(USER_SYSTEM_ID+1)})")
        else: 
            log.info("Admin user already created")

    def close(self) -> None:
        self._client.close()

    @property
    def c(self) -> Cursor:
        return self._cursor
    
    def commit(self) -> None:
        return self._client.commit()

    @staticmethod
    def hash(password:str) -> str:
        return hashlib.sha512(password.encode("utf-8")).hexdigest()

    def log(self, user_id:int, action:str) -> None:
        log.info(f"USER_ID {user_id} -> {action}")
        self.c.execute(
            'INSERT INTO log (date, user_id, action) VALUES (?, ?, ?);', 
            (datetime.datetime.now().isoformat(), 
            user_id,
            action)
        )
        self.commit()

    def __create_user_system(self) -> None:
        # Add system user
        self.c.execute(
            'INSERT INTO user (name, email, password, admin) VALUES (?, ?, ?, ?);', 
            (USER_SYSTEM_NAME,
            USER_SYSTEM_EMAIL,
            Database.hash(random.randbytes(16).hex()),
            -1)
        )
        self.commit()
        # Add default properties for system user
        self.c.executemany(
            'INSERT INTO user_property (key, value, user_id) VALUES (?, ?, ?);', [
                ("PROJECT_CREATE_DISABLED", "FALSE", USER_SYSTEM_ID),
                ("OBJECT_DELETE_DISABLED", "FALSE", USER_SYSTEM_ID),
                ("USER_LOGIN_DISABLED", "FALSE", USER_SYSTEM_ID),
                ("OBJECT_MAX_UPLOAD_SIZE_MB", SYSTEM_MAX_UPLOAD_SIZE_MB, USER_SYSTEM_ID),
                ("WEBHOOKS_DISABLED", "FALSE", USER_SYSTEM_ID)
            ])
        self.commit()

    def __create_user_admin(self) -> None:
        self.c.execute(
            'INSERT INTO user (name, email, password, admin) VALUES (?, ?, ?, ?);', 
            (USER_ADMIN_NAME,
            USER_ADMIN_EMAIL,
            Database.hash(USER_DEFAULT_PASSWORD),
            1)
        )
        self.commit()
        log.warning("Default admin user %s created with password: %s", USER_ADMIN_EMAIL, USER_DEFAULT_PASSWORD)

    def __update_db_schema_version(self) -> bool:

        schemas = []
        has_db_version = self.c.execute("SELECT 1 FROM sqlite_master WHERE name = 'rr_db_version'").fetchone()
        schema_dir = Path(__file__).resolve().parent / "schema"

        # Get all the schemas and corresponding ids
        if not schema_dir.exists() or not schema_dir.is_dir():
            log.fatal("Database schema directory not found: %s", schema_dir)
            return False

        for p in schema_dir.iterdir():
            if not p.is_file():
                continue
            m = re.match(r"^(\d+)", p.name)
            if not m:
                continue
            try:
                ver = int(m.group(1))
            except ValueError:
                continue
            schemas.append((ver, p))

        schemas.sort(key=lambda x: x[0])
        latest_version = schemas[-1][0] if schemas else -1

        # Check for first installation and current db version
        if has_db_version is None:
            current_version = -1
        else:
            db_version = self.c.execute("SELECT id FROM rr_db_version ORDER BY id DESC LIMIT 1").fetchone()
            current_version = db_version[0] if db_version else -1
        
        # Evaluate action based on the db version and the schema version
        if current_version == latest_version:
            log.info("Database schema up-to-date (version %s)", current_version)
        elif current_version > latest_version:
            log.warning("Database version (%s) has a higher schema version than the available (%s). Something is wrong. Please, make sure you are using the latest version of the application.", current_version, latest_version)
            return False
        elif current_version < latest_version:
            log.warning("Database version ID=%s is older than latest schema ID=%s, applying updates...", current_version, latest_version)
            for ver, path in schemas:
                if ver <= current_version:
                    continue
                try:
                    sql = path.read_text()
                    self.c.executescript(sql)
                    self.commit()
                    log.info("Database: applied schema %s", path.name)
                except Error as e:
                    log.fatal("Database: failed to apply schema %s: %s", path.name, e)
                    return False

        # Check for required tabels
        required_tables = ["rr_db_version", "log", "user", "user_property", "project", "project_user", "object", "object_integration_review"]
        raw_tables = self.c.execute("SELECT name FROM sqlite_master").fetchall()

        if raw_tables is None:
            log.info("Database: unable to find all required tables. Please check the logs.")
            return False
        
        tables = [table[0] for table in raw_tables]
        log.debug("Checking tables creation...")
        if not all(t in tables for t in required_tables):
            log.warning("Failed to find the following required tables: %s", ", ".join([t for t in required_tables if t not in tables]))
            return False
        
        return True
    
    
