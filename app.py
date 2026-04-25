from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')

# Config flask
app.config['SECRET_KEY'] = 'uma_chave_secreta_muito_louca_e_segura_profinder'

# Config bd  
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'profinder.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Extensões
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Por favor, faça login para acessar esta página."
login_manager.login_message_category = "info"

# --- MODELOS DA BASE DE DADOS ---
class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(11), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(128), nullable=False)
    tipo_conta = db.Column(db.String(20), default='cliente')

class Profissional(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(11), unique=True, nullable=False) 
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(128), nullable=False)
    profissao = db.Column(db.String(50), nullable=False)
    bairro = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.Text, nullable=True) # Nova coluna adicionada!
    avaliacao = db.Column(db.Float, default=5.0) 
    foto = db.Column(db.String(255), default='https://cdn-icons-png.flaticon.com/512/3135/3135715.png')
    tipo_conta = db.Column(db.String(20), default='profissional')

@login_manager.user_loader
def load_user(user_id):
    user = Usuario.query.get(int(user_id))
    if user:
        return user
    return Profissional.query.get(int(user_id))

with app.app_context():
    db.create_all()

# ==========================================
# ROTAS DE NAVEGAÇÃO BÁSICAS
# ==========================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

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

@app.route('/perfil/<int:id>')
def perfil(id):
    profissional_selecionado = Profissional.query.get_or_404(id)
    return render_template('perfil.html', profissional=profissional_selecionado)


# ==========================================
# ROTAS DE AUTENTICAÇÃO E REGISTO
# ==========================================

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro_cliente():
    if request.method == 'POST':
        nome = request.form.get('nome')
        cpf_raw = request.form.get('cpf')
        email = request.form.get('email')
        senha = request.form.get('senha')
        confirma_senha = request.form.get('confirma_senha')

        cpf = cpf_raw.replace('.', '').replace('-', '') if cpf_raw else None

        if len(cpf) != 11:
            flash("O CPF deve conter exatamente 11 dígitos!", "danger")
            return render_template('cadastro.html', nome=nome, cpf=cpf_raw, email=email)

        if senha != confirma_senha:
            flash("As palavras-passe não coincidem. Tente novamente!", "danger")
            return render_template('cadastro.html', nome=nome, cpf=cpf_raw, email=email)

        email_existe = Usuario.query.filter_by(email=email).first() or Profissional.query.filter_by(email=email).first()
        cpf_existe = Usuario.query.filter_by(cpf=cpf).first() or Profissional.query.filter_by(cpf=cpf).first()

        if email_existe or cpf_existe:
            flash("Este E-mail ou CPF já estão registados no sistema.", "danger")
            return render_template('cadastro.html', nome=nome, cpf=cpf_raw, email=email)

        senha_criptografada = bcrypt.generate_password_hash(senha).decode('utf-8')
        novo_usuario = Usuario(nome=nome, cpf=cpf, email=email, senha=senha_criptografada)
        
        db.session.add(novo_usuario)
        db.session.commit()
        
        login_user(novo_usuario)
        return redirect(url_for('index'))
        
    return render_template('cadastro.html')

