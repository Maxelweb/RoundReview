from flask import render_template, request, session, redirect, Blueprint, url_for, current_app
from .utils import is_logged, is_logged_admin
from ..config import VERSION, log, GITHUB_OAUTH_ENABLED, APP_NAME
from ..database import Database
from ..models import User, Log, SystemProperty, Property, LoginProvider
from .utils import get_system_property


basic_blueprint = Blueprint('basic', __name__)


@basic_blueprint.route('/')
def index():
    """ Index page """
    return render_template(
        "index.html",
        title=APP_NAME,
        version=VERSION,
        logged=is_logged(),
        admin=is_logged_admin(),
        user=session["user"] if is_logged() else None,
    )


@basic_blueprint.route("/login", methods=["POST", "GET"])
def login():
    """ Login page """
    output = ()
    if is_logged():
        return redirect("/")
    if request.method == "POST":
        db = Database()
        res = db.c.execute(
            'SELECT * FROM user WHERE email = ? AND password = ? AND admin >= 0 AND deleted = 0 LIMIT 1', 
            (
                request.form["email"],
                db.hash(request.form["password"])
            )
        ).fetchone()
        if not res:
            output = ("error", "Wrong email or password")
        else:
            user = User(res)
            # Check if user login is disabled across the system, but allow admin
            if get_system_property(SystemProperty.USER_LOGIN_DISABLED) == "TRUE":
                db.close()
                output = ("error", "User login is disabled across the system")
            else:
                session["user"] = user
                session["user"].load_properties_from_db(db)
                session["provider"] = LoginProvider.INTERNAL
                db.log(session["user"].id, f"login (provider={LoginProvider.INTERNAL.value})")
                db.close()
                return redirect("/")
        
    return render_template(
        "login.html",
        output=output,
        version=VERSION,
        github_enabled=GITHUB_OAUTH_ENABLED,
        logged=False,
        title="Login",
    )


@basic_blueprint.route("/login/redirects/github")
def login_redirect_github():
    """ Login using Github OAuth """
    if not GITHUB_OAUTH_ENABLED:
        return redirect("/")
    redirect_uri = url_for('basic.login_callback_github', _external=True)
    return current_app.oauth.create_client('github').authorize_redirect(redirect_uri)


@basic_blueprint.route("/login/callbacks/github")
def login_callback_github():
    """ Callback after login using Github OAuth """
    if not GITHUB_OAUTH_ENABLED:
        return redirect("/")
    try:
        github = current_app.oauth.create_client('github')
        _ = github.authorize_access_token()
            
        resp = github.get('user')
        profile = resp.json()
        github_username:str = profile['login']

        db = Database()
        res = db.c.execute(
            'SELECT u.* FROM user u, user_property up ON u.id = up.user_id WHERE up.key = ? AND up.value = ? AND u.admin >= 0 AND u.deleted = 0 LIMIT 1', 
            (Property.GITHUB_USERNAME.value, github_username.casefold(),)
        ).fetchone()
        if not res:
            output = ("error", "No internal user is associated with your GitHub account. Please ask the administrator to add you.")
        else:
            user = User(res)
            # Check if user login is disabled across the system, but allow admin
            if get_system_property(SystemProperty.USER_LOGIN_DISABLED) == "TRUE":
                db.close()
                output = ("error", "User login is disabled across the system")
            else:
                session["user"] = user
                session["user"].load_properties_from_db(db)
                session["provider"] = LoginProvider.GITHUB
                db.log(session["user"].id, f"login (provider={LoginProvider.GITHUB.value})")
                db.close()
                return redirect("/")
            
        db.close()
    except Exception as e:
        output = ("error", "Unable to login via Github. Please try again.")
        log.error("Unable to execute login via github provider: %s", e)
    return render_template(
        "login.html",
        output=output,
        version=VERSION,
        github_enabled=GITHUB_OAUTH_ENABLED,
        logged=False,
        title="Login",
    )

@basic_blueprint.route("/logout")
def logout():
    """ Logout page """
    session.pop("user", None)
    session.pop("provider", None)
    return redirect("/")
