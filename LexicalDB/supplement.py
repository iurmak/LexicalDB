from markdown import markdown
from flask import session, url_for, Markup, redirect, flash
from LexicalDB.models import Users
from flask_mail import Mail, Message
from LexicalDB import app
from bs4 import BeautifulSoup
from time import strftime, gmtime
from calendar import timegm
from re import sub, IGNORECASE
from json import dumps, loads
from itsdangerous import URLSafeSerializer
from LexicalDB.models import Participant_relations, Labels


mail = Mail(app)

class Amend:
    def anti_html(self):
        if self:
            return BeautifulSoup(self, features='html.parser').get_text()

    def md(self, html=False, delete_p=True, delete_br=True):
        if not self:
            return self
        if self:
            if html:
                string = markdown(self, extensions=['nl2br'])
            else:
                string = markdown(Amend.anti_html(self), extensions=['nl2br'])
            if delete_p:
                for tag in ['<p>', '</p>']:
                    string = string.replace(tag, '')
            if delete_br:
                for tag in ['<br />', '<br />']:
                    string = string.replace(tag, '')
            string = string.replace('<img', '<img class="img-fluid"').replace('--', '–')
            return Markup(string)

    def username(self, link=True):
        role_id = Users.query.get(self).role_id
        if role_id == 2:
            if link:
                username = Markup(f"""<a href="{url_for('profile', user_id=self)}" class="link-success">{Users.query.get(self).username}</a>""")
            else:
                username = Markup(f"""<span class="text-success">{Users.query.get(self).username}</span>""")
        elif role_id == 3:
            if link:
                username = Markup(f"""<a href="{url_for('profile', user_id=self)}" class="link-danger">{Users.query.get(self).username}</a>""")
            else:
                username = Markup(f"""<span class="text-danger">{Users.query.get(self).username}</span>""")
        else:
            username = None
        return username

    def flash(self, type, url=None):
        flash(Markup(self), f'alert alert-{type}')
        if url:
            return redirect(url)

    def cypher_unit(self):
        return URLSafeSerializer(app.config['SECRET_KEY'], salt='entry').dumps(self)

    def cypher_user(self):
        return URLSafeSerializer(app.config['SECRET_KEY'], salt='login').dumps(self)

    def datetime(self):
        return strftime('%d.%m.%Y %H:%M', gmtime(self+10800))

    def spaces(self):
        while self.endswith(' ') or self.endswith(' ') or self.endswith(',') or self.endswith(';'):
            self = self[:-1]
        while self.startswith(' ') or self.startswith(' ') or self.startswith(',') or self.startswith(';'):
            self = self[1:]
        return self

    def mark(what, where):
        what = what.replace(r'([ \.!\?\\,\(\)\[\]\"\':;&\$^#@=\|\n]|^)', '').replace(r'([ \.!\?\\,\(\)\[\]\"\':;&\$^#@=\|\n]|$)', '')
        #where = sub(r'(-|=)', '(-|=|)', where)
        return Markup(sub(what, r"<mark class='p-0'>\1</mark>", where, flags=IGNORECASE))

class Check():
    def time(self=None):
        return timegm(gmtime())
    def update(self=None):
        return None

    def status(self=None):
        return Amend.flash('У вас недостаточно прав для этого действия.', 'danger', url_for('profile'))
    def login(self=None):
        return Amend.flash('Для выполнения этого действия нужно войти.', 'danger', url_for('login'))
    def page(url='/'):
        return Amend.flash('Такой страницы не существует.', 'danger', url)
    def index(self, list):
        if not list:
            return None
        if isinstance(list, str):
            list = [list]
        return list.index(self)
    def len(self):
        return len(self)
    def range(self, max):
        return range(self, max)
    def set(self):
        dic = {}
        for i in self:
            dic.update({i:0})
        return list(dict(dic))
    def split(what, by, to_int=False):
        if what and isinstance(what, str):
            if to_int:
                return [int(i) for i in what.split(by)]
            return what.split(by)
        return []
    def labels(self, type, tooltips=True):
        print(self, type)
        if type == 'tax':
            labels = [(Labels.query.get(l.target_id).l, Labels.query.get(l.target_id).decode, Labels.query.get(l.target_id).l_id) for l in
                      Participant_relations.query.filter_by(type=1, participant_id=self).join(Labels, Participant_relations.target_id==Labels.l_id).order_by(
                          Labels.rank.asc(), Labels.l.asc()).all()]
        elif type == 'top':
            labels = [(Labels.query.get(l.target_id).l, Labels.query.get(l.target_id).decode, Labels.query.get(l.target_id).l_id) for l in
                      Participant_relations.query.filter_by(type=2, participant_id=self).join(Labels,
                                                                         Participant_relations.target_id == Labels.l_id).order_by(
                          Labels.rank.asc(), Labels.l.asc()).all()]
        elif type == 'mer':
            labels = [(Labels.query.get(l.target_id).l, Labels.query.get(l.target_id).decode, Labels.query.get(l.target_id).l_id) for l in
                      Participant_relations.query.filter_by(type=5, participant_id=self).join(Labels,
                                                                         Participant_relations.target_id == Labels.l_id).order_by(
                          Labels.rank.asc(), Labels.l.asc()).all()]
        if labels and type not in ['tax', 'top', 'mer']:
            if tooltips:
                labels = [
                    f'<abbr style="font-variant-caps: small-caps" data-bs-toggle="tooltip" title="{l[1]}"><b>{l[0]}</b></abbr>'
                    for l in labels]
            else:
                labels = [f'<span style="font-variant-caps: small-caps"><b>{l[0]}</b></span>' for l in labels]
            labels = f"""<span>{', '.join(labels)}</span>"""
        elif labels and type == 'tax':
            if tooltips:
                labels = [
                    f'''<abbr style="font-variant-caps: small-caps" data-bs-toggle="tooltip" title="{l[1]}"><a href="" target="_blank">{l[0]}</a></abbr>'''
                    for l in labels]
            else:
                labels = [f'<span style="font-variant-caps: small-caps"><b>{l[0]}</b></span>' for l in labels]
            labels = f"""<span>{', '.join(labels)}</span>"""
        elif labels and type == 'top':
            if tooltips:
                labels = [
                    f'''<abbr style="font-variant-caps: small-caps" data-bs-toggle="tooltip" title="{l[1]}"><a href="" target="_blank">{l[0]}</a></abbr>'''
                    for l in labels]
            else:
                labels = [f'<span style="font-variant-caps: small-caps"><b>{l[0]}</b></span>' for l in labels]
            labels = f"""<span>{', '.join(labels)}</span>"""
        elif labels and type == 'mer':
            if tooltips:
                labels = [
                    f'''<abbr style="font-variant-caps: small-caps" data-bs-toggle="tooltip" title="{l[1]}"><a href="" target="_blank">{l[0]}</a></abbr>'''
                    for l in labels]
            else:
                labels = [f'<span style="font-variant-caps: small-caps"><b>{l[0]}</b></span>' for l in labels]
            labels = f"""<span>{', '.join(labels)}</span>"""
        else:
            return ''
        return Markup(labels)

class Emails():
    def send(heading, body, to, reply_to=None):
        msg = Message(heading, recipients=to)
        msg.html = body
        if reply_to:
            msg.reply_to = reply_to
        return mail.send(msg)

class BackUp():
    def row(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}