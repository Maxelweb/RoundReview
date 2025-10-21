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
        """ Init the database operations """

        if self.__update_db_schema_version():
            log.info("Database schema version updated correctly!")
        else:
            log.fatal("Unable to update schema in the database. Please check the logs.")
            exit(1)
        
        if self.c.execute("SELECT name FROM user WHERE admin = -1").fetchone() is None:
            self.__create_user_system()
            self.log(USER_SYSTEM_ID, f"user add (user_id={USER_SYSTEM_ID})")
        else: 
            log.info("System user: already created!")

        self.__check_system_properties()

        if self.c.execute("SELECT name FROM user WHERE admin = 1").fetchone() is None:
            self.__create_user_admin()
            self.log(USER_SYSTEM_ID, f"user add (user_id={(USER_SYSTEM_ID+1)})")
        else: 
            log.info("Admin user: at least one already created!")

    def close(self) -> None:
        self._client.close()

    @property
    def c(self) -> Cursor:
        return self._cursor
    
    def commit(self) -> None:
        return self._client.commit()

    @staticmethod
    def hash(password:str) -> str:
        """ Hashing function """
        return hashlib.sha512(password.encode("utf-8")).hexdigest()

    def log(self, user_id:int, action:str) -> None:
        """ Add a log into the database """
        log.info(f"USER_ID {user_id} -> {action}")
        self.c.execute(
            'INSERT INTO log (date, user_id, action) VALUES (?, ?, ?);', 
            (datetime.datetime.now().isoformat(), 
            user_id,
            action)
        )
        self.commit()

    def __create_user_system(self) -> None:
        """ Add the system user that handles automatic operations """
        # Add system user
        self.c.execute(
            'INSERT INTO user (name, email, password, admin) VALUES (?, ?, ?, ?);', 
            (USER_SYSTEM_NAME,
            USER_SYSTEM_EMAIL,
            Database.hash(random.randbytes(16).hex()),
            -1)
        )
        self.commit()

    def __check_system_properties(self) -> None:
        """ Add the system properties with defaults (if missing) """
        expected_props = [
            ("PROJECT_CREATE_DISABLED", "FALSE"),
            ("OBJECT_DELETE_DISABLED", "FALSE"),
            ("USER_LOGIN_DISABLED", "FALSE"),
            ("OBJECT_MAX_UPLOAD_SIZE_MB", SYSTEM_MAX_UPLOAD_SIZE_MB),
            ("WEBHOOKS_DISABLED", "FALSE")
        ]
        existing_props = {row[0] for row in self.c.execute("SELECT key FROM user_property WHERE user_id = ?;", (USER_SYSTEM_ID,)).fetchall()}
        props_to_add = [(k, v, USER_SYSTEM_ID) for k, v in expected_props if k not in existing_props]

        if props_to_add:
            self.c.executemany('INSERT INTO user_property (key, value, user_id) VALUES (?, ?, ?);', props_to_add)
            self.commit()
            log.info("System properties: added missing properties for System User: %s", ", ".join([t[0] for t in props_to_add]))
        else:
            log.info("System properties: all required properties already created!")

    def __create_user_admin(self) -> None:
        self.c.execute(
            'INSERT INTO user (name, email, password, admin) VALUES (?, ?, ?, ?);', 
            (USER_ADMIN_NAME,
            USER_ADMIN_EMAIL,
            Database.hash(USER_DEFAULT_PASSWORD),
            1)
        )
        self.commit()
        log.warning('*' * 30)
        log.warning("(!) Admin user: adding default user %s with password: %s", USER_ADMIN_EMAIL, USER_DEFAULT_PASSWORD)
        log.warning('*' * 30)

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
            log.info("Database schema up-to-date (v%s)", current_version)
        elif current_version > latest_version:
            log.warning("Database schema (v%s) has a higher schema version than the available (v%s). Something is wrong. Please, make sure you are using the latest version of the application.", current_version, latest_version)
            return False
        elif current_version < latest_version:
            log.warning("Database schema in use (v%s) is older than latest schema (v%s), applying updates...", current_version, latest_version)
            for ver, path in schemas:
                if ver <= current_version:
                    continue
                try:
                    sql = path.read_text()
                    self.c.executescript(sql)
                    self.commit()
                    log.info("Database: applied schema %s", path.name)
                    if ver > 0: # Minimum schema version for logging
                        self.log(USER_SYSTEM_ID, f"database schema version update (id={ver})")
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
        if not all(t in tables for t in required_tables):
            log.warning("Failed to find the following required tables: %s", ", ".join([t for t in required_tables if t not in tables]))
            return False
        
        return True
    
    
