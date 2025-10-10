import uuid, json
from flask import request, session, Blueprint
from ..utils import is_logged
from ...config import VERSION, log, USER_SYSTEM_ID, SYSTEM_MAX_UPLOAD_SIZE_MB
from ...database import Database
from ...models import User, Project, Property, Role, Object, ObjectStatus, SystemProperty

api_integration_bp = Blueprint('api_integration', __name__)

# TODO: only reviewers or owners of that object can interact with these APIs

@api_integration_bp.route("/api/integration/reviews/objects/<object_id>", methods=["GET"])
def object_integration_get(object_id: str):
    """ Get all integration reviews for an object based on the table object_integration_review """
    pass

@api_integration_bp.route("/api/integration/reviews/objects/<object_id>", methods=["POST"])
def object_integration_create(object_id: str):
    """ Create an integration review for an object """
    pass

@api_integration_bp.route("/api/integration/reviews/<review_id>", methods=["GET"])
def object_integration_read(review_id: str):
    """ Read an integration review """
    pass

@api_integration_bp.route("/api/integration/reviews/<review_id>", methods=["PUT"])
def object_integration_update(review_id: str):
    """ Update an integration review """
    pass

@api_integration_bp.route("/api/integration/reviews/<review_id>", methods=["DELETE"])
def object_integration_delete(review_id: str):
    """ Delete an integration review """
    pass