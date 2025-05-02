from flask import Flask, session

def is_logged():
    return "user" in session.keys()

def is_logged_admin():
    return is_logged() and session["user"].admin
