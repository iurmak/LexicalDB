from flask import Flask
from datetime import timedelta

app = Flask(__name__)
app.secret_key = 'afaqw2r2o872211@310-))(1$$5'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lex_typ.db'
app.config['MAIL_SERVER'] = 'smtp.beget.com'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USERNAME'] = 'notifications@pamiri.online'
app.config['MAIL_DEFAULT_SENDER'] = ('Pamir Languages', 'notifications@pamiri.online')
app.config['MAIL_PASSWORD'] = '9iQM32&n'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)

"""
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'pamir.languages@gmail.com'
app.config['MAIL_DEFAULT_SENDER'] = 'pamir.languages@gmail.com'
app.config['MAIL_PASSWORD'] = 'mufhumrmyfhkzfoy'
"""
import LexicalDB.profile, LexicalDB.login, LexicalDB.about, LexicalDB.templates

if __name__ == "__main__":
    app.run(debug=True)