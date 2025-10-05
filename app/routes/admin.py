from datetime import datetime
from flask import render_template, request, session, redirect, Blueprint
from .utils import is_logged, is_logged_admin
from ..config import VERSION, log, USER_DEFAULT_PASSWORD, USER_SYSTEM_ID, WEBSITE_URL
from ..database import Database
from ..models import User, Log, SystemPropertyInfo, SystemProperty

admin_blueprint = Blueprint('admin', __name__)

@admin_blueprint.route('/admin/users', methods=["POST", "GET"])
def users():
    """ Admin Users page """
    if not is_logged_admin():
        return redirect("/")
    db = Database()
    output = ""
    user_id = request.form.get('user_id') or request.args.get('user_id')
    user_email = request.form.get('email')
    target = request.form.get('target')
    check_list = [str(session["user"].id), str(USER_SYSTEM_ID)]
    if request.method == "POST":
        if target == "email" and user_id not in check_list and user_email is not None:
            db.c.execute('UPDATE user SET email = ? WHERE id = ? LIMIT 1', (user_email,user_id))
            db.commit()
            output = ("success", f"User #{user_id} email updated!")
            db.log(session["user"].id, f"user email update (user_id={user_id})")
        elif target == "undelete" and user_id not in check_list:
            db.c.execute('UPDATE user SET deleted = ? WHERE id = ? LIMIT 1', (0,user_id))
            db.commit()
            output = ("success", f"User #{user_id} undeleted!")
            db.log(session["user"].id, f"user undeleted (user_id={user_id})")
        elif target == "delete" and user_id not in check_list:
            db.c.execute('UPDATE user SET deleted = ? WHERE id = ? LIMIT 1', (1,user_id))
            db.commit()
            output = ("success", f"User #{user_id} deleted!")
            db.log(session["user"].id, f"user deleted (user_id={user_id})")
        elif target == "password" and user_id not in check_list:
            db.c.execute('UPDATE user SET password = ? WHERE id = ? LIMIT 1', (db.hash(USER_DEFAULT_PASSWORD),user_id))
            db.commit()
            output = ("success", f"User #{user_id} updated with new password: {USER_DEFAULT_PASSWORD}")
            db.log(session["user"].id, f"user password reset (user_id={user_id})")
        elif target == "user":
            if request.form["name"] is None or request.form["email"] is None:
                output = ("error", "Unable to add user, some fields are missing")
            else:
                db.c.execute('INSERT INTO user (name, email, password) VALUES (?,?,?)', (request.form["name"],request.form["email"],db.hash(USER_DEFAULT_PASSWORD)))
                db.commit()
                user_res = db.c.execute('SELECT * FROM user WHERE email = ? LIMIT 1', (request.form["email"],)).fetchone()
                if user_res is None:
                    output = ("error", "Unable to add user, check the inserted fields.")
                else:
                    user = User(user_res)
                    output = ("success", f"New user #{user.id} added with password: {USER_DEFAULT_PASSWORD}")
                    db.log(session["user"].id, f"user add (user_id={user.id})")
    res = db.c.execute('SELECT * FROM user ORDER BY id DESC').fetchall()
    users = [User(row) for row in res]
    db.close()
    return render_template(
        "admin/users.html",
        output=output,
        users=users,
        selected_user_id=int(user_id) if user_id is not None else 0,
        title="Users",
        version=VERSION,
        logged=is_logged(),
        admin=is_logged_admin(),
        user=session["user"],
    )

@admin_blueprint.route('/admin/logs')
def logs():
    """ Admin logs page """
    if not is_logged_admin():
        return redirect("/")
    db = Database()
    action = request.args.get("action")
    user_id = request.args.get("user_id")
    start_query = "SELECT * FROM log "
    params = ()
    where_query = "WHERE 1=1"
    if action not in [None, '']:
        where_query += " AND action LIKE ?"
        params += (f"%{action}%",)
    if user_id not in [None, '']:
        where_query += " AND user_id = ?"
        params += (user_id,)
    res = db.c.execute(start_query + where_query + " ORDER BY id DESC", params).fetchall()
    logs = [Log(row) for row in res]
    for log in logs:
        log.user = User(db.c.execute("SELECT * FROM user WHERE id = ? LIMIT 1", (log.user_id,)).fetchone())
    db.close()
    return render_template(
        "admin/logs.html",
        logs=logs,
        title="Logs",
        action=action,
        user_id=int(user_id) if user_id not in [None, ''] else None,
        version=VERSION,
        logged=is_logged(),
        admin=is_logged_admin(),
        user=session["user"],
    )

@admin_blueprint.route("/admin/settings", methods=["GET", "POST"])
def settings():
    """ Global Settings page """
    if not is_logged_admin():
        return redirect("/")
    output = None
    db = Database()
    res = db.c.execute(
        'SELECT * FROM user WHERE id = ? AND admin = -1 LIMIT 1', 
        (USER_SYSTEM_ID,)
    ).fetchone()
    if res:
        sys_user = User(res)
        sys_user.load_properties_from_db(db)
    if request.method == "POST":
        error = False
        # For each request form key, update the system user property
        for key in request.form:
            value = request.form.get(key)
            if value is not None:
                if not SystemProperty[key].check_value(value):
                    output = ("error", f"Invalid value for {key}: {value} (see description below the field)")
                    error = True
                    break
                sys_user.properties[key] = value
                db.c.execute(
                    'UPDATE user_property SET value = ? WHERE user_id = ? AND key = ?',
                    (value, sys_user.id, key)
                )
                db.commit()
                db.log(session["user"].id, f"system property update (key={key}, value={value})")
        if not error:
            output = ("success", "Global settings updated!")
    db.close()
    return render_template(
        "admin/settings.html",
        title="Global Settings",
        syspropinfo=SystemProperty,
        sys_user=sys_user,
        version=VERSION,
        output=output,
        logged=is_logged(),
        admin=is_logged_admin(),
        user=session["user"],
    )
