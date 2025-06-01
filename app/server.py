from datetime import datetime
from flask import Flask
from flask_session import Session
from .routes import admin_blueprint, basic_blueprint, settings_blueprint, project_blueprint

app = Flask(__name__, template_folder='template')
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.register_blueprint(basic_blueprint)
app.register_blueprint(admin_blueprint)
app.register_blueprint(settings_blueprint)
app.register_blueprint(project_blueprint)
Session(app)
