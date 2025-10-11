import requests
from uuid import uuid4
from enum import Enum
from flask import render_template, request, session, redirect, Blueprint
from .utils import is_logged, is_logged_admin, log
from ..config import VERSION
from ..database import Database
from ..models import User, Property, LoginProvider

settings_blueprint = Blueprint('settings', __name__)

class ResultMessage(Enum): 
    NO_ACTION_WARNING = ("warning", "Nothing to do, the settings remain the same.")
    OLD_PSW_ERROR = ("error", "Old password wrong")
    MISMATCH_PSW_ERROR = ("error", "New password does not match the confirm password")
    SESSION_RELOAD_ERROR = ("error", "Unable to re-load session, please logout.")
    PASSWORD_UPDATE_SUCCESS = ("success", "Password changed successfully.")
    DEVELOPER_UPDATE_SUCCESS = ("success", "Developer settings updated successfully.")
    DEVELOPER_WEBHOOK_ERROR = ("error", "The URL is not reachable correctly. Make sure the return http status code is 200.")


@settings_blueprint.route("/settings", methods=["GET"])
def settings():
    """ Settings page """
    if not is_logged():
        return redirect("/")

    return render_template(
        "settings.html",
        user=session["user"],
        provider=session["provider"],
        providers=LoginProvider,
        title="Your Settings",
        version=VERSION,
        logged=is_logged(),
        admin=is_logged_admin(),
    )

@settings_blueprint.route("/settings/properties", methods=["POST"])
def properties():
    """ Submit properties update page """
    output = ""
    if not is_logged():
        return redirect("/")
    
    user:User = session["user"]
    db = Database()

    enable_api_key = request.form.get('enable_api_key', False)
    webhook_url = request.form.get('webhook_url', None)
    
    # Enable API Key
    if not user.has_prop(Property.API_KEY) and enable_api_key:
        value = str(uuid4())
        db.c.execute(
                'INSERT INTO user_property (key, value, user_id) VALUES (?,?,?)', 
                (Property.API_KEY.value, value, session['user'].id)
            )
        db.commit()
        db.log(session["user"].id, f"settings update (target={Property.API_KEY.value}, action=enable, value={value})")
        if not user.reload_from_db(db):
            output = ResultMessage.SESSION_RELOAD_ERROR
        else:
            output = ResultMessage.DEVELOPER_UPDATE_SUCCESS

    # Disable API Key
    elif user.has_prop(Property.API_KEY) and not enable_api_key:
        db.c.execute(
            'DELETE FROM user_property WHERE key = ? AND user_id = ?', 
            (Property.API_KEY.value, session['user'].id)
        )
        db.commit()
        db.log(session["user"].id, f"settings update (target={Property.API_KEY.value}, action=disable)")
        if not user.reload_from_db(db):
            output = ResultMessage.SESSION_RELOAD_ERROR
        else:
            output = ResultMessage.DEVELOPER_UPDATE_SUCCESS

    # Update Webhook URL
    elif user.has_prop(Property.API_KEY) and webhook_url is not None:
        if webhook_url == "" or webhook_url is None:
            # Remove property if empty
            db.c.execute(
                'DELETE FROM user_property WHERE key = ? AND user_id = ?', 
                (Property.WEBHOOK_URL.value, session['user'].id)
            )
            db.commit()
            db.log(session["user"].id, f"settings update (target={Property.WEBHOOK_URL.value}, action=disable)")
            if not user.reload_from_db(db):
                output = ResultMessage.SESSION_RELOAD_ERROR
            else:
                output = ResultMessage.DEVELOPER_UPDATE_SUCCESS
        else:
            # Try to reach the webhook URL
            status_code = None
            try:
                req = requests.head(webhook_url, timeout=5)
                status_code = req.status_code
            except Exception as e:
                log.error(f"Webhook URL validation error: {e}")

            if status_code != 200:
                output = ResultMessage.DEVELOPER_WEBHOOK_ERROR
            else:
                if user.has_prop(Property.WEBHOOK_URL):
                    db.c.execute(
                        'UPDATE user_property SET value = ? WHERE key = ? AND user_id = ?', 
                        (webhook_url, Property.WEBHOOK_URL.value, session['user'].id)
                    )
                    action = "update"
                else:
                    db.c.execute(
                        'INSERT INTO user_property (key, value, user_id) VALUES (?,?,?)', 
                        (Property.WEBHOOK_URL.value, webhook_url, session['user'].id)
                    )
                    action = "enable"
                db.commit()
                db.log(session["user"].id, f"settings update (target={Property.WEBHOOK_URL.value}, action={action}, value={webhook_url})")

                if not user.reload_from_db(db):
                    output = ResultMessage.SESSION_RELOAD_ERROR
                else:
                    output = ResultMessage.DEVELOPER_UPDATE_SUCCESS
    else:
        output = ResultMessage.NO_ACTION_WARNING

    db.close()
    return render_template(
        "settings.html",
        user=session["user"],
        provider=session["provider"],
        providers=LoginProvider,
        title="Settings",
        output=output.value,
        version=VERSION,
        logged=is_logged(),
        admin=is_logged_admin(),
    )

@settings_blueprint.route("/settings/password", methods=["POST"])
def password():
    """ Submit Password update page """
    output = ""
    if not is_logged():
        return redirect("/")
    db = Database()
    old_psw = request.form.get('old_password')
    new_psw = request.form.get('new_password')
    chk_psw = request.form.get('confirm_password')
    if old_psw is not None and new_psw is not None and chk_psw is not None:
        if db.hash(old_psw) != session['user']._password:
            output = ResultMessage.OLD_PSW_ERROR
        elif new_psw != chk_psw:
            output = ResultMessage.MISMATCH_PSW_ERROR
        else:
            db.c.execute(
                'UPDATE user SET password = ? WHERE id = ? LIMIT 1', 
                (db.hash(new_psw), session['user'].id)
            ).fetchone()
            db.commit()
            if not session["user"].reload_from_db(db):
                output = ResultMessage.SESSION_RELOAD_ERROR
            else:
                db.log(session["user"].id, "settings update (target=password)")
                output = ResultMessage.PASSWORD_UPDATE_SUCCESS
    db.close()
    return render_template(
        "settings.html",
        user=session["user"],
        provider=session["provider"],
        providers=LoginProvider,
        title="Settings",
        output=output.value,
        version=VERSION,
        logged=is_logged(),
        admin=is_logged_admin(),
    )