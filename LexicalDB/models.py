from LexicalDB import app
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)


class Roles(db.Model):
    role_id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.Text, unique=True)
    users = db.relationship('Users', backref='role', lazy=True)

class Users(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text(40), nullable=False, unique=True)
    firstname = db.Column(db.Text(40), nullable=False)
    surname = db.Column(db.Text(40), nullable=False)
    email = db.Column(db.Text(100), unique=True)
    password = db.Column(db.Text(100))
    joined = db.Column(db.Integer, nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey(Roles.role_id), default=1)
    last_seen = db.Column(db.Integer, nullable=False)

class Examples(db.Model):
    example_id = db.Column(db.Integer, primary_key=True)
    example = db.Column(db.Text, unique=False)
    original_script = db.Column(db.Text, unique=False, nullable=True)
    translation = db.Column(db.Text, unique=False, nullable=True)
    source = db.Column(db.Text, unique=False, nullable=True)
    comment = db.Column(db.Text, unique=False, nullable=True)
    government = db.Column(db.Text, nullable=True, unique=False)

class Semantic_roles(db.Model):
    sr_id = db.Column(db.Integer, primary_key=True)
    sr = db.Column(db.Text, unique=True)

class Labels(db.Model):
    l_id = db.Column(db.Integer, primary_key=True)
    l = db.Column(db.Text, unique=False, nullable=False)
    decode= db.Column(db.Text, unique=False, nullable=True)
    type = db.Column(db.Integer, nullable=False) # 1 -- mer, 2 -- tax, 3 -- top
    rank = db.Column(db.Integer, nullable=True)

class Participants(db.Model):
    participant_id = db.Column(db.Integer, primary_key=True)
    participant = db.Column(db.Text, unique=False)
    sr_id = db.Column(db.Integer, db.ForeignKey(Semantic_roles.sr_id))
    other = db.Column(db.Text, unique=True)
    status = db.Column(db.Integer) #1 -- core, 2 -- peripheral
    type = db.Column(db.Integer, nullable=False, default=1)  # 1 -- from template, 2 -- from meanings

class Participant_relations(db.Model):
    participant_id = db.Column(db.Integer, db.ForeignKey(Participants.participant_id))
    target_id = db.Column(db.Integer, unique=False, primary_key=True)
    type = db.Column(db.Integer, unique=False) #1 -- taxonomy, 2 -- topology, 3 -- parent-child, 4 -- participant-meaning, 5 -- mereology

class Templates(db.Model):
    templ_id = db.Column(db.Integer, primary_key=True)
    templ = db.Column(db.Text, unique=True)
    created_by = db.Column(db.Integer, db.ForeignKey(Users.user_id))
    datetime = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Integer, nullable=False, default=1) # 1 -- not shown, 2 -- shown

class Template_relations(db.Model):
    templ_id = db.Column(db.Integer, db.ForeignKey(Templates.templ_id))
    target_id = db.Column(db.Integer, unique=False, primary_key=True)
    type = db.Column(db.Integer, unique=False) #1 -- parent-child, 2 -- ese, 3 -- example, 4 -- template-meaning, 9 -- template-participant

class Event_structure(db.Model):
    ese_id = db.Column(db.Integer, nullable=False, primary_key=True)
    ese = db.Column(db.Text, unique=False, nullable=False)
    type = db.Column(db.Integer, unique=False, nullable=False) #1 -- Initial States, 2 -- beginning, 3 -- Process, 4 -- Final stage, 5 -- Result, 6 -- Implications
    rank = db.Column(db.Integer, unique=False, nullable=False)
    status = db.Column(db.Integer, unique=False, nullable=True) #1 -- assertion, 2 -- presupposition

class Event_structure_relations(db.Model):
    ese_id = db.Column(db.Integer, nullable=False)
    target_id = db.Column(db.Integer, unique=False, primary_key=True)
    type = db.Column(db.Integer, unique=False, nullable=False) #1 -- belonging to a template, 2 -- belonging to a meaning

class Parts_of_speech(db.Model):
    pos_id = db.Column(db.Integer, primary_key=True)
    pos = db.Column(db.Text, unique=True)
    full_name = db.Column(db.Text, unique=True, nullable=True)

class Languages(db.Model):
    lang_id = db.Column(db.Integer, primary_key=True)
    lang = db.Column(db.Text, unique=True)
    code = db.Column(db.Text, unique=True, nullable=True)

class Lexemes(db.Model):
    lex_id = db.Column(db.Integer, primary_key=True)
    lang_id = db.Column(db.Integer, db.ForeignKey(Languages.lang_id))
    pos_id = db.Column(db.Integer, db.ForeignKey(Parts_of_speech.pos_id))

class Lexeme_relations(db.Model):
    lex_id = db.Column(db.Integer, nullable=False)
    target_id = db.Column(db.Integer, unique=False, primary_key=True)
    type = db.Column(db.Integer, unique=False, nullable=False) #1 -- meaning, 2 -- antonym, 3 -- synonym

class Forms(db.Model):
    form_id = db.Column(db.Integer, primary_key=True)
    lex_id = db.Column(db.Integer, db.ForeignKey(Lexemes.lex_id))
    type = db.Column(db.Integer, nullable=False) #1 -- form, 2 -- script form
    form = db.Column(db.Text, nullable=False)
    parent_id = db.Column(db.Integer, nullable=True)

class Meanings(db.Model):
    m_id = db.Column(db.Integer, primary_key=True)
    lex_id = db.Column(db.Integer, db.ForeignKey(Lexemes.lex_id))
    status = db.Column(db.Integer, nullable=False, default=1) # 1 -- not shown, 2 -- shown

class Example_to_meaning(db.Model):
    example_id = db.Column(db.Integer, db.ForeignKey(Examples.example_id), primary_key=True)
    m_id = db.Column(db.Integer, db.ForeignKey(Meanings.m_id), primary_key=False)