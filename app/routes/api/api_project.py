import uuid, json
from flask import request, session, Blueprint
from ..utils import is_logged, get_system_property, get_user_from_api_key, check_authentication
from ...config import log
from ...database import Database
from ...models import Project, Role, SystemProperty

api_project_bp = Blueprint('api_project', __name__)

@api_project_bp.route("/api/projects", methods=["GET"])
def project_list():
    """ List of the projects (where the user is involved)"""
    if not check_authentication():
        return {"error": "Unauthorized"}, 401

    user_id = session["user"].id if is_logged() else get_user_from_api_key(request.headers.get("x-api-key"))

    db = Database()
    try:
        # Fetch projects where the user is involved
        rows = db.c.execute(
            '''
            SELECT p.id, p.title, p.deleted
            FROM project p
            INNER JOIN project_user pu ON p.id = pu.project_id
            WHERE pu.user_id = ? AND p.deleted = 0
            ''',
            (user_id,)
        ).fetchall()

        # Convert rows to Project instances and then to dictionaries
        projects = [Project.from_db_row(row).to_dict() for row in rows]
        return {"projects": projects}, 200
    except Exception as e:
        log.error(f"Error fetching projects: {e}")
        return {"error": "Internal server error"}, 500
    finally:
        db.close()

@api_project_bp.route("/api/projects", methods=["POST"])
def project_create():
    """ Create a new project """
    if not check_authentication():
        return {"error": "Unauthorized"}, 401

    user_id = session["user"].id if is_logged() else get_user_from_api_key(request.headers.get("x-api-key"))

    data = request.form or request.json
    log.debug(data)
    if not data or "title" not in data:
        return {"error": "Missing required field 'title'"}, 400

    title = data["title"]

    db = Database()
    try:
        # Check if project creation is disabled across the system
        if get_system_property(SystemProperty.PROJECT_CREATE_DISABLED) == "TRUE":
            return {"error": "Project creation is disabled across the system"}, 403

        # Create the new project
        db.c.execute("INSERT INTO project (title, deleted) VALUES (?, ?)",
            (title, 0)
        )
        db.commit()
        project_id = db.c.lastrowid
        db.log(user_id, f"project add (project_id={project_id})")

        # Add the creator as the owner of the project
        db.c.execute("INSERT INTO project_user (project_id, user_id, role) VALUES (?, ?, ?)",
            (project_id, user_id, Role.OWNER.value)
        )
        db.commit()
        db.log(user_id, f"project user add (project_id={project_id}, user_id={user_id}, role={Role.OWNER.value})")
        return {"message": "Project created successfully", "project_id": project_id}, 201
    except Exception as e:
        log.error(f"Error creating project: {e}")
        return {"error": "Internal server error"}, 500
    finally:
        db.close()

@api_project_bp.route("/api/projects/<project_id>", methods=["PUT"])
def project_update(project_id:str):
    """ Update an existing project (only for project owners) """

    if not check_authentication():
        return {"error": "Unauthorized"}, 401

    user_id = session["user"].id if is_logged() else get_user_from_api_key(request.headers.get("x-api-key"))

    data = request.form or request.json
    if not data or "title" not in data:
        return {"error": "Missing required field 'title'"}, 400

    title = data["title"]

    db = Database()
    try:
        # Check if the user is the owner of the project
        owner_check = db.c.execute(
            '''
            SELECT 1
            FROM project_user
            WHERE project_id = ? AND user_id = ? AND role = ?
            ''',
            (project_id, user_id, Role.OWNER.value)
        ).fetchone()

        if not owner_check:
            return {"error": "Forbidden: Only project owners can update the project"}, 403

        # Update the project title
        db.c.execute(
            '''
            UPDATE project
            SET title = ?
            WHERE id = ? AND deleted = 0
            ''',
            (title, project_id)
        )
        db.commit()
        db.log(user_id, f"project update (project_id={project_id}, keys=title)")
        return {"message": "Project updated successfully"}, 200
    
    except Exception as e:
        log.error(f"Error updating project: {e}")
        return {"error": "Internal server error"}, 500
    finally:
        db.close()

@api_project_bp.route("/api/projects/<project_id>/users", methods=["GET"])
def project_users_list(project_id: str):
    """ Retrieve a list of all users who are members of the project """

    if not check_authentication():
        return {"error": "Unauthorized"}, 401

    user_id = session["user"].id if is_logged() else get_user_from_api_key(request.headers.get("x-api-key"))

    db = Database()
    try:
        # Check if the user is a member of the project
        member_check = db.c.execute(
            '''
            SELECT 1
            FROM project_user
            WHERE project_id = ? AND user_id = ?
            ''',
            (project_id, user_id)
        ).fetchone()

        if not member_check:
            return {"error": "Forbidden: You are not a member of this project"}, 403

        # Fetch all users in the project
        rows = db.c.execute(
            '''
            SELECT u.id, u.name, u.email, pu.role
            FROM user u
            INNER JOIN project_user pu ON u.id = pu.user_id
            WHERE pu.project_id = ? AND u.deleted = 0
            ''',
            (project_id,)
        ).fetchall()

        # Convert rows to dictionaries
        users = [{"id": row[0], "name": row[1], "role": row[3]} for row in rows]
        return {"users": users}, 200

    except Exception as e:
        log.error(f"Error fetching users for project {project_id}: {e}")
        return {"error": "Internal server error"}, 500
    finally:
        db.close()

@api_project_bp.route("/api/projects/<project_id>/join", methods=["POST"])
def project_join(project_id:str):
    """ Add a new member using their username to a project (only for project owners) """
    if not check_authentication():
        return {"error": "Unauthorized"}, 401

    user_id = session["user"].id if is_logged() else get_user_from_api_key(request.headers.get("x-api-key"))

    data = request.form or request.json
    if not data or "username" not in data or "role" not in data:
        return {"error": "Missing required fields 'username' and 'role'"}, 400

    username = data["username"]
    role = data["role"]

    if role not in Role.values():
        return {"error": f"Invalid role. Valid roles are: {', '.join(Role.values())}"}, 400

    db = Database()
    try:
        # Check if the user is the owner of the project
        owner_check = db.c.execute(
            '''
            SELECT 1
            FROM project_user
            WHERE project_id = ? AND user_id = ? AND role = ?
            ''',
            (project_id, user_id, Role.OWNER.value)
        ).fetchone()

        if not owner_check:
            return {"error": "Forbidden: Only project owners can add members"}, 403

        # Check if the user with the given username exists
        user_row = db.c.execute(
            '''
            SELECT id
            FROM user
            WHERE name = ? AND deleted = 0
            ''',
            (username,)
        ).fetchone()

        if not user_row:
            return {"error": "User with the given username does not exist"}, 404

        new_user_id = user_row[0]

        # Check if the user is already a member of the project
        member_check = db.c.execute(
            '''
            SELECT 1
            FROM project_user
            WHERE project_id = ? AND user_id = ?
            ''',
            (project_id, new_user_id)
        ).fetchone()

        if member_check:
            return {"error": "User is already a member of the project"}, 400

        # Add the user to the project
        db.c.execute(
            '''
            INSERT INTO project_user (project_id, user_id, role)
            VALUES (?, ?, ?)
            ''',
            (project_id, new_user_id, role)
        )
        db.commit()
        db.log(user_id, f"project user join (project_id={project_id}, user_id={new_user_id}, role={role})")
        return {"message": "User added to the project successfully"}, 201

    except Exception as e:
        log.error(f"Error adding user to project: {e}")
        return {"error": "Internal server error"}, 500
    finally:
        db.close()

@api_project_bp.route("/api/projects/<project_id>/unjoin", methods=["DELETE"])
def project_unjoin(project_id:str):
    """ Remove a member using their username from a project (only for project owners or the member themselves) """
    if not check_authentication():
        return {"error": "Unauthorized"}, 401

    user_id = session["user"].id if is_logged() else get_user_from_api_key(request.headers.get("x-api-key"))

    data = request.form or request.json
    if not data or "username" not in data:
        return {"error": "Missing required field 'username'"}, 400

    username = data["username"]

    db = Database()
    try:
        # Check if the user with the given username exists
        user_row = db.c.execute(
            '''
            SELECT id
            FROM user
            WHERE name = ? AND deleted = 0
            ''',
            (username,)
        ).fetchone()

        if not user_row:
            return {"error": "User with the given name does not exist"}, 404

        target_user_id = user_row[0]

        # Check if the target user is a member of the project
        member_check = db.c.execute(
            '''
            SELECT role
            FROM project_user
            WHERE project_id = ? AND user_id = ?
            ''',
            (project_id, target_user_id)
        ).fetchone()

        if not member_check:
            return {"error": "User is not a member of the project"}, 400

        target_user_role = member_check[0]

        # Check if the requester is the owner or the target user themselves
        if target_user_id != user_id:
            owner_check = db.c.execute(
                '''
                SELECT 1
                FROM project_user
                WHERE project_id = ? AND user_id = ? AND role = ?
                ''',
                (project_id, user_id, Role.OWNER.value)
            ).fetchone()

            if not owner_check:
                return {"error": "Forbidden: Only project owners can remove other members"}, 403

        # Prevent owners from removing themselves if they are the only owner
        if target_user_role == Role.OWNER.value:
            owner_count = db.c.execute(
                '''
                SELECT COUNT(*)
                FROM project_user
                WHERE project_id = ? AND role = ?
                ''',
                (project_id, Role.OWNER.value)
            ).fetchone()[0]

            if owner_count <= 1:
                return {"error": "Cannot remove the only owner of the project"}, 400

        # Remove the user from the project
        db.c.execute(
            '''
            DELETE FROM project_user
            WHERE project_id = ? AND user_id = ?
            ''',
            (project_id, target_user_id)
        )
        db.commit()
        db.log(user_id, f"project user join (project_id={project_id}, user_id={target_user_id})")
        return {"message": "User removed from the project successfully"}, 200

    except Exception as e:
        log.error(f"Error removing user from project: {e}")
        return {"error": "Internal server error"}, 500
    finally:
        db.close()

