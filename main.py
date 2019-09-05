from flask import Flask
from api import api

app = Flask(__name__)

@app.route('/')
def main_page():
    return 'Nothing Here, yet, check API docs'

app.register_blueprint(api, url_prefix='/api')


app.run(host='0.0.0.0', port='1234')