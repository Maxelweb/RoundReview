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
            session["user"].load_properties_from_db(db)
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
