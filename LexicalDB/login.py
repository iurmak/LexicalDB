from LexicalDB import app
from flask import request, render_template, redirect, \
    url_for, session, flash
from LexicalDB.models import db, Users
from LexicalDB.supplement import Amend, Emails, Check
from itsdangerous import URLSafeTimedSerializer, exc, URLSafeSerializer
from os.path import join, dirname, realpath


@app.route('/auth', methods=['POST', 'GET'])
@app.route('/auth/<string:token>', methods=['POST', 'GET'])
def login(token=None):
    if request.method == 'GET':
        if token:
            try:
                email, password = URLSafeTimedSerializer(app.config['SECRET_KEY'],
                                                         salt='recover_password').loads(token,
                                                                                        max_age=3600)
            except exc.SignatureExpired:
                flash('Ссылка устарела.',
                      'alert alert-danger')
                return redirect(url_for('login'))
            Users.query.filter_by(email=email).first().password = password
            db.session.commit()
            return Amend.flash('Пароль изменён.', 'success', url_for('login'))

        if session.get('user'):
            session.clear()
        return render_template('login.html')

    elif request.method == 'POST':
        login = request.form.get('login')
        if request.form.get('new_password'):
            email = request.form.get('email')
            if Users.query.filter_by(email=email).first():
                token = URLSafeTimedSerializer(app.config['SECRET_KEY'], salt='recover_password').dumps(
                    [email, URLSafeSerializer(app.config["SECRET_KEY"], salt='password').dumps(request.form.get('new_password'))])
                Emails.send('Восстановление пароля',
                           f'''
                           <p>Если вы запрашивали изменение пароля, перейдите по ссылке:
                           <a href="{url_for('login', token=token, _external=True)}">
                           {url_for('login', token=token, _external=True)}</a>.</p>
                           <p>Если это письмо пришло по ошибке, проигнорируйте его.</p>''',
                           [email])
                return Amend.flash('Следуйте инструкциям, отправленным на имейл.',
                               'warning',
                               url_for('login'))
            else:
                return Amend.flash('Профиля с таким имейлом не существует.',
                               'danger',
                               url_for('login'))
        password = request.form.get('password')
        if '@' in login and Users.query.filter_by(email=login).first() and URLSafeSerializer(app.config["SECRET_KEY"], salt='password').dumps(password) ==\
                Users.query.filter_by(
                email=login).first().password:
            user_id = Users.query.filter_by(email=login).first().user_id
            session['user'] = URLSafeSerializer(app.config["SECRET_KEY"], salt='login').dumps(user_id)
            Users.query.get(user_id).last_seen = Check.time()
            db.session.commit()
            return Amend.flash(f'''Вы успешно вошли как {Amend.username(user_id, link=False)}!''',
                               'success',
                               url_for('profile'))
        elif Users.query.filter_by(username=login).first() and URLSafeSerializer(app.config["SECRET_KEY"], salt='password').dumps(password) ==\
                Users.query.filter_by(username=login).first().password:
            user_id = Users.query.filter_by(username=login).first().user_id
            session['user'] = URLSafeSerializer(app.config["SECRET_KEY"], salt='login').dumps(user_id)
            Users.query.get(user_id).last_seen = Check.time()
            db.session.commit()
            return Amend.flash(f'''Вы успешно вошли как {Amend.username(user_id, link=False)}!''',
                               'success',
                               url_for('profile'))
        else:
            return Amend.flash('Пользователя с указанными данными не существует.<br>Если вы зарегистрированы, перепроверьте логин и пароль.',
                               'danger',
                               url_for('login'))

@app.context_processor
def auth_check():
    def username(user_id):
        user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(user_id)
        return Users.query.get(user_id).username

    def status(user_id):
        user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(user_id)
        return Users.query.get(user_id).role_id

    def decypher_user_id(user_id):
        user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(user_id)
        return user_id
    return dict(username=username, status=status, decypher_user_id=decypher_user_id)
"""
@app.before_request
def check_for_maintenance():
    status = 0
    with open(join(dirname(realpath(__file__)), 'static/maintenance.txt'), 'r', encoding='UTF-8') as m:
        maintenance = int(m.readlines()[0])
    session.permanent = True
    whitelist = [
        url_for('maintenance'),
        url_for('login'),
        url_for('static', filename='css/bootstrap.css'),
        url_for('static', filename='js/jquery-3.2.1.slim.js'),
        url_for('static', filename='js/bootstrap.bundle.min.js'),
        url_for('static', filename='Shughni_logo_favicon.png')
    ]
    if session.get('user'):
        user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(session.get('user'))
        status = Users.query.get(user_id).role_id
    if maintenance and request.path not in whitelist and status != 3:
        return redirect(url_for('maintenance'))
    if maintenance and status == 3:
        return Amend.flash('Включён режим техобслуживания! Изменения могут не сохраниться!', 'danger')"""
