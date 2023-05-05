from LexicalDB import app
from flask import request, render_template, url_for, session
from LexicalDB.models import db, Users, Roles
from LexicalDB.supplement import Amend, Check, Emails
from itsdangerous import URLSafeSerializer


@app.route('/profile', methods=['GET', 'POST'])
@app.route('/profile/<int:user_id>', methods=['POST', 'GET'])
def profile(user_id=None):
    Check.update()
    if not session.get('user'):
        return Check.login()
    if user_id is None:
        user_id = URLSafeSerializer(app.config["SECRET_KEY"], salt='login').loads(session.get('user'))
    who = URLSafeSerializer(app.config["SECRET_KEY"], salt='login').loads(session.get('user'))

    if request.method == 'GET':
        if not Users.query.get(user_id):
            return Check.page()
        unique_edits = list()
        user = Users.query.get(user_id)
        return render_template('profile.html',
                               user_id=user_id,
                               user=user,
                               unique_edits=unique_edits,
                               Roles=Roles,
                               Check=Check,
                               Amend=Amend)

@app.route('/profile/edits', methods=['POST', 'GET'])
@app.route('/profile/<int:user_id>/edits', methods=['POST', 'GET'])
def edits(user_id=None):
    Check.update()
    if not session.get('user'):
        return Check.login()
    if user_id is None:
        user_id = URLSafeSerializer(app.config["SECRET_KEY"], salt='login').loads(session.get('user'))
    who = URLSafeSerializer(app.config["SECRET_KEY"], salt='login').loads(session.get('user'))

    if request.method == 'GET':
        if not Users.query.get(user_id):
            return Check.page()
        unique_edits = list()
        user = Users.query.get(user_id)
        return render_template('edits.html',
                               user_id=user_id,
                               user=user,
                               unique_edits=unique_edits,
                               Roles=Roles,
                               Check=Check,
                               Amend=Amend)

    elif request.method == 'POST':
        post = dict(request.form)
        user = Users.query.get(user_id)
        if post.get('new_password') and Users.query.get(who).role_id == 2 and user_id == who:
            current_password = URLSafeSerializer(app.config["SECRET_KEY"], salt='password').dumps(post.get('current_password'))
            if current_password != user.password:
                return Amend.flash('Текущий пароль введён неверно. Попробуйте ещё раз.', 'danger',
                                   url_for('profile'))
            Emails.send(f'''Смена пароля''',
                        f'''
                        <p>Подтверждаем, что ваш пароль на сайте {url_for('index', _external=True)} сменён.</p>
                        <p>Если это письмо пришло к вам по ошибке, проигнорируйте его.</p>
                        <p>Если вы не меняли пароль, <b>срочно</b> <a href="{url_for('contact', _external=True)}">
                        свяжитесь с администраторами</a>.</p>
                        ''',
                        [user.email])
            user.password = URLSafeSerializer(app.config["SECRET_KEY"], salt='password').dumps(post.get('new_password'))
            db.session.commit()
            return Amend.flash('Вы успешно сменили пароль.',
                               'success',
                               url_for('profile'))
        else:
            return Check.page()

@app.route('/profile/edit/<int:user_id>', methods=['POST', 'GET'])
def edit_profile(user_id):
    Check.update()
    if not session.get('user'):
        return Check.login()
    who = URLSafeSerializer(app.config["SECRET_KEY"], salt='login').loads(session.get('user'))
    if Users.query.get(who).role_id != 3:
        return Check.status()

    if request.method == 'GET':
        user = Users.query.get(user_id)
        return render_template('profile_editing.html',
                               user=user,
                               Roles=Roles,
                               Amend=Amend)

    elif request.method == 'POST':
        post = dict(request.form)
        user = Users.query.get(user_id)
        if post.get('new_password'):
            Emails.send(f'''Смена пароля''',
                        f'''
                        <p>Сообщаем, что вам сменили пароль (новый: <b>{post.get('new_password')}</b>) 
                        на сайте {url_for('index', _external=True)}.</p>
                        <p>Если это письмо пришло к вам по ошибке, проигнорируйте его.</p>''',
                        [user.email])
            user.password = URLSafeSerializer(app.config["SECRET_KEY"], salt='password').dumps(post.get('new_password'))
            db.session.commit()
            return Amend.flash('Вы успешно сменили пароль.',
                               'success',
                               url_for('edit_profile', user_id=user_id))
        if Users.query.filter_by(username=post.get('username')).first() and Users.query.filter_by(username=post.get('username')).first().user_id != user_id:
            return Amend.flash('Это имя занято.', 'danger', request.url)
        else:
            user.username = post.get('username')
        if Users.query.filter_by(email=post.get('email')).first() and Users.query.filter_by(email=post.get('email')).first().user_id != user_id:
            return Amend.flash('Этот имейл уже используется.', 'danger', request.url)
        elif user.email != post.get('email'):
            Emails.send('''Смена имейла''',
                        f'''<p>Просто подтверждаем, что вам сменили имейл 
                        на сайте {url_for('index', _external=True)}.</p>
                        <p>Если это письмо пришло к вам по ошибке, проигнорируйте его.</p>''',
                        [post.get('email')])
            user.email = post.get('email')
        user.firstname = post.get('firstname')
        user.surname = post.get('surname')
        user.role_id = post.get('role_id')
        db.session.commit()
        return Amend.flash('Вы успешно обновили данные профиля.',
                           'success',
                           url_for('profile', user_id=user_id))


@app.route('/profiles', methods=['GET', 'POST'])
@app.route('/profiles/<int:page>', methods=['GET', 'POST'])
def profiles(page=1):
    Check.update()
    if not session.get('user'):
        return Check.login()
    user_id = int(URLSafeSerializer(app.config["SECRET_KEY"], salt='login').loads(session.get('user')))
    if Users.query.get(user_id).role_id not in [2, 3]:
        return Check.status()
    if request.method == 'GET':
        page_of_profiles = Users.query.order_by(Users.user_id.desc()).paginate(page, 20)
        profiles = page_of_profiles.items
        return render_template('profiles.html',
                               profiles=profiles,
                               items=page_of_profiles,
                               Amend=Amend,
                               Roles=Roles)

    elif request.method == 'POST':
        if request.form.get('query'):
            if request.form.get('parameter') == 'ID':
                try:
                    profiles = Users.query.filter_by(user_id=int(request.form.get('query'))).order_by(Users.user_id.desc()).all()
                    page_of_profiles = None
                except:
                    return Amend.flash('Введите число.', 'danger', url_for('profiles'))
            elif request.form.get('parameter') == 'username':
                profiles = Users.query.filter_by(username=request.form.get('query')).order_by(Users.user_id.desc()).all()
                page_of_profiles = None
            elif request.form.get('parameter') == 'firstname':
                profiles = Users.query.filter_by(firstname=request.form.get('query')).order_by(Users.user_id.desc()).all()
                page_of_profiles = None
            elif request.form.get('parameter') == 'surname':
                profiles = Users.query.filter_by(surname=request.form.get('query')).order_by(Users.user_id.desc()).all()
                page_of_profiles = None
            elif request.form.get('parameter') == 'email':
                profiles = Users.query.filter_by(email=request.form.get('query')).order_by(Users.user_id.desc()).all()
                page_of_profiles = None
            return render_template('profiles.html',
                                   profiles=profiles,
                                   items=page_of_profiles,
                                   Amend=Amend,
                                   Roles=Roles)
        return Amend.flash('Введите поисковый запрос.', 'danger', url_for('profiles'))

@app.route('/profiles/add', methods=['GET', 'POST'])
def add_user():
    Check.update()
    if not session.get('user'):
        return Check.login()
    user_id = int(URLSafeSerializer(app.config["SECRET_KEY"], salt='login').loads(session.get('user')))
    if Users.query.get(user_id).role_id != 3:
        return Check.status()

    if request.method == 'GET':
        return render_template('add_user.html')

    elif request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        firstname = request.form.get('firstname')
        surname = request.form.get('surname')
        password = request.form.get('password')
        if Users.query.filter_by(email=email).first():
            taken_id = Users.query.filter_by(email=email).first().user_id
            return Amend.flash(
                f'''Имейл занят (см. профиль <a href="{url_for('profile', user_id=Amend.cypher_user(taken_id))}">{Users.query.filter_by(email=email).first().username}</a>).''',
                'warning', url_for('add_user'))
        elif Users.query.filter_by(username=username).first():
            taken_id = Users.query.filter_by(username=username).first().user_id
            return Amend.flash(
                f'''Отображаемое имя занято (см. <a href="{url_for('profile', user_id=Amend.cypher_user(taken_id))}">профиль</a>).''',
                'warning', url_for('add_user'))
        user = Users(
            username=username,
            email=email,
            password=URLSafeSerializer(app.config["SECRET_KEY"], salt='password').dumps(password),
            firstname=firstname,
            surname=surname,
            joined=Check.time(),
            role_id=2
        )
        db.session.add(user)
        db.session.commit()
        Emails.send('Создание профиля',
                    f'''
                    <p>Здравствуйте. Для вас создан профиль на сайте
                    <a href="{url_for('index', _external=True)}">{url_for('index', _external=True)}</a>.
                    </p><p>Пароль для <a href="{url_for('login', _external=True)}">входа</a>: 
                    <b>{password}</b>.
                    </p><p>Если это письмо пришло вам по ошибке, проигнорируйте его.</p>''',
                    [email])
        return Amend.flash('Профиль создан.', 'success',
                           url_for('profiles'))