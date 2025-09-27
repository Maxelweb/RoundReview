from types import SimpleNamespace
from flask import render_template, request, session, redirect, Blueprint
from .utils import is_logged, is_logged_admin, build_object_tree
from ..config import VERSION, log
from ..database import Database
from ..models import Project, Object, ObjectStatus, Role, ProjectUser
from .api import project_list, project_create, project_objects_list, project_objects_create, project_users_list

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

@project_blueprint.route('/projects/<project_id>/', methods=["GET"])
def view_objects(project_id:str):
    """ View the objects of a specific project """
    path = request.args.get('path', '/') # Default to root if no path is provided
    output = ()
    objects = {}
    project = None
    res, status = project_list()
    if status == 200:
        project = [Project.from_dict(elem) for elem in res["projects"] if elem["id"] == int(project_id)][0]
    res, status = project_objects_list(project_id)
    if status == 200:
        objects = [Object.from_dict(elem) for elem in res["objects"]]
        tree = build_object_tree(objects)
        log.debug("view_objects - tree: %s", tree)

    else:
        output = ("error", res["error"])
    return render_template(
        "project/view.html",
        title=project.title,
        user=session["user"],
        objects=objects,
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
    folder_path = request.args.get('folder_path', '/') # Default to root if no path is provided
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
        user=session["user"],
        output=output,
        folder_path=folder_path,
        project_id=project_id,
        version=VERSION,
        logged=is_logged(),
        admin=is_logged_admin(),
        project_role=get_user_role_in_project(project_id),
    )

@project_blueprint.route('/projects/<project_id>/users', methods=["GET"])
def view_users(project_id:str):
    """ Show the users of a specific project with the roles """
    output = ()
    users = []

    res, status = project_users_list(project_id)
    if status == 200:
        users = [elem for elem in res["users"]]
    else:
        output = ("error", res["error"])
    return render_template(
        "project/manage.html",
        title="Project Users",
        user=session["user"],
        users=users,
        project_id=project_id,
        output=output,
        version=VERSION,
        logged=is_logged(),
        admin=is_logged_admin(),
        role=Role,
        project_role=get_user_role_in_project(project_id),
    )

@project_blueprint.route('/projects/<project_id>/users/<user_id>', methods=["POST"])
def update_user(project_id:str):
    """ TODO: Add / Remove users or update their roles """
    output = ()
    users = []

    res, status = project_users_list(project_id)
    if status == 200:
        users = [ProjectUser.from_dict(elem) for elem in res["users"]]
    else:
        output = ("error", res["error"])
    return render_template(
        "project/manage.html",
        title="Project Users",
        user=session["user"],
        users=users,
        project_id=project_id,
        output=output,
        version=VERSION,
        logged=is_logged(),
        admin=is_logged_admin(),
        project_role=get_user_role_in_project(project_id),
        role=Role,
    )
