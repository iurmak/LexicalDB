from LexicalDB import app
from flask import render_template, request, url_for, session, redirect, send_file
from LexicalDB.supplement import Emails, Amend, Check
from LexicalDB.models import db, Users
from itsdangerous import URLSafeSerializer
from os.path import join, dirname, realpath


@app.route('/')
def index():
    return redirect('profiles')

@app.route('/sabr')
def maintenance():
    with open(join(dirname(realpath(__file__)), 'static/maintenance.txt'), 'r', encoding='UTF-8') as m:
        status = int(m.readlines()[0])
    if session.get('user'):
        user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(session.get('user'))
        if Users.query.get(user_id).role_id == 3:
            with open(join(dirname(realpath(__file__)), 'static/maintenance.txt'), 'w', encoding='UTF-8') as m:
                if status:
                    m.write('0')
                else:
                    m.write('1')
            return redirect(url_for('settings'))
        else:
            if status:
                return render_template('maintenance.html')
            else:
                return redirect(url_for('index'))
    else:
        if status:
            return render_template('maintenance.html')
        else:
            return redirect(url_for('index'))


@app.route('/download_db', methods=['GET', 'POST'])
def download_db():
    Check.update()
    if not session.get('user'):
        return Check.login()
    user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(session.get('user'))
    if Users.query.get(user_id).role_id != 3:
        return Check.status()
    return send_file('lex_typ.db', as_attachment=True)