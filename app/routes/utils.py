from flask import session, request
from ..models import Object, User, Property, SystemProperty
from ..config import USER_SYSTEM_ID, log
from ..database import Database

def is_logged():
    return "user" in session.keys()

def is_logged_admin():
    return is_logged() and session["user"].admin

def build_object_tree(objects:list[Object]) -> dict:
    tree = {'root': {'_objects': []}}
    for obj in objects:
        path_parts = obj.path.strip('/').split('/')
        current_level = tree['root']
        if path_parts == ['']:
            current_level['_objects'].append(obj)
            continue
        for part in path_parts:
            if part not in current_level:
                current_level[part] = {'_objects': []}
            current_level = current_level[part]
        current_level['_objects'].append(obj)
    return tree

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
            (Property.API_KEY.value, api_key)
        ).fetchone()
        db.close()
        if user_row:
            user = User(user_row)
            log.debug(f"API Key authentication successful for user ID {user.id}")
            return True
        
    # Check if the user is logged in via session
    if is_logged() and session["user"].id is not None:
        return True
    return False

def get_system_property(key: SystemProperty) -> str | None:
    """ Get a system property value by key """
    db = Database()
    try:
        row = db.c.execute(
            'SELECT value FROM user_property WHERE user_id = ? AND key = ? LIMIT 1',
            (USER_SYSTEM_ID, key.value)
        ).fetchone()
        if row:
            return row[0]
        return None
    except Exception as e:
        log.error(f"Error fetching system property {key}: {e}")
        return None
    finally:
        db.close()