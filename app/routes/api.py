import uuid
from flask import request, session, Blueprint
from .utils import is_logged
from ..config import VERSION, log
from ..database import Database
from ..models import User, Project, Property, Role, Object, ObjectStatus

api_blueprint = Blueprint('api', __name__)

def get_user_from_api_key(api_key:str) -> User:
    """ Get user from API key """
    db = Database()
    try:
        # Fetch the user associated with the given API key
        user_row = db.c.execute(
            '''
            SELECT *
            FROM user
            WHERE id IN (
                SELECT user_id
                FROM user_property
                WHERE key = ? AND value = ?
            ) AND deleted = 0
            LIMIT 1
            ''',
            (Property.API_KEY.value, api_key)
        ).fetchone()
        if user_row:
            return User(user_row)
        return None
    except Exception as e:
        log.error(f"Error fetching user by API key: {e}")
        return None
    finally:
        db.close()

def check_authentication() -> bool:
    """ Check the authentication of the user.
        Could be flask session or via API Key in header x-api-key"""

    api_key = request.headers.get("x-api-key")
    if api_key:
        # Validate the API key by checking user properties in the database
        db = Database()
        user_row = db.c.execute(
            'SELECT id, name, email, password, admin, deleted FROM user WHERE id IN (SELECT user_id FROM user_property WHERE key = ? AND value = ?) AND deleted = 0 LIMIT 1',
            (User.Property.API_KEY.value, api_key)
        ).fetchone()
        if user_row:
            db.close()
            user = User(user_row)
            return True
        
    # Check if the user is logged in via session
    if is_logged() and session["user"].id is not None:
        return True

    return False

@api_blueprint.route("/api/projects", methods=["GET"])
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

@api_blueprint.route("/api/projects", methods=["POST"])
def project_create(args:dict=None):
    """ Create a new project """
    if not check_authentication():
        return {"error": "Unauthorized"}, 401

    user_id = session["user"].id if is_logged() else get_user_from_api_key(request.headers.get("x-api-key"))

    #data = args if args is not None else request.json
    data = request.form or request.json
    log.debug(data)
    if not data or "title" not in data:
        return {"error": "Missing required field 'title'"}, 400

    title = data["title"]

    db = Database()
    try:
        db.c.execute("INSERT INTO project (title, deleted) VALUES (?, ?)",
            (title, 0)
        )
        db.commit()

        project_id = db.c.lastrowid
        db.c.execute("INSERT INTO project_user (project_id, user_id, role) VALUES (?, ?, ?)",
            (project_id, user_id, Role.OWNER.value)
        )
        db.commit()

        return {"message": "Project created successfully", "project_id": project_id}, 201
    except Exception as e:
        log.error(f"Error creating project: {e}")
        return {"error": "Internal server error"}, 500
    finally:
        db.close()

@api_blueprint.route("/api/projects/<project_id>", methods=["PUT"])
def project_update(project_id:str):
    """ Update an existing project (only for project owners) """

    if not check_authentication():
        return {"error": "Unauthorized"}, 401

    user_id = session["user"].id if is_logged() else get_user_from_api_key(request.headers.get("x-api-key"))

    data = request.json
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
        return {"message": "Project updated successfully"}, 200
    
    except Exception as e:
        log.error(f"Error updating project: {e}")
        return {"error": "Internal server error"}, 500
    finally:
        db.close()

@api_blueprint.route("/api/projects/<project_id>/users", methods=["GET"])
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

@api_blueprint.route("/api/projects/<project_id>/join", methods=["POST"])
def project_join(project_id:str):
    """ Add a new member using their username to a project (only for project owners) """
    if not check_authentication():
        return {"error": "Unauthorized"}, 401

    user_id = session["user"].id if is_logged() else get_user_from_api_key(request.headers.get("x-api-key"))

    data = request.json
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

        return {"message": "User added to the project successfully"}, 201

    except Exception as e:
        log.error(f"Error adding user to project: {e}")
        return {"error": "Internal server error"}, 500
    finally:
        db.close()

