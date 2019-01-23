import os
import hashlib
from flask import Flask, render_template, url_for, request, redirect, make_response
import sqlite3

DB_NAME = 'data.db'

app = Flask(__name__)


@app.route('/')
@app.route('/index')
def index():
    if request.cookies.get('token') != '':
        return redirect('profile')
    return render_template('index.html')


@app.route('/sign-in', methods=['POST'])
def signin():
    login = request.form['login']
    password = request.form['password']
    token = hashlib.sha3_256(bytes(login+password, encoding='utf-8')).hexdigest()
    db = sqlite3.connect(DB_NAME)
    try:
        user = db.execute("SELECT * FROM users WHERE login='%s'" % login).fetchone()
        if user is None:
            db.close()
            return render_template('index.html', sign_in_error='No such login')
        else:
            if user[2] != token:
                db.close()
                return render_template('index.html', sign_in_error='Incorrect password')
    except sqlite3.Error:
        print('database error')
    resp = make_response(redirect('profile'))
    resp.set_cookie('token', token)
    db.close()
    return resp


@app.route('/sign-up', methods=['POST'])
def signup():
    login = request.form['login']
    password = request.form['password']
    sha = hashlib.sha3_256(bytes(login + password, encoding='utf-8'))
    token = sha.hexdigest()
    db = sqlite3.connect(DB_NAME)
    try:
        db.execute("INSERT INTO users (login, token) VALUES ('%s', '%s')" % (login, token))
    except sqlite3.Error:
        db.close()
        return render_template('index.html', sign_up_error='Such login exists')
    resp = make_response(redirect('profile'))
    resp.set_cookie('token', token)
    db.commit()
    db.close()
    return resp


@app.route('/logout')
def logout():
    resp = make_response(redirect('index'))
    resp.set_cookie('token', '')
    return resp


@app.route('/profile')
def profile():
    return render_template('profile.html')

#
# CSS PROCESSING
#


@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)


def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                 endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)


app.run(host='192.168.1.6', port=8080, debug=True)
