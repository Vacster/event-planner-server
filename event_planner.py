import sqlite3
import requests
from flask import Flask, jsonify, request, Response
app = Flask(__name__)

@app.route('/event/create/<name>', methods=['POST'])
def create_event(name):
    conn = sqlite3.connect('events.db')
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = ?", (name,))
    result = c.fetchone()
    if result:
        conn.close()
        return Response("Table already exists", status=409)        
    else:
        content = request.get_json(silent=True)
        print(content)
        query = "CREATE TABLE "
        query += name
        query += " ( name text NOT NULL,"
        query += "code text NOT NULL PRIMARY KEY"
        for value in content['columns']:
            query += ", "
            query += value 
            query += " integer DEFAULT 0"
        query += ");"
        c.execute(query)
        conn.close()
        return Response(content, status=201)

@app.route('/event/<name>/users', methods=['POST'])
def add_users(name):
    conn = sqlite3.connect('events.db')
    c = conn.cursor()
    content = request.get_json()

    query = 'INSERT INTO '
    query += name
    query += '(name, code) values('
    for value in content['users']:
        inside_query = '\'' + value[0] + '\','
        inside_query += '\'' + value[1] + '\');'
        with conn:
            c.execute(query + inside_query)
    
    conn.close()
    return Response(str(len(content['users'])), status=201)

@app.route('/event/<name>', methods=['GET'])
def get_event(name):
    conn = sqlite3.connect('events.db')
    try:
        c = conn.execute('SELECT * FROM ' + name)
        names = [description[0] for description in c.description]
        print(names)
        conn.close()
        return jsonify(columns=names)
    except:
        conn.close()
        return Response('Event doesn\'t exists.', status=404)

@app.route('/event/<name>/<column>/<code>', methods=['PATCH'])
def mark_column(name, column, code):
    conn = sqlite3.connect('events.db')
    result = check(conn, name, column, code)

    if result == 0:
        conn.close()
        return Response(status=404)
    elif result == 1:
        conn.close()
        return Response(status=400)
    
    username = accept(conn, name, column, code)
    conn.close()
    return Response(username, status=200)

def check(conn, name, column, code):
    try:
        result = conn.execute("SELECT " + column + " FROM " + 
        name + " WHERE code = :code", {"code": code})
        return 1 if (result.fetchone()[0] == 1) else 2
    except Exception as e:
        print("Error in check")
        return 0

def accept(conn, name, column, code):
    conn.execute("UPDATE " + name + " SET " + column +
    " = 1 WHERE code = :code", {"code": code})
    conn.commit()
    cursor = conn.cursor()
    names = [name[0] for name in cursor.execute("SELECT name FROM " + name + " WHERE code = :code", {"code": code})]
    print(names)
    return names