@api_blueprint.route("/api/projects/<project_id>/unjoin", methods=["DELETE"])
def project_unjoin(project_id:str):
    """ Remove a member using their username from a project (only for project owners or the member themselves) """
    if not check_authentication():
        return {"error": "Unauthorized"}, 401

    user_id = session["user"].id if is_logged() else get_user_from_api_key(request.headers.get("x-api-key"))

    data = request.json
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

        return {"message": "User removed from the project successfully"}, 200

    except Exception as e:
        log.error(f"Error removing user from project: {e}")
        return {"error": "Internal server error"}, 500
    finally:
        db.close()

@api_blueprint.route("/api/projects/<project_id>/objects", methods=["GET"])
def project_objects_list(project_id:str):
    """ List all the objects inside the project """
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

        # Fetch all objects inside the project
        rows = db.c.execute(
            '''
            SELECT id, path, user_id, project_id, name, description, comments, version, status, upload_date, update_date
            FROM object
            WHERE project_id = ? AND status IS NOT NULL
            ''',
            (project_id,)
        ).fetchall()

        # Convert rows to Object instances and then to dictionaries
        objects = [Object.from_db_row(row).to_dict() for row in rows]
        return {"objects": objects}, 200

    except Exception as e:
        log.error(f"Error fetching objects for project {project_id}: {e}")
        return {"error": "Internal server error"}, 500
    finally:
        db.close()

