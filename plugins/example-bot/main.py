""" 
Example Flask Bot
---------------------
This is an example on how to make a bot with a Flask application using webhooks.
"""
from flask import Flask, request
from config import (
    log,
    DEBUG,
    PLUGIN_NAME,
    PLUGIN_VERSION,
)

app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    """ Show index landing page """
    return {"message": f"Bot {PLUGIN_NAME} (v{PLUGIN_VERSION}) is active"}, 200


@app.route('/webhook', methods=['POST'])
def handle_webhook():
    """ Handle Webhook call from the RoundReview application """

    data = request.get_json()

    if not data or data.get("event") != "object.updated":
        log.warning("Invalid payload call")
        return {"error": "Invalid payload"}, 400
    
    status = data.get("updated_fields", {}).get("status")
    log.info("New notification: Document %s from project %s has been updated with a new status: %s", data.get("object_id"), data.get("project_id"), status)

    # < Do something with this information >
    # E.g. You can use an API KEY to call the APIs and retrieve document information.
    
    return {"message": "Notification received!"}, 200


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8082, debug=DEBUG)
