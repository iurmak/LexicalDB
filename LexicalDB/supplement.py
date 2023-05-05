from markdown import markdown
from flask import session, url_for, Markup, redirect, flash
from LexicalDB.models import db, Users, Semantic_roles, Participants, Participant_relations,\
    Event_structure, Templates, Template_relations, Lexemes, Lexeme_relations, Forms, Parts_of_speech, Languages,\
    Examples, Event_structure_relations, Meanings, Labels, Example_to_meaning, Posts
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

    def delete(self, type):
        if type == 'meaning':
            lex_id = Meanings.query.filter_by(m_id=self).first().lex_id
            Meanings.query.filter_by(m_id=self).delete()
            for p in Participant_relations.query.filter_by(target_id=self, type=4).all():
                Participants.query.filter_by(participant_id=p.participant_id).delete()
            for e in Example_to_meaning.query.filter_by(m_id=self).all():
                Examples.query.filter_by(example_id=e.example_id).delete()
            Example_to_meaning.query.filter_by(m_id=self).delete()
            Participant_relations.query.filter_by(target_id=self, type=4).delete()
            Lexeme_relations.query.filter_by(target_id=self, type=1).delete()
            Template_relations.query.filter_by(target_id=self, type=4).delete()
            for ese in Event_structure_relations.query.filter_by(target_id=self, type=2).all():
                Event_structure.query.filter_by(ese_id=ese.ese_id).delete()
            Event_structure_relations.query.filter_by(target_id=self, type=2).delete()
            db.session.commit()
            return Amend.flash('Значение удалено.', 'success', url_for('edit_lexeme', lex_id=lex_id))

        elif type == 'template':
            return Amend.flash('Давайте сначала определимся, что нужно удалять.', 'warning', url_for('edit_template', templ_id=self))
            lex_id = Meanings.query.filter_by(m_id=self).first().lex_id
            Meanings.query.filter_by(m_id=self).delete()
            for p in Participant_relations.query.filter_by(target_id=self, type=4).all():
                Participants.query.filter_by(participant_id=p.participant_id).delete()
            for e in Example_to_meaning.query.filter_by(m_id=self).all():
                Examples.query.filter_by(example_id=e.example_id).delete()
            Example_to_meaning.query.filter_by(m_id=self).delete()
            Participant_relations.query.filter_by(target_id=self, type=4).delete()
            Lexeme_relations.query.filter_by(target_id=self, type=1).delete()
            for ese in Event_structure_relations.query.filter_by(target_id=self, type=2).all():
                Event_structure.query.filter_by(ese_id=ese.ese_id).delete()
            Event_structure_relations.query.filter_by(target_id=self, type=2).delete()
            db.session.commit()
            return Amend.flash('Значение удалено.', 'success', url_for('edit_lexeme', lex_id=lex_id))

        elif type == 'lexeme':
            for m in Meanings.query.filter_by(lex_id=self).all():
                m_id = m.m_id
                Meanings.query.filter_by(m_id=m_id).delete()
                for p in Participant_relations.query.filter_by(target_id=m_id, type=4).all():
                    Participants.query.filter_by(participant_id=p.participant_id).delete()
                for e in Example_to_meaning.query.filter_by(m_id=m_id).all():
                    Examples.query.filter_by(example_id=e.example_id).delete()
                Example_to_meaning.query.filter_by(m_id=m_id).delete()
                Participant_relations.query.filter_by(target_id=m_id, type=4).delete()
                Lexeme_relations.query.filter_by(target_id=m_id, type=1).delete()
                for ese in Event_structure_relations.query.filter_by(target_id=m_id, type=2).all():
                    Event_structure.query.filter_by(ese_id=ese.ese_id).delete()
                Event_structure_relations.query.filter_by(target_id=m_id, type=2).delete()
            Forms.query.filter_by(lex_id=self).delete()
            for p in Lexeme_relations.query.filter(Lexeme_relations.lex_id.in_([4,5])).filter_by(lex_id=self).all():
                Posts.query.filter_by(post_id=p.target_id).delete()
            Lexeme_relations.query.filter_by(lex_id=self).delete()
            Lexemes.query.filter_by(lex_id=self).delete()
            db.session.commit()
            return Amend.flash('Лексема удалена.', 'success', url_for('lexemes'))

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

    def ese(id, type, tooltips=True):
        if type == 'm':
            type = 2
        elif type == 't':
            type = 1
        else:
            return ''
        names = {
            1: 'Начальное состояние',
            2: 'Начало действия',
            3: 'Процесс',
            4: 'Завершение действия',
            5: 'Результат',
            6: 'Следствие'
        }
        current = []
        for ese in Event_structure_relations.query.filter_by(type=type, target_id=id).join(Event_structure, Event_structure_relations.ese_id==Event_structure.ese_id).order_by(Event_structure.type.asc()).all():
            if Event_structure.query.get(ese.ese_id):
                if Event_structure.query.get(ese.ese_id).type == 6:
                    ass_pres = ''
                elif Event_structure.query.get(ese.ese_id).status == 1:
                    ass_pres = ' (А)'
                elif Event_structure.query.get(ese.ese_id).status == 2:
                    ass_pres = ' (П)'
                current.append((names.get(Event_structure.query.get(ese.ese_id).type) + ass_pres, Event_structure.query.get(ese.ese_id).ese.replace('"', '&quot;')))
        if current:
            return Markup(', '.join([f'''<abbr style="" data-bs-toggle="tooltip" title="{c[1]}">{c[0]}</abbr>''' for c in current]))
        else:
            return ''

    def labels(self, type, tooltips=True):
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
                    f'<abbr style="" data-bs-toggle="tooltip" title="{l[1]}"><b>{l[0]}</b></abbr>'
                    for l in labels]
            else:
                labels = [f'<span style=""><b>{l[0]}</b></span>' for l in labels]
            labels = f"""<span>{', '.join(labels)}</span>"""
        elif labels and type == 'tax':
            if tooltips:
                labels = [
                    f'''<abbr style="" data-bs-toggle="tooltip" title="{l[1]}"><a href="" target="_blank">{l[0]}</a></abbr>'''
                    for l in labels]
            else:
                labels = [f'<span style=""><b>{l[0]}</b></span>' for l in labels]
            labels = f"""<span>{', '.join(labels)}</span>"""
        elif labels and type == 'top':
            if tooltips:
                labels = [
                    f'''<abbr style="" data-bs-toggle="tooltip" title="{l[1]}"><a href="" target="_blank">{l[0]}</a></abbr>'''
                    for l in labels]
            else:
                labels = [f'<span style=""><b>{l[0]}</b></span>' for l in labels]
            labels = f"""<span>{', '.join(labels)}</span>"""
        elif labels and type == 'mer':
            if tooltips:
                labels = [
                    f'''<abbr style="" data-bs-toggle="tooltip" title="{l[1]}"><a href="" target="_blank">{l[0]}</a></abbr>'''
                    for l in labels]
            else:
                labels = [f'<span style=""><b>{l[0]}</b></span>' for l in labels]
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