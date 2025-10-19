from datetime import datetime
from types import SimpleNamespace
from flask import render_template, request, session, redirect, Blueprint
from .utils import is_logged, is_logged_admin, build_object_tree
from ..config import VERSION, log
from ..database import Database
from ..models import Project, Object, ObjectStatus, Role, ProjectUser
from .api import (
    project_list, 
    project_update,
    project_create, 
    project_objects_list, 
    project_objects_create, 
    project_users_list,
    project_join,
    project_unjoin,
    object_delete,
)

def get_user_role_in_project(project_id:str) -> Role:
    """ Get the role of the current logged user in a specific project """
    if not is_logged():
        return Role.NO_ROLE
    res, status = project_users_list(project_id)
    if status != 200:
        return Role.NO_ROLE
    user_id = session["user"].id
    for user in res["users"]:
        if user["id"] == user_id:
            return Role(user["role"]) if user["role"] in Role.values() else Role.NO_ROLE
    return Role.NO_ROLE


project_blueprint = Blueprint('project', __name__)


@project_blueprint.route('/projects', methods=["GET"])
def list():
    """ List projects """
    if not is_logged():
        return redirect("/")
    output = ()
    projects = {}
    res, status = project_list()
    if status == 200:
        projects = [Project.from_dict(elem) for elem in res["projects"]]
    else:
        output = ("error", res["error"])
    return render_template(
        "project/list.html",
        title="Your Projects",
        user=session["user"],
        projects=projects,
        output=output,
        version=VERSION,
        logged=is_logged(),
        admin=is_logged_admin()
    )


@project_blueprint.route('/projects/create', methods=["GET", "POST"])
def create():
    """ Create a new project """
    if not is_logged():
        return redirect("/")
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
        user=session["user"],
        output=output,
        version=VERSION,
        logged=is_logged(),
        admin=is_logged_admin()
    )


@project_blueprint.route('/projects/<project_id>/', methods=["GET", "POST"])
def view_objects(project_id:str):
    """ View the objects of a specific project or Delete an object from the same project """

    if not is_logged():
        return redirect("/")

    path = request.args.get('path', '/') # Default to root if no path is provided
    object_id = request.form.get("object_id", None)
    output = ()
    objects = {}
    project = None

    # Object deletion
    if request.method == "POST" and request.args.get("delete", None) == "1" and object_id is not None:
        res, status = object_delete(object_id)
        if status == 200:
            output = ("success", res["message"])
        else:
            output = ("error", res["error"])

    # Project Objects
    res, status = project_list()
    if status == 200:
        project = [Project.from_dict(elem) for elem in res["projects"] if elem["id"] == int(project_id)][0]
    res, status = project_objects_list(project_id)
    if status == 200:
        objects = [Object.from_dict(elem) for elem in res["objects"]]
        tree = build_object_tree(objects)
        last_objects = sorted(objects, key=lambda obj: obj.update_date, reverse=True)[:5]
    else:
        output = ("error", res["error"])

    return render_template(
        "project/view.html",
        title=project.title,
        user=session["user"],
        last_objects=last_objects,
        tree=tree,
        path=path,
        project=project,
        output=output,
        version=VERSION,
        logged=is_logged(),
        admin=is_logged_admin(),
        role=Role,
        project_role=get_user_role_in_project(project_id),
    )


@project_blueprint.route('/projects/<project_id>/create', methods=["GET", "POST"])
def create_object(project_id:str):
    """ Create a new object in project """

    if not is_logged():
        return redirect("/")

    folder_path = request.args.get('folder_path', '/') # Default to root if no path is provided
    output = ()
    data = None
    if request.method == "POST":
        data = request.form
        res, status = project_objects_create(project_id=project_id)
        if status == 201:
            return redirect(f"/projects/{project_id}/")
        else:
            output = ("error", res["error"])
    return render_template(
        "project/object/create.html",
        title="Create new document",
        user=session["user"],
        output=output,
        folder_path=folder_path,
        project_id=project_id,
        version=VERSION,
        data=data,
        logged=is_logged(),
        admin=is_logged_admin(),
        project_role=get_user_role_in_project(project_id),
    )


@project_blueprint.route('/projects/<project_id>/manage', methods=["GET", "POST"])
def manage_project(project_id:str):
    """ Show and update project infos and users of a specific project with the roles """
    if not is_logged():
        return redirect("/")    
    output = ()
    users = []
    action = request.args.get("action", None)
    if request.method == "POST":
        if action == "join":
            res, status = project_join(project_id=project_id)
            if status == 201:
                output = ("success", f"User '{ request.form.get("username") }' ({request.form.get("role")}) added in the project")
            else:
                print(res)
                output = ("error", res["error"])
        elif action == "unjoin":
            res, status = project_unjoin(project_id=project_id)
            if status == 200:
                output = ("success", f"User '{ request.form.get("username") }' removed from the project")
            else:
                output = ("error", res["error"])
        elif action == "rename_project":
            res, status = project_update(project_id=project_id)
            if status == 200:
                output = ("success", f"Project renamed successfully")
            else:
                output = ("error", res["error"])
        else:
            res, status = {"error": "Wrong action"}, 400
            output = ("error", res["error"])

    res, status = project_users_list(project_id)
    if status == 200:
        users = [elem for elem in res["users"]]
    else:
        output = ("error", res["error"])

    res, status = project_list()
    if status == 200:
        project = [Project.from_dict(elem) for elem in res["projects"] if elem["id"] == int(project_id)][0]

    return render_template(
        "project/manage.html",
        title="Project Management",
        user=session["user"],
        users=users,
        project=project,
        output=output,
        version=VERSION,
        logged=is_logged(),
        admin=is_logged_admin(),
        role=Role,
        project_role=get_user_role_in_project(project_id),
    )

