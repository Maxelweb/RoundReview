from types import SimpleNamespace
from flask import render_template, request, session, redirect, Blueprint
from .utils import is_logged, is_logged_admin
from ..config import VERSION, log
from ..database import Database
from ..models import User, Log

api_blueprint = Blueprint('api', __name__)

def check_authentication() -> bool:
    """ Check the authentication of the user.
        Could be flask session or via API Key in header x-api-key"""
    return False

@api_blueprint.route("/api/projects", methods=["GET"])
def project_list():
    """ List of the projects (where the user is involved)"""
    return {}, 500

@api_blueprint.route("/api/projects", methods=["POST"])
def project_create():
    """ Create a new project """
    return {}, 500

@api_blueprint.route("/api/projects/<project_id>", methods=["PUT"])
def project_update():
    """ Update an existing project (only for project owners) """
    return {}, 500 

@api_blueprint.route("/api/projects/<project_id>/join", methods=["POST"])
def project_join():
    """ Add a new member using their email to a project (only for project owners) """
    return {}, 500 

@api_blueprint.route("/api/projects/<project_id>/unjoin", methods=["DELETE"])
def project_unjoin():
    """ Remove a member using their email to a project (only for project owners or members) """
    return {}, 500

@api_blueprint.route("/api/projects/<project_id>/objects", methods=["GET"])
def project_objects_list():
    """ List all the objects inside the project """
    return {}, 500 

@api_blueprint.route("/api/projects/<project_id>/objects", methods=["POST"])
def project_objects_create():
    """ Create a new object inside the project """
    return {}, 500 

@api_blueprint.route("/api/objects/<object_id>", methods=["GET"])
def project_objects():
    """ Get detail information of the object """
    return {}, 500 

@api_blueprint.route("/api/objects/<object_id>", methods=["DELETE"])
def project_objects():
    """ Delete an object """
    return {}, 500 

@api_blueprint.route("/api/objects/<object_id>", methods=["PUT"])
def project_objects():
    """ Update an object """
    return {}, 500 