@api_blueprint.route("/api/projects/<project_id>/objects", methods=["POST"])
def project_objects_create(project_id: str):
    """ Create a new object inside the project, accepting application/pdf and storing file as blob """
    if not check_authentication():
        return {"error": "Unauthorized"}, 401

    user_id = session["user"].id if is_logged() else get_user_from_api_key(request.headers.get("x-api-key"))

    # Check if the request contains a file
    if "file" not in request.files:
        return {"error": "Missing required file 'file'"}, 400

    file = request.files["file"]

    # Validate file type
    if file.content_type != "application/pdf":
        return {"error": "Invalid file type. Only 'application/pdf' is allowed"}, 400

    # Extract metadata from the request
    name = request.form.get("name")
    description = request.form.get("description", "")
    path = request.form.get("path", "/")
    version = request.form.get("version", "")
    status = request.form.get("status", ObjectStatus.NO_REVIEW.value)

    if not path.startswith("/"):
        return {"error": "Invalid path. Path must start with '/'."}, 400

    if not name:
        return {"error": "Missing required field 'name'"}, 400

    if status not in ObjectStatus.values():
        return {"error": f"Invalid status. Valid statuses are: {', '.join(ObjectStatus.values())}"}, 400

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

        # Read the file content as blob
        file_blob = file.read()

        # Insert the new object into the database
        object_id = str(uuid.uuid4())
        db.c.execute(
            '''
            INSERT INTO object (id, path, user_id, project_id, name, description, version, status, raw)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (object_id, path, user_id, project_id, name, description, version, status, file_blob)
        )
        db.commit()

        object_id = db.c.lastrowid
        return {"message": "Object created successfully", "object_id": object_id}, 201

    except Exception as e:
        log.error(f"Error creating object in project {project_id}: {e}")
        return {"error": "Internal server error"}, 500
    finally:
        db.close()

@api_blueprint.route("/api/objects/<object_id>", methods=["GET"])
def object_get(object_id: str, load_raw: bool=False):
    """ Get detail information of the object """

    if request.args.get("raw", "0") == "1":
        load_raw = True

    if not check_authentication():
        return {"error": "Unauthorized"}, 401

    user_id = session["user"].id if is_logged() else get_user_from_api_key(request.headers.get("x-api-key"))

    db = Database()
    try:
        # Check if the user is a member of the project associated with the object
        project_check = db.c.execute(
            '''
            SELECT project_id
            FROM object
            WHERE id = ?
            ''',
            (object_id,)
        ).fetchone()

        if not project_check:
            return {"error": "Object not found"}, 404

        project_id = project_check[0]

        member_check = db.c.execute(
            '''
            SELECT 1
            FROM project_user
            WHERE project_id = ? AND user_id = ?
            ''',
            (project_id, user_id)
        ).fetchone()

        if not member_check:
            return {"error": "Forbidden: You are not a member of the project associated with this object"}, 403

        # Fetch the object details
        object_row = db.c.execute(
            '''
            SELECT id, path, user_id, project_id, name, description, comments, version, status, upload_date, update_date
            FROM object
            WHERE id = ?
            ''',
            (object_id,)
        ).fetchone()

        if not object_row:
            return {"error": "Object not found"}, 404

        obj = Object.from_db_row(object_row)

        # Load raw data if available
        if load_raw:
            obj.load_raw(db)

        return {"object": obj.to_dict()}, 200

    except Exception as e:
        log.error(f"Error fetching object {object_id}: {e}")
        return {"error": "Internal server error"}, 500
    finally:
        db.close()

@api_blueprint.route("/api/objects/<object_id>", methods=["DELETE"])
def object_delete(object_id: str):
    """ Delete an object """
    if not check_authentication():
        return {"error": "Unauthorized"}, 401

    user_id = session["user"].id if is_logged() else get_user_from_api_key(request.headers.get("x-api-key"))

    db = Database()
    try:
        # Check if the object exists
        object_row = db.c.execute(
            '''
            SELECT id, user_id, project_id
            FROM object
            WHERE id = ?
            ''',
            (object_id,)
        ).fetchone()

        if not object_row:
            return {"error": "Object not found"}, 404

        object_user_id = object_row[1]
        project_id = object_row[2]

        # Check if the user is a member of the project associated with the object
        member_check = db.c.execute(
            '''
            SELECT role
            FROM project_user
            WHERE project_id = ? AND user_id = ?
            ''',
            (project_id, user_id)
        ).fetchone()

        if not member_check:
            return {"error": "Forbidden: You are not a member of the project associated with this object"}, 403

        user_role = member_check[0]

        # Only the object owner or a project owner can delete the object
        if user_id != object_user_id and user_role != Role.OWNER.value:
            return {"error": "Forbidden: Only the object owner or a project owner can delete the object"}, 403

        # Delete the object
        db.c.execute(
            '''
            DELETE FROM object
            WHERE id = ?
            ''',
            (object_id,)
        )
        db.commit()

        return {"message": "Object deleted successfully"}, 200

    except Exception as e:
        log.error(f"Error deleting object {object_id}: {e}")
        return {"error": "Internal server error"}, 500
    finally:
        db.close()

@api_blueprint.route("/api/objects/<object_id>", methods=["PUT"])
def object_update(object_id: str):
    """ Update an object """
    if not check_authentication():
        return {"error": "Unauthorized"}, 401

    user_id = session["user"].id if is_logged() else get_user_from_api_key(request.headers.get("x-api-key"))

    data = request.json
    if not data:
        return {"error": "Missing request body"}, 400

    allowed_fields = {"name", "description", "comments", "version", "status", "path"}
    updates = {key: value for key, value in data.items() if key in allowed_fields}

    if "status" in updates and updates["status"] not in ObjectStatus.values():
        return {"error": f"Invalid status. Valid statuses are: {', '.join(ObjectStatus.values())}"}, 400

    if not updates:
        return {"error": "No valid fields to update"}, 400

    db = Database()
    try:
        # Check if the object exists
        object_row = db.c.execute(
            '''
            SELECT id, user_id, project_id
            FROM object
            WHERE id = ?
            ''',
            (object_id,)
        ).fetchone()

        if not object_row:
            return {"error": "Object not found"}, 404

        object_user_id = object_row[1]
        project_id = object_row[2]

        # Check if the user is a member of the project associated with the object
        member_check = db.c.execute(
            '''
            SELECT role
            FROM project_user
            WHERE project_id = ? AND user_id = ?
            ''',
            (project_id, user_id)
        ).fetchone()

        if not member_check:
            return {"error": "Forbidden: You are not a member of the project associated with this object"}, 403

        user_role = member_check[0]

        # Only the object owner or a project owner can update the object
        if user_id != object_user_id and user_role != Role.OWNER.value:
            return {"error": "Forbidden: Only the object owner or a project owner can update the object"}, 403

        # Build the update query dynamically
        update_query = "UPDATE object SET update_date = CURRENT_TIMESTAMP, " + ", ".join(f"{key} = ?" for key in updates.keys()) + " WHERE id = ?"
        db.c.execute(update_query, (*updates.values(), object_id))
        db.commit()

        return {"message": "Object updated successfully"}, 200

    except Exception as e:
        log.error(f"Error updating object {object_id}: {e}")
        return {"error": "Internal server error"}, 500
    finally:
        db.close()
