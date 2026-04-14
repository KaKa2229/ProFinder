from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

# Framework: Flask / Jinja 2
app = Flask(__name__, template_folder='app/template', static_folder='app/static')

# CONFIGURAÇÃO DO BANCO DE DADOS 
basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'profinder.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(11), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return f'<Usuario {self.nome}>'

class Profissional(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(11), unique=True, nullable=False) 
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(128), nullable=False)
    profissao = db.Column(db.String(50), nullable=False)
    bairro = db.Column(db.String(50), nullable=False)
    avaliacao = db.Column(db.Float, default=5.0) 
    foto = db.Column(db.String(255), nullable=False) 
    def __repr__(self):
        return f'<Profissional {self.nome} - {self.profissao}>'

with app.app_context():
    db.create_all()

# ROTAS DAS PÁGINAS 
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')
 
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        print(f"--- NOVA TENTATIVA DE LOGIN ---")
        print(f"Email recebido: {email}")
        #Verificação de login via BD
        
    return render_template('login.html')

# Cadastro de Cliente Padrão
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro_cliente():
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        print(f"--- NOVO CADASTRO DE CLIENTE: {nome} | {email} ---")
        # Futuramente: Salvar no Banco de Dados
        
    return render_template('cadastro.html')

# Cadastro de Profissional
@app.route('/cadastro-profissional', methods=['GET', 'POST'])
def cadastro_profissional():
    if request.method == 'POST':
        nome = request.form.get('nome')
        profissao = request.form.get('profissao')
        print(f"--- NOVO CADASTRO DE PROFISSIONAL: {nome} | {profissao} ---")
        # Futuramente: Salvar no Banco de Dados
        
    return render_template('cadastroProfissional.html')

@app.route('/ajuda')
def ajuda():
    return render_template('ajuda.html')


@app.route('/faq')
def faq():
    return render_template('faq.html')


@app.route('/busca-servicos')
def busca_servicos():
    return render_template('busca_servicos.html')

@app.route('/busca-profissionais/<categoria>')
def busca_profissionais(categoria):
    profissionais_encontrados = Profissional.query.filter_by(profissao=categoria).all()
    
    return render_template('busca_profissionais.html', profissionais=profissionais_encontrados, categoria=categoria)

if __name__ == '__main__':
    app.run(debug=True)