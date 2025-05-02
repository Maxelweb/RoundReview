from types import SimpleNamespace
from flask import render_template, request, session, redirect, Blueprint
from .utils import is_logged, is_logged_admin
from ..config import VERSION, log
from ..database import Database
from ..models import User, Log

basic_blueprint = Blueprint('basic', __name__)

@basic_blueprint.route('/')
def index():
    """ Index page """
    return render_template(
        "index.html",
        title="Welcome",
        version=VERSION,
        logged=is_logged(),
        admin=is_logged_admin()
    )

@basic_blueprint.route("/login", methods=["POST", "GET"])
def login():
    """ Login page """
    output = ""
    if is_logged():
        return redirect("/")
    if request.method == "POST":
        db = Database()
        res = db.c.execute(
            'SELECT * FROM user WHERE email = ? AND password = ? AND admin >= 0 LIMIT 1', 
            (
                request.form["email"],
                db.hash(request.form["password"])
            )
        ).fetchone()
        if res:
            session["user"] = User(res)
            db.log(session["user"].id, "login")
            return redirect("/")
        else:
            output = ("error", "Wrong email or password")
        db.close()
    return render_template(
        "login.html",
        output=output,
        version=VERSION,
        logged=False,
        title="Login",
    )

@basic_blueprint.route("/logout")
def logout():
    """ Logout page """
    session.pop("user", None)
    return redirect("/")

@basic_blueprint.route("/settings", methods=["POST", "GET"])
def settings():
    """ Settings page """
    output = ""
    if not is_logged():
        return redirect("/")
    db = Database()
    old_psw = request.form.get('old_password')
    new_psw = request.form.get('new_password')
    chk_psw = request.form.get('confirm_password')
    if request.method == "POST" and old_psw is not None and new_psw is not None and chk_psw is not None:
        if db.hash(old_psw) != session['user']._password:
            output = ("error", "Old password wrong")
        elif new_psw != chk_psw:
            output = ("error", "New password does not match the confirm password field")
        else:
            db.c.execute(
                'UPDATE user SET password = ? WHERE id = ? LIMIT 1', 
                (db.hash(new_psw), session['user'].id)
            ).fetchone()
            db.commit()
            res = db.c.execute(
                'SELECT * FROM user WHERE id = ? LIMIT 1', (session['user'].id,)
            ).fetchone()
            if not res:
                output = ("error", "Unable to re-load session, please logout.")
            else:
                session["user"] = User(res)
                db.log(session["user"].id, "settings update (target=password)")
                output = ("success", "Password changed successfully.")
    db.close()
    return render_template(
        "settings.html",
        title="Settings",
        output=output,
        version=VERSION,
        logged=is_logged(),
        admin=is_logged_admin(),
    )