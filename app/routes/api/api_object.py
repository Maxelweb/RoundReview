import uuid, json, datetime, base64
from flask import request, session, Blueprint, current_app
from ..utils import is_logged, get_system_property, get_user_from_api_key, check_authentication, get_user_webhooks, call_webhook
from ...config import log, SYSTEM_MAX_UPLOAD_SIZE_MB, VERSION
from ...database import Database
from ...models import Project, Role, Object, ObjectStatus, SystemProperty

api_object_bp = Blueprint('api_object', __name__)

@api_object_bp.route("/api/projects/<project_id>/objects", methods=["GET"])
def project_objects_list(project_id:str):
    """ List all the objects inside the project """
    if not check_authentication():
        return {"error": "Unauthorized"}, 401

    user_id = session["user"].id if is_logged() else get_user_from_api_key(request.headers.get("x-api-key")).id

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

@api_object_bp.route("/api/projects/<project_id>/objects", methods=["POST"])
def project_objects_create(project_id: str):
    """ Create a new object inside the project, accepting application/pdf and storing file as blob """

    if not check_authentication():
        return {"error": "Unauthorized"}, 401

    user_id = session["user"].id if is_logged() else get_user_from_api_key(request.headers.get("x-api-key")).id

    # Check if the request contains a file
    if "file" not in request.files:
        return {"error": "Missing required file 'file'"}, 400

    file = request.files["file"]

    # Validate file type
    if file.content_type != "application/pdf":
        return {"error": "Invalid file type. Only 'application/pdf' is allowed"}, 400

    # Check if file is in fact a PDF (basic check)
    if not file.read(4) == b"%PDF":
        return {"error": "Invalid file content. The file is not a valid PDF."}, 400
    file.seek(0)  # Reset file pointer after reading

    # Read the file content as blob
    file_blob = file.read()

    # Block if max file size across the system exceeded
    max_file_size = SYSTEM_MAX_UPLOAD_SIZE_MB
    system_max_file_size = get_system_property(SystemProperty.OBJECT_MAX_UPLOAD_SIZE_MB)
    if system_max_file_size is not None:
        max_file_size = int(system_max_file_size)
    if len(file_blob) is not None and len(file_blob) > max_file_size * 1024 * 1024: 
        return {"error": f"File size exceeds the maximum allowed limit of {max_file_size} MB"}, 400

    # Extract metadata from the request
    data = request.form or request.json
    name = data.get("name")
    description = data.get("description", "") 
    path = data.get("path", "/")
    version = data.get("version", "")
    status = data.get("status", ObjectStatus.NO_REVIEW.value)

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
        db.log(user_id, f"project object add (project_id={project_id}, object_id={object_id})")
        return {"message": "Object created successfully", "object_id": object_id}, 201

    except Exception as e:
        log.error(f"Error creating object in project {project_id}: {e}")
        return {"error": "Internal server error"}, 500
    finally:
        db.close()

@api_object_bp.route("/api/objects/<object_id>", methods=["GET"])
def object_get(object_id: str, load_raw: bool=False):
    """ Get detail information of the object """

    if request.args.get("raw", "0") == "1":
        load_raw = True

    if not check_authentication():
        return {"error": "Unauthorized"}, 401

    user_id = session["user"].id if is_logged() else get_user_from_api_key(request.headers.get("x-api-key")).id

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
            # encode data to base64 to be JSON serializable
            if obj.raw is not None:
                obj.raw = str(base64.b64encode(obj.raw), "utf-8")


        return {"object": obj.to_dict()}, 200

    except Exception as e:
        log.error(f"Error fetching object {object_id}: {e}")
        return {"error": "Internal server error"}, 500
    finally:
        db.close()

@api_object_bp.route("/api/objects/<object_id>", methods=["DELETE"])
def object_delete(object_id: str):
    """ Delete an object """
    if not check_authentication():
        return {"error": "Unauthorized"}, 401

    user_id = session["user"].id if is_logged() else get_user_from_api_key(request.headers.get("x-api-key")).id

    db = Database()
    try:
        # Check if object delete is disabled across the system
        if get_system_property(SystemProperty.OBJECT_DELETE_DISABLED) == "TRUE":
            return {"error": "Object deletion is disabled across the system"}, 403

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
            return {"error": "Forbidden: Only the object author or a project owner can delete the object"}, 403

        # Delete the object
        db.c.execute(
            '''
            DELETE FROM object
            WHERE id = ?
            ''',
            (object_id,)
        )
        db.commit()
        db.log(user_id, f"project object delete (project_id={project_id}, object_id={object_id})")
        return {"message": "Object deleted successfully"}, 200

    except Exception as e:
        log.error(f"Error deleting object {object_id}: {e}")
        return {"error": "Internal server error"}, 500
    finally:
        db.close()

@api_object_bp.route("/api/objects/<object_id>", methods=["PUT"])
def object_update(object_id: str):
    """ Update an object """
    if not check_authentication():
        return {"error": "Unauthorized"}, 401

    user_id = session["user"].id if is_logged() else get_user_from_api_key(request.headers.get("x-api-key")).id

    data = request.form or request.json
    if not data:
        return {"error": "Missing request body"}, 400

    log.debug(data.items())

    allowed_fields = {"name", "description", "comments", "version", "status", "path"}
    allowed_fields_for_member  = {"name", "description", "version", "path"}
    allowed_fields_for_reviewer = {"name", "description", "comments", "version", "status", "path"}
    updates = {key: value for key, value in data.items() if key in allowed_fields}

    if "comments" in updates.keys():
        updates["comments"] = json.dumps(updates["comments"])

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

        # Allowed fields update for member
        if user_role == Role.MEMBER.value and not all([key in allowed_fields_for_member for key in updates.keys()]):
            return {"error": "Forbidden: Only the project owner or reviewer can update those fields"}, 403
        
        # Allowed fields update for reviewer
        if user_role == Role.REVIEWER.value and not all([key in allowed_fields_for_reviewer for key in updates.keys()]):
            return {"error": "Forbidden: Only the project owner can update those object fields"}, 403
        
        # Allowed fields update for owner
        if user_role == Role.OWNER.value and not all([key in allowed_fields for key in updates.keys()]):
            return {"error": "Forbidden: You cannot update those object fields"}, 403

        # Build the update query dynamically
        update_query = "UPDATE object SET update_date = CURRENT_TIMESTAMP, " + ", ".join(f"{key} = ?" for key in updates.keys()) + " WHERE id = ?"

        db.c.execute(update_query, (*updates.values(), object_id))
        db.commit()
        db.log(user_id, f"project object update (project_id={project_id}, keys={"|".join(f"{key}" for key in updates.keys())})")

        # Webhook: if status changed, trigger notification for reviewers and owners
        if get_system_property(SystemProperty.WEBHOOKS_DISABLED) != "TRUE" and "status" in updates.keys():
            webhooks = get_user_webhooks(project_id)
            seconds = 1
            for wh_user_id, wh_url in webhooks.items():
                current_app.scheduler.add_job(
                    func=call_webhook,
                    args=(wh_url, {
                        "event": "object.updated",
                        "object_id": object_id,
                        "project_id": project_id,
                        "updated_fields": {"status" : updates["status"]},
                        "updated_at": datetime.datetime.now().isoformat() + "Z",
                    }, {"Content-Type": "application/json", "User-Agent": f"RoundReview/{VERSION}"}),
                    name=f"webhook_object_updated_{object_id}_user_{wh_user_id}",
                    replace_existing=False,
                    max_instances=1,
                    misfire_grace_time=300,
                    trigger='date',
                    run_date=datetime.datetime.now() + datetime.timedelta(seconds=seconds)
                )
                seconds += 2 

        return {"message": "Object updated successfully"}, 200

    except Exception as e:
        log.error(f"Error updating object {object_id}: {e}")
        return {"error": "Internal server error"}, 500
    finally:
        db.close()
