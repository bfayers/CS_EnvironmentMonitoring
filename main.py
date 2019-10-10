from flask import Flask
from api import api
from dashboard import dashboard

from db import get_db



app = Flask(__name__)

@app.teardown_appcontext
def close_connection(exception):
    db = get_db()
    if db is not None:
        db.close()

#@app.route('/')
#def main_page():
#    return 'Nothing Here, yet, check API docs'

@app.route('/init')
def init_db():
    db = get_db()
    with app.open_resource('database_schema.sql', mode='r') as f:
        #Execute the sql file as a script
        db.cursor().executescript(f.read())
        #Commit changes to database file
        db.commit()
    return "idk, probably worked?"

app.register_blueprint(api, url_prefix='/api')
app.register_blueprint(dashboard)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port='1234', debug=True)