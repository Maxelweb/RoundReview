import hashlib
import random
import datetime
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
        if self.__create_tables():
            log.warning("Database initialized with tables")
        else:
            log.fatal("Unable to create tables in database")
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
                ("OBJECT_MAX_UPLOAD_SIZE", SYSTEM_MAX_UPLOAD_SIZE_MB, USER_SYSTEM_ID)
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

    def __create_tables(self) -> bool:

        tables_to_create = ["log", "user", "project", "project_user", "object"]

        self.c.execute('''
            CREATE TABLE IF NOT EXISTS "log" (
                "id"	INTEGER,
                "date"	TEXT NOT NULL,
                "user_id" INTEGER,
                "action" TEXT NOT NULL,
                PRIMARY KEY("id" AUTOINCREMENT),
                FOREIGN KEY("user_id") REFERENCES "user"("id")
            ); 
        ''')
        self.commit()
        self.c.execute('''                        
            CREATE TABLE IF NOT EXISTS "user" (
                "id"	INTEGER,
                "name"	VARCHAR(32) UNIQUE,
                "email"	VARCHAR(64) UNIQUE,
                "password"	TEXT NOT NULL,
                "admin"	INTEGER DEFAULT 0,
                "deleted" INTEGER DEFAULT 0,
                PRIMARY KEY("id" AUTOINCREMENT)
            );
        ''')
        self.commit()
        self.c.execute('''                        
            CREATE TABLE IF NOT EXISTS "user_property" (
                "key"	VARCHAR(32) NOT NULL,
                "value"	TEXT NOT NULL,
                "user_id" INTEGER REFERENCES user(id)
            );
        ''')
        self.commit()
        self.c.execute('''                        
            CREATE TABLE IF NOT EXISTS "project" (
                "id"	INTEGER,
                "title"	TEXT NOT NULL,
                "deleted" INTEGER DEFAULT 0,
                PRIMARY KEY("id" AUTOINCREMENT)
            );
        ''')
        self.commit()
        self.c.execute('''                        
            CREATE TABLE IF NOT EXISTS "project_user" (
                "project_id" INTEGER REFERENCES project(id),
                "user_id" INTEGER REFERENCES user(id),
                "role" VARCHAR(32) NOT NULL
            );
        ''')
        self.commit()
        self.c.execute('''                        
            CREATE TABLE IF NOT EXISTS "object" (
                "id" CHAR(36),
                "path" TEXT NOT NULL,
                "user_id" INTEGER REFERENCES user(id),
                "project_id" INTEGER REFERENCES project(id),
                "name" TEXT NOT NULL,
                "description" TEXT DEFAULT NULL,
                "raw" BLOB DEFAULT NULL,
                "comments" TEXT DEFAULT NULL,
                "version" VARCHAR(64) DEFAULT NULL,
                "status" VARCHAR(32) DEFAULT NULL,
                "upload_date" TEXT DEFAULT CURRENT_TIMESTAMP,
                "update_date" TEXT DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        self.commit()
        raw_tables = self.c.execute("SELECT name FROM sqlite_master").fetchall()
        if raw_tables is None:
            return False
        tables = [table[0] for table in raw_tables]
        log.debug("Checking tables creation...")
        if not all(t in tables for t in tables_to_create):
            log.warning("Failed to create the following tables: %s", ", ".join([t for t in tables_to_create if t not in tables]))
            return False
        return True
    
    
