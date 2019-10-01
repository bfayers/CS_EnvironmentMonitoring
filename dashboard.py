from flask import Blueprint, request, render_template, url_for


dashboard = Blueprint('dashboard', __name__)


@dashboard.route('/')
def login():
    return render_template('dashboard/login.html')

@dashboard.route('/register')
def register():
    return render_template('dashboard/register.html')