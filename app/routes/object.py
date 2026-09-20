import base64
import io
import json
import fitz
from types import SimpleNamespace
from flask import render_template, request, session, Blueprint, redirect, send_file
from .utils import is_logged, is_logged_admin
from ..config import VERSION, log
from ..database import Database
from ..models import Project, Object, ObjectStatus, Role, Review
from .api import project_list, object_get, object_update, object_review_get
from .project import get_user_role_in_project


object_blueprint = Blueprint('object', __name__)


@object_blueprint.route('/projects/<project_id>/objects/<object_id>', methods=["GET"])
def view_object(project_id: str, object_id: str):
    """ View and handle the object of a specific project """
    if not is_logged():
        return redirect("/")
    output = ()
    project:Project = None
    obj:Object = None
    can_edit = True if get_user_role_in_project(project_id) in [Role.OWNER, Role.REVIEWER, Role.MEMBER] else False
    can_review = True if get_user_role_in_project(project_id) in [Role.OWNER, Role.REVIEWER] else False

    res, status = project_list()
    if status == 200:
        project = next((Project.from_dict(elem) for elem in res["projects"] if elem["id"] == int(project_id)), None)
        
    res, status = object_get(object_id, load_raw=False)
    if status == 200:
        obj = Object.from_dict(res["object"])
    else:
        output = ("error", res["error"])

    res, status = object_review_get(project_id=project_id, object_id=object_id)
    reviews = []
    if status == 200:
        reviews = [Review.from_dict(data=review) for review in res["reviews"]] 
    else:
        output = ("error", res["error"])

    db = Database()
    res = obj.load_user(db=db)
    log.debug("User loading in object: %s", res)
    db.close()

    return render_template(
        "project/object/view.html",
        title=obj.name,
        user=session["user"],
        object=obj,
        project=project,
        output=output,
        version=VERSION,
        logged=is_logged(),
        admin=is_logged_admin(),
        can_edit=can_edit,
        can_review=can_review,
        project_role=get_user_role_in_project(project_id),
        object_statuses=ObjectStatus,
        reviews=reviews,
    )


@object_blueprint.route('/projects/<project_id>/objects/<object_id>/file', methods=["GET"])
def get_file(project_id: str, object_id: str):
    """ Serve the file associated with the object """
    if not is_logged():
        return redirect("/")
    res, status = object_get(object_id, load_raw=True)
    if status == 200:
        obj = Object.from_dict(res["object"])
        if obj.raw is not None:
            raw_object = base64.b64decode(obj.raw)
            return (
                raw_object,
                200,
                {
                    "Content-Type": "application/pdf",
                    "Content-Disposition": f"inline; filename={obj.name}.pdf"
                }
            )
        else:
            return {"error": "PDF content not found"}, 404
    else:
        return {"error": f"Error fetching object: {res['error']}"}, status


@object_blueprint.route('/api/projects/<project_id>/objects/<object_id>/file/comments', methods=["GET"])
def get_file_with_comments(project_id: str, object_id: str):
    """Serve a copy of the PDF with its comments as standard PDF annotations."""
    if not is_logged():
        return {"error": "Unauthorized"}, 401

    res, status = object_get(object_id, load_raw=True)
    if status != 200:
        return {"error": f"Error fetching object: {res['error']}"}, status

    obj = Object.from_dict(res["object"])
    if str(obj.project_id) != str(project_id):
        return {"error": "Object not found"}, 404
    if obj.raw is None:
        return {"error": "PDF content not found"}, 404

    raw_object = base64.b64decode(obj.raw)
    document = fitz.open(stream=raw_object, filetype="pdf")
    try:
        comments_data = json.loads(obj.comments or '{"inlineComments": []}')
    except (TypeError, json.JSONDecodeError):
        comments_data = {"inlineComments": []}

    for comment in comments_data.get("inlineComments", []):
        try:
            page_number = int(comment.get("page", 1)) - 1
            x = float(comment["x"])
            y = float(comment["y"])
            if not 0 <= page_number < len(document):
                continue

            page = document[page_number]
            annotation_text = comment.get("text", "")
            annotation = page.add_text_annot(fitz.Point(x, y), annotation_text, icon="Comment")
            annotation.set_info(
                title=comment.get("authorName", "Round Review"),
                subject="Round Review comment",
            )
            annotation.update()
        except (KeyError, TypeError, ValueError):
            continue

    metadata = document.metadata or {}
    metadata["producer"] = "Round Review"
    metadata["creator"] = metadata.get("creator") or "Round Review"
    metadata["keywords"] = ", ".join(filter(None, [metadata.get("keywords", ""), "Round Review"]))
    document.set_metadata(metadata)
    output = document.tobytes(garbage=4, deflate=True)
    document.close()

    return send_file(
        io.BytesIO(output),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{obj.name}-with-comments.pdf",
    )


@object_blueprint.route('/projects/<project_id>/objects/<object_id>/edit', methods=["GET", "POST"])
def edit_object(project_id: str, object_id: str):
    """ Edit and handle the object of a specific project """
    if not is_logged():
        return redirect("/")
    output = ()
    obj:Object = None
    can_edit = True if get_user_role_in_project(project_id) in [Role.OWNER, Role.REVIEWER, Role.MEMBER] else False

    # Update documentation
    if request.method == "POST":
        res, status = object_update(request.form.get('object_id', None))
        if status == 200:
            output = ("success", "Document information updated successfully!")
        else:
            output = ("error", res["error"])

    res, status = object_get(object_id, load_raw=False)
    if status == 200:
        obj = Object.from_dict(res["object"])
    else:
        output = ("error", res["error"])

    return render_template(
        "project/object/edit.html",
        title="Update document",
        user=session["user"],
        object=obj,
        project_id=project_id,
        output=output,
        version=VERSION,
        logged=is_logged(),
        admin=is_logged_admin(),
        can_edit=can_edit,
        project_role=get_user_role_in_project(project_id),
        object_statuses=ObjectStatus,
    )