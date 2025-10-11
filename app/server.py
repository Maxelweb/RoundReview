from datetime import datetime
from flask import Flask
from flask_session import Session
from .scheduler import scheduler
from .oauth import oauth
from .routes import (
    admin_blueprint,
    basic_blueprint, 
    settings_blueprint, 
    project_blueprint, 
    object_blueprint, 
    api_project_bp, 
    api_integration_bp, 
    api_object_bp
)

app = Flask(__name__, template_folder='template')
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.register_blueprint(basic_blueprint)
app.register_blueprint(admin_blueprint)
app.register_blueprint(settings_blueprint)
app.register_blueprint(project_blueprint)
app.register_blueprint(object_blueprint)
app.register_blueprint(api_project_bp)
app.register_blueprint(api_object_bp)
app.register_blueprint(api_integration_bp)
app.scheduler = scheduler
app.oauth = oauth
oauth.init_app(app)
Session(app)
