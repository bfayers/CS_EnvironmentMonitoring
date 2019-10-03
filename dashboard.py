from flask import Blueprint, request, render_template, url_for, redirect
from db import get_db
from api import checkAccess

dashboard = Blueprint('dashboard', __name__)

def authCheck():
    userCookie = request.cookies.get('userCookie')
    if userCookie == None:
        return False
    else:
        response = checkAccess(userCookie)
        if response[1] == 'validCookie':
            return True
        else:
            return False

@dashboard.route('/')
def dash():
    if authCheck() == False:
        return redirect("/login")
    return render_template('dashboard/dashboard.html')

@dashboard.route('/sensors')
def dashSensors():
    if authCheck() == False:
        return redirect("/login")
    return render_template('dashboard/sensors'+request.args.get('do')+'.html')

@dashboard.route('/login')
def login():
    return render_template('dashboard/login.html')

@dashboard.route('/register')
def register():
    return render_template('dashboard/register.html')