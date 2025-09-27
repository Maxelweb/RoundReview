from flask import Flask, session
from ..models import Object, Role

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