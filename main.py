from app.server import app
from app.config import log, DEBUG
from app.database import Database
from waitress import serve

def main():
    log.info("Initialising Database...")
    db = Database()
    db.initialize()
    db.close()
    log.info("Starting server...")
    if DEBUG:
        app.config["TEMPLATES_AUTO_RELOAD"] = True
        app.run(
            debug=False, 
            host="0.0.0.0", 
            port="8080",
            load_dotenv=True,
        )
    else:
        serve(app, host="0.0.0.0", port="8080")
if __name__ == "__main__":
    main()
    
    
