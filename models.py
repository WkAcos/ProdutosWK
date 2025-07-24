from db import db
from flask_login import UserMixin
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy import JSON, PickleType


class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(90), unique=True)
    senha = db.Column(db.String())
    is_admin = db.Column(db.Boolean, default=False)

    # Campo que você já usa para armazenar percentuais personalizados
    percentuais = db.Column(MutableList.as_mutable(JSON), default=[])
    descricao = db.Column(db.String(255))
