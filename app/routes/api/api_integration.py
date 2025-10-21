import uuid
from flask import request, session, Blueprint
from ..utils import is_logged, check_authentication, get_user_from_api_key
from ...config import log
from ...database import Database
from ...models import Role, Review

api_integration_bp = Blueprint('api_integration', __name__)

@api_integration_bp.route("/api/projects/<project_id>/objects/<object_id>/integrations/reviews", methods=["GET"])
def object_review_get(project_id: str, object_id: str):
    """ Get all integration reviews for an object from a project """
    if not check_authentication():
        return {"error": "Unauthorized"}, 401
    
    user_id = session["user"].id if is_logged() else get_user_from_api_key(request.headers.get("x-api-key")).id

    db = Database()
    try:
        # Check if the user is a member of the project
        member_check = db.c.execute(
            '''
            SELECT Role
            FROM project_user
            WHERE project_id = ? AND user_id = ?
            ''',
            (project_id, user_id)
        ).fetchone()

        if not member_check:
            return {"error": "Forbidden: You are not a member of this project"}, 403

        # Check if the object exists in the project
        object_check = db.c.execute(
            '''
            SELECT 1
            FROM object
            WHERE project_id = ? AND id = ?
            ''',
            (project_id, object_id)
        ).fetchone()

        if not object_check:
            return {"error": "Forbidden: This object does not exist in this project"}, 403

        # Fetch all reviews for the object
        rows = db.c.execute(
            '''
            SELECT id, name, icon, url, url_text, value, created_at, user_id, object_id
            FROM object_integration_review
            WHERE object_id = ?
            ORDER BY created_at DESC
            ''',
            (object_id,)
        ).fetchall()

        # Convert rows to Object instances and then to dictionaries
        reviews = [Review.from_db_row(row).to_dict() for row in rows]
        return {"reviews": reviews}, 200

    except Exception as e:
        log.error(f"Error fetching reviews for project {project_id} and object {object_id}: {e}")
        return {"error": "Internal server error"}, 500
    finally:
        db.close()

@api_integration_bp.route("/api/projects/<project_id>/objects/<object_id>/integrations/reviews", methods=["POST"])
def object_review_create(project_id:str, object_id: str):
    """ Create an integration review for an object """
    if not check_authentication():
        return {"error": "Unauthorized"}, 401

    user_id = session["user"].id if is_logged() else get_user_from_api_key(request.headers.get("x-api-key")).id

    db = Database()
    try:

        # Sanitize input
        try:
            data = request.get_json()
            if not data:
                raise ValueError("No JSON data provided")
        except Exception as e:
            log.warning(f"Invalid JSON data provided: {e}")
            return {"error": "Bad Request: Invalid JSON data"}, 400
        
        # Check for required keys and types
        required_keys = {"name", "value"}
        if not required_keys.issubset(data.keys()):
            return {"error": f"Bad Request: Missing required keys: {required_keys - data.keys()}"}, 400
        
        # Validate input types and lengths
        name = data["name"]
        value = data["value"]
        icon = data.get("icon", None)
        url = data.get("url", None)
        url_text = data.get("url_text", None)
        if not isinstance(name, str) or not isinstance(value, str):
            return {"error": "Bad Request: 'name' and 'value' must be strings"}, 400
        if icon is not None and not isinstance(icon, str):
            return {"error": "Bad Request: 'icon' must be a string"}, 400
        if url is not None and not isinstance(url, str):
            return {"error": "Bad Request: 'url' must be a string"}, 400
        if url_text is not None and not isinstance(url_text, str):
            return {"error": "Bad Request: 'url_text' must be a string"}, 400
        if len(name) > 32:
            return {"error": "Bad Request: 'name' exceeds maximum length of 32 characters"}, 400
        if icon is not None and len(icon) > 32:
            return {"error": "Bad Request: 'icon' exceeds maximum length of 32 characters"}, 400
        if url is not None and len(url) > 128:
            return {"error": "Bad Request: 'url' exceeds maximum length of 128 characters"}, 400
        if url_text is not None and len(url_text) > 64:
            return {"error": "Bad Request: 'url_text' exceeds maximum length of 64 characters"}, 400
        if len(value) > 8192:
            return {"error": "Bad Request: 'value' exceeds maximum length of 8192 characters"}, 400

        # Check if the user is a member of the project
        member_check = db.c.execute(
            '''
            SELECT Role
            FROM project_user
            WHERE project_id = ? AND user_id = ?
            ''',
            (project_id, user_id)
        ).fetchone()

        if not member_check:
            return {"error": "Forbidden: You are not a member of this project"}, 403
        
        if member_check[0] not in [Role.OWNER.value, Role.REVIEWER.value]:
            return {"error": "Forbidden: You do not have permission to create reviews"}, 403

        # Check if the object exists in the project
        object_check = db.c.execute(
            '''
            SELECT 1
            FROM object
            WHERE project_id = ? AND id = ?
            ''',
            (project_id, object_id)
        ).fetchone()

        if not object_check:
            return {"error": "Forbidden: This object does not belong to this project"}, 403
        
        # Check if a review has been already created by this user for this object
        existing_review = db.c.execute(
            '''
            SELECT 1
            FROM object_integration_review
            WHERE object_id = ? AND user_id = ?
            ''',
            (object_id, user_id)
        ).fetchone()

        if existing_review:
            return {"error": "Conflict: You have already created a review for this object. Remove or update the current review."}, 409

        # Create new object integration review
        review_id = str(uuid.uuid4())
        db.c.execute(
            '''
            INSERT INTO object_integration_review (id, name, icon, url, url_text, value, user_id, object_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (review_id, name, icon, url, url_text, value, user_id, object_id)
        )
        db.commit()
        db.log(user_id, f"project object review add (project_id={project_id}, object_id={object_id}, review_id={review_id})")
        return {"message": "Review created successfully", "review_id": review_id }, 201

    except Exception as e:
        log.error(f"Error fetching reviews for project {project_id} and object {object_id}: {e}")
        return {"error": "Internal server error"}, 500
    finally:
        db.close()

@api_integration_bp.route("/api/integrations/reviews", methods=["GET"])
def integration_review_read_all(load_values: bool=True):
    """ Read all the integration reviews of the current authenticated user """
    if not check_authentication():
        return {"error": "Unauthorized"}, 401

    user_id = session["user"].id if is_logged() else get_user_from_api_key(request.headers.get("x-api-key")).id

    if request.args.get("value", "0") == "1":
        load_values = True

    db = Database()
    try:
        # Fetch all reviews for the user
        rows = db.c.execute(
            '''
            SELECT id, name, icon, url, url_text, value, created_at, user_id, object_id
            FROM object_integration_review
            WHERE user_id = ?
            ORDER BY created_at DESC
            ''',
            (user_id,)
        ).fetchall()

        # Convert rows to Object instances and then to dictionaries
        reviews = [Review.from_db_row(row).to_dict() for row in rows]
        
        # Remove the value field if not requested
        if not load_values:
            for review in reviews:
                review.pop("value", None)

        return {"reviews": reviews}, 200

    except Exception as e:
        log.error(f"Error fetching reviews for user {user_id}: {e}")
        return {"error": "Internal server error"}, 500
    finally:
        db.close()


@api_integration_bp.route("/api/integrations/reviews/<review_id>", methods=["DELETE"])
def integration_review_delete(review_id: str):
    """ Delete an integration review """

    if not check_authentication():
        return {"error": "Unauthorized"}, 401

    user_id = session["user"].id if is_logged() else get_user_from_api_key(request.headers.get("x-api-key")).id

    db = Database()
    try:
        # Check if the review exists and belongs to the user or the user is a reviewer or a owner of the project
        review_check = db.c.execute(
            '''
            SELECT 1
            FROM object_integration_review
            WHERE id = ? AND user_id = ?
            UNION
            SELECT 1
            FROM object_integration_review oir
            JOIN object o ON oir.object_id = o.id
            JOIN project_user pu ON o.project_id = pu.project_id
            WHERE oir.id = ? AND pu.user_id = ? AND pu.Role IN (?, ?)
            ''',
            (review_id, user_id, review_id, user_id, Role.OWNER.value, Role.REVIEWER.value)
        ).fetchone()

        if not review_check:
            return {"error": "Not Found: Review does not exist or cannot be deleted by you"}, 404
        
        # Delete the review
        db.c.execute(
            '''
            DELETE FROM object_integration_review
            WHERE id = ?
            ''',
            (review_id,)
        )
        db.commit()
        db.log(user_id, f"object review delete (review_id={review_id})")
        return {"message": "Review deleted successfully"}, 200
    except Exception as e:
        log.error(f"Error deleting review {review_id} for user {user_id}: {e}")
        return {"error": "Internal server error"}, 500
    finally:
        db.close()