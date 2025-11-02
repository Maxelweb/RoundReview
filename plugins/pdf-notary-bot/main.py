import os, json
import requests
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from apscheduler.schedulers.background import BackgroundScheduler
from waitress import serve
from routes import core_blueprint
from config import (
    log,
    DEBUG,
    API_BASE_URL, 
    API_KEY,
    PLUGIN_NAME,
    PLUGIN_SIGNED_PDFS_FOLDER,
    PLUGIN_IS_BEHIND_PROXY,
    PLUGIN_BASE_URL_PREFIX,
)

# Core definitions
scheduler = BackgroundScheduler()
app = Flask(__name__)
if PLUGIN_IS_BEHIND_PROXY:
    app.wsgi_app = ProxyFix(app.wsgi_app, x_prefix=1)
app.register_blueprint(core_blueprint, url_prefix=PLUGIN_BASE_URL_PREFIX)
scheduler.start()

# Background service to clean deleted reviews
@scheduler.scheduled_job('interval', hours=24)
def clean_deleted_reviews() -> None:
    log.info("Starting cleaning background service")
    res = requests.get(
        url=f"{API_BASE_URL}/integrations/reviews", 
        headers={"x-api-key": API_KEY}
    )
    if res.status_code != 200:
        log.error("Unable to get reviews for this user")

    # Track all valid object IDs from reviews
    valid_object_ids = set()
    for review in json.loads(res.content).get("reviews", []):
        if review.get("name") != PLUGIN_NAME:
            continue
        object_id = review.get("object_id", None)
        if object_id:
            valid_object_ids.add(object_id)

    # Clean up existing files that don't have reviews
    for file_name in os.listdir(PLUGIN_SIGNED_PDFS_FOLDER):
        if not file_name.endswith('.pdf'):
            continue
        current_object_id = file_name.replace('.pdf', '')
        if current_object_id not in valid_object_ids:
            file_path = os.path.join(PLUGIN_SIGNED_PDFS_FOLDER, file_name)
            log.info("Deleting signed PDF for Object ID = %s", current_object_id)
            os.remove(file_path)
    log.info("Cleaning background service completed")


if __name__ == '__main__':
    if DEBUG:
        app.config["TEMPLATES_AUTO_RELOAD"] = True
        app.run(host="0.0.0.0", port=8081, debug=DEBUG)
    else:
        serve(app, host="0.0.0.0", port="8081")