@app.route('/cadastro-profissional', methods=['GET', 'POST'])
def cadastro_profissional():
    if request.method == 'POST':
        nome = request.form.get('nome')
        cpf_raw = request.form.get('cpf')
        email = request.form.get('email')
        senha = request.form.get('senha')
        confirma_senha = request.form.get('confirma_senha')
        profissao = request.form.get('profissao')
        regiao = request.form.get('regiao')
        descricao = request.form.get('descricao')

        cpf = cpf_raw.replace('.', '').replace('-', '') if cpf_raw else None

        if len(cpf) != 11:
            flash("O CPF deve conter exatamente 11 dígitos!", "danger")
            return render_template('cadastroProfissional.html', nome=nome, cpf=cpf_raw, email=email, profissao=profissao, regiao=regiao, descricao=descricao)

        if senha != confirma_senha:
            flash("As palavras-passe não coincidem. Tente novamente!", "danger")
            return render_template('cadastroProfissional.html', nome=nome, cpf=cpf_raw, email=email, profissao=profissao, regiao=regiao, descricao=descricao)

        email_existe = Usuario.query.filter_by(email=email).first() or Profissional.query.filter_by(email=email).first()
        cpf_existe = Usuario.query.filter_by(cpf=cpf).first() or Profissional.query.filter_by(cpf=cpf).first()

        if email_existe or cpf_existe:
            flash("Este E-mail ou CPF já estão registados no sistema.", "danger")
            return render_template('cadastroProfissional.html', nome=nome, cpf=cpf_raw, email=email, profissao=profissao, regiao=regiao, descricao=descricao)

        senha_criptografada = bcrypt.generate_password_hash(senha).decode('utf-8')

        novo_profissional = Profissional(
            nome=nome, cpf=cpf, email=email, senha=senha_criptografada, 
            profissao=profissao, bairro=regiao, descricao=descricao
        )
        db.session.add(novo_profissional)
        db.session.commit()

        login_user(novo_profissional)
        return redirect(url_for('index'))
        
    return render_template('cadastroProfissional.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        usuario = Usuario.query.filter_by(email=email).first()
        profissional = Profissional.query.filter_by(email=email).first()
        user = usuario or profissional

        if user and bcrypt.check_password_hash(user.senha, senha):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash("E-mail ou palavra-passe incorretos. Verifique os seus dados.", "danger")
            return redirect(url_for('login'))
        
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# ==========================================
# ROTA: MEU PERFIL (Dinâmica para Cliente ou Profissional)
# ==========================================

@app.route('/meu-perfil', methods=['GET', 'POST'])
@login_required
def meu_perfil():
    if request.method == 'POST':
        # Recolhe os dados básicos enviados pelo formulário
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha_atual = request.form.get('senha_atual')
        nova_senha = request.form.get('nova_senha')
        confirma_senha = request.form.get('confirma_senha')

        # Atualiza os dados básicos na memória
        current_user.nome = nome
        current_user.email = email

        # Se o utilizador for Profissional, atualiza os campos extra
        if current_user.tipo_conta == 'profissional':
            current_user.profissao = request.form.get('profissao')
            current_user.bairro = request.form.get('regiao')
            current_user.descricao = request.form.get('descricao')

        # Lógica de atualização de segurança (Palavra-passe)
        if nova_senha or confirma_senha:
            if not senha_atual:
                flash("Para alterar a sua palavra-passe, deve introduzir a palavra-passe atual.", "danger")
                return redirect(url_for('meu_perfil'))

            # Verifica se a senha atual está correta na base de dados
            if bcrypt.check_password_hash(current_user.senha, senha_atual):
                if nova_senha == confirma_senha:
                    if len(nova_senha) < 6:
                        flash("A nova palavra-passe deve ter pelo menos 6 caracteres.", "danger")
                        return redirect(url_for('meu_perfil'))
                    
                    # Encripta a nova senha e substitui
                    current_user.senha = bcrypt.generate_password_hash(nova_senha).decode('utf-8')
                    flash("Perfil e palavra-passe atualizados com sucesso!", "success")
                else:
                    flash("A nova palavra-passe e a confirmação não coincidem.", "danger")
                    return redirect(url_for('meu_perfil'))
            else:
                flash("A palavra-passe atual está incorreta. A sua alteração não foi guardada.", "danger")
                return redirect(url_for('meu_perfil'))
        else:
            flash("O seu perfil foi atualizado com sucesso!", "success")

        # Guarda definitivamente as alterações e recarrega a página
        db.session.commit()
        return redirect(url_for('meu_perfil'))

    # Se for apenas um "GET" (entrar na página), exibe o HTML correto consoante o tipo de conta
    if current_user.tipo_conta == 'profissional':
        return render_template('meu_perfil_profissional.html')
    else:
        return render_template('meu_perfil_cliente.html')

if __name__ == '__main__':
    app.run(debug=True)