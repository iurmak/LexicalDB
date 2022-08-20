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

class Beginnings(db.Model):
    beg_id = db.Column(db.Integer, primary_key=True)
    beg = db.Column(db.Text, unique=True)
    rank = db.Column(db.Integer)

class Examples(db.Model):
    example_id = db.Column(db.Integer, primary_key=True)
    example = db.Column(db.Text, unique=False)

class Final_stages(db.Model):
    fs_id = db.Column(db.Integer, primary_key=True)
    fs = db.Column(db.Text, unique=True)
    rank = db.Column(db.Integer)

class Implications(db.Model):
    impl_id = db.Column(db.Integer, primary_key=True)
    impl = db.Column(db.Text, unique=True)
    rank = db.Column(db.Integer)

class Initial_states(db.Model):
    inst_id = db.Column(db.Integer, primary_key=True)
    inst = db.Column(db.Text, unique=True)
    rank = db.Column(db.Integer)

class Processes(db.Model):
    proc_id = db.Column(db.Integer, primary_key=True)
    proc = db.Column(db.Text, unique=True)
    rank = db.Column(db.Integer)

class Results(db.Model):
    res_id = db.Column(db.Integer, primary_key=True)
    res = db.Column(db.Text, unique=True)
    rank = db.Column(db.Integer)

class Semantic_roles(db.Model):
    sr_id = db.Column(db.Integer, primary_key=True)
    sr = db.Column(db.Text, unique=True)

class Taxonomy(db.Model):
    tax_id = db.Column(db.Integer, primary_key=True)
    tax = db.Column(db.Text, unique=True)

class Topology(db.Model):
    top_id = db.Column(db.Integer, primary_key=True)
    top = db.Column(db.Text, unique=True)

class Participants(db.Model):
    participant_id = db.Column(db.Integer, primary_key=True)
    participant = db.Column(db.Text, unique=True)
    sr_id = db.Column(db.Integer, db.ForeignKey(Semantic_roles.sr_id))
    other = db.Column(db.Text, unique=True)
    status = db.Column(db.Integer) #1 -- core, 2 -- peripheral

class Participant_relations(db.Model):
    participant_id = db.Column(db.Integer, db.ForeignKey(Participants.participant_id))
    target_id = db.Column(db.Integer, unique=False, primary_key=True)
    type = db.Column(db.Integer, unique=False) #1 -- taxonomy, 2 -- topology, 3 -- parent-child

class Templates(db.Model):
    templ_id = db.Column(db.Integer, primary_key=True)
    templ = db.Column(db.Text, unique=True)
    created_by = db.Column(db.Integer, db.ForeignKey(Users.user_id))
    datetime = db.Column(db.Integer, nullable=False)

class Template_relations(db.Model):
    templ_id = db.Column(db.Integer, db.ForeignKey(Templates.templ_id))
    target_id = db.Column(db.Integer, unique=False, primary_key=True)
    type = db.Column(db.Integer, unique=False) #1 -- parent-child, 2 -- beg, 3 -- example, 4 -- final stage, 5 -- impl,\
    # 6 -- inst, 7 -- proc, 8 -- res, 9 -- template-participant

class Event_structure_relations(db.Model):
    element_id = db.Column(db.Integer, nullable=False)
    type_of_element = db.Column(db.Text, unique=False, nullable=False)
    target_id = db.Column(db.Integer, unique=False, primary_key=True)
    type = db.Column(db.Integer, unique=False, nullable=False) #1 -- belonging to a template
