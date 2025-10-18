/*
    =======================================
    SQLite updates
    =======================================
*/

CREATE TABLE IF NOT EXISTS "rr_db_version" (
    "id"	INTEGER,
    "updated_at" TEXT DEFAULT CURRENT_TIMESTAMP,
    "description" TEXT NOT NULL,
    PRIMARY KEY("id")
); 

/*
    Log schema updates
    =======================================
*/

INSERT INTO "rr_db_version" (id, description) VALUES(0, "Add table for schema versioning");