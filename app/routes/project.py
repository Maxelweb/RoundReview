from types import SimpleNamespace
from flask import render_template, request, session, redirect, Blueprint
from .utils import is_logged, is_logged_admin
from ..config import VERSION, log
from ..database import Database
from ..models import Project, Object, ObjectStatus
from .api import project_list, project_create, project_objects_list, project_objects_create

project_blueprint = Blueprint('project', __name__)

@project_blueprint.route('/projects', methods=["GET"])
def list():
    """ List projects """
    output = ()
    projects = {}
    res, status = project_list()
    if status == 200:
        projects = [Project.from_dict(elem) for elem in res["projects"]]
    else:
        output = ("error", res["message"])
    return render_template(
        "project/list.html",
        title="Your Projects",
        projects=projects,
        output=output,
        version=VERSION,
        logged=is_logged(),
        admin=is_logged_admin()
    )

@project_blueprint.route('/projects/create', methods=["GET", "POST"])
def create():
    """ Create a new project """
    output = ()
    if request.method == "POST":
        res, status = project_create()
        if status == 201:
            return redirect(f"/projects/{res["project_id"]}")
        else:
            output = ("error", res["error"])
    return render_template(
        "project/create.html",
        title="Create new project",
        output=output,
        version=VERSION,
        logged=is_logged(),
        admin=is_logged_admin()
    )

@project_blueprint.route('/projects/<project_id>/', methods=["GET"])
def view_objects(project_id:str):
    """ View the objects of a specific project """
    output = ()
    objects = {}
    project = None
    res, status = project_list()
    if status == 200:
        project = [Project.from_dict(elem) for elem in res["projects"] if elem["id"] == int(project_id)][0]
    res, status = project_objects_list(project_id)
    if status == 200:
        objects = [Object.from_dict(elem) for elem in res["objects"]]
        print("object paths:", [obj.path for obj in objects])
                
    else:
        output = ("error", res["error"])
    return render_template(
        "project/view.html",
        title=project.title,
        objects=objects,
        project=project,
        output=output,
        version=VERSION,
        logged=is_logged(),
        admin=is_logged_admin()
    )

@project_blueprint.route('/projects/<project_id>/create', methods=["GET", "POST"])
def create_object(project_id:str):
    """ Create a new object in project """
    output = ()
    if request.method == "POST":
        res, status = project_objects_create(project_id=project_id)
        if status == 201:
            return redirect(f"/projects/{project_id}/")
        else:
            output = ("error", res["error"])
    return render_template(
        "project/object/create.html",
        title="Create new document",
        output=output,
        project_id=project_id,
        version=VERSION,
        logged=is_logged(),
        admin=is_logged_admin()
    )