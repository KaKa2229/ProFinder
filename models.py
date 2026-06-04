from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    tipo_usuario = db.Column(db.String(20), nullable=False, default='cliente')
    # A foto de perfil fica no utilizador para que tanto clientes como profissionais a possam ter
    foto = db.Column(db.String(255), nullable=True, default='/static/img/default-avatar.png')
    
    perfil_profissional = db.relationship('Profissional', backref='usuario', uselist=False, cascade='all, delete-orphan')

class Profissional(db.Model):
    __tablename__ = 'profissionais'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    # Campo Telefone devidamente estruturado!
    telefone = db.Column(db.String(20), nullable=False, default='')
    
    profissao = db.Column(db.String(100), nullable=False)
    bairro = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    avaliacao = db.Column(db.Float, default=0.0)
    
    portfolio = db.relationship('Portfolio', backref='profissional', lazy=True, cascade='all, delete-orphan')

class Portfolio(db.Model):
    __tablename__ = 'portfolio'
    
    id = db.Column(db.Integer, primary_key=True)
    profissional_id = db.Column(db.Integer, db.ForeignKey('profissionais.id'), nullable=False)
    
    titulo = db.Column(db.String(100), nullable=False)
    data_conclusao = db.Column(db.String(50), nullable=True)
    imagem_url = db.Column(db.String(255), nullable=False)