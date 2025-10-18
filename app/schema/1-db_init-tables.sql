/*
    =======================================
    SQLite updates
    =======================================
*/

CREATE TABLE IF NOT EXISTS "log" (
    "id"	INTEGER,
    "date"	TEXT NOT NULL,
    "user_id" INTEGER,
    "action" TEXT NOT NULL,
    PRIMARY KEY("id" AUTOINCREMENT),
    FOREIGN KEY("user_id") REFERENCES "user"("id")
); 
                    
CREATE TABLE IF NOT EXISTS "user" (
    "id"	INTEGER,
    "name"	VARCHAR(32) UNIQUE,
    "email"	VARCHAR(64) UNIQUE,
    "password"	TEXT NOT NULL,
    "admin"	INTEGER DEFAULT 0,
    "deleted" INTEGER DEFAULT 0,
    PRIMARY KEY("id" AUTOINCREMENT)
);
                    
CREATE TABLE IF NOT EXISTS "user_property" (
    "key"	VARCHAR(32) NOT NULL,
    "value"	TEXT NOT NULL,
    "user_id" INTEGER REFERENCES user(id)
);
                    
CREATE TABLE IF NOT EXISTS "project" (
    "id"	INTEGER,
    "title"	TEXT NOT NULL,
    "deleted" INTEGER DEFAULT 0,
    PRIMARY KEY("id" AUTOINCREMENT)
);
                    
CREATE TABLE IF NOT EXISTS "project_user" (
    "project_id" INTEGER REFERENCES project(id),
    "user_id" INTEGER REFERENCES user(id),
    "role" VARCHAR(32) NOT NULL
);
                    
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
    "update_date" TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY("id")
);

CREATE TABLE IF NOT EXISTS "object_integration_review" (
    "id" CHAR(36),
    "name" VARCHAR(32) NOT NULL, 
    "icon" VARCHAR(32) DEFAULT NULL,
    "url" VARCHAR(255) DEFAULT NULL,
    "url_text" VARCHAR(64) DEFAULT NULL, 
    "value" TEXT NOT NULL,
    "created_at" TEXT DEFAULT CURRENT_TIMESTAMP,
    "user_id" INTEGER REFERENCES user(id), 
    "object_id" INTEGER REFERENCES object(id),
    PRIMARY KEY("id")
);

/*
    Log schema updates
    =======================================
*/

INSERT INTO "rr_db_version" (id, description) VALUES(1, "Add core tables for Round Review application");