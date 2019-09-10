import sqlite3
DATABASE = './data.db'
def get_db():
    db = sqlite3.connect(DATABASE)
    return db