from flask import Flask, render_template, request, redirect, url_for, flash
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import os

# Importamos a base de dados e os modelos do ficheiro models.py
from models import db, Usuario, Profissional, Portfolio

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.config['SECRET_KEY'] = 'secretkey123' # Necessário para as sessões

# CONFIGURAÇÃO DO BANCO DE DADOS REAL
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'profinder.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializa as extensões
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' # Se um utilizador não logado tentar acessar área restrita, vai para 'login'
login_manager.login_message = "Por favor, faça login para acessar esta página."
login_manager.login_message_category = "info"

@login_manager.user_loader
def load_user(user_id):
    # Agora todos os utilizadores (clientes ou profissionais) estão na tabela Usuario
    return Usuario.query.get(int(user_id))

# Criação automática das tabelas antes da primeira requisição (se não existirem)
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

        # Na estrutura relacional, verificamos apenas a tabela Usuario
        email_existe = Usuario.query.filter_by(email=email).first()
        cpf_existe = Usuario.query.filter_by(cpf=cpf).first()

        if email_existe or cpf_existe:
            flash("Este E-mail ou CPF já estão registados no sistema.", "danger")
            return render_template('cadastro.html', nome=nome, cpf=cpf_raw, email=email)

        senha_criptografada = bcrypt.generate_password_hash(senha).decode('utf-8')
        
        # Cria o Cliente
        novo_usuario = Usuario(nome=nome, cpf=cpf, email=email, senha=senha_criptografada, tipo_usuario='cliente')
        
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

        email_existe = Usuario.query.filter_by(email=email).first()
        cpf_existe = Usuario.query.filter_by(cpf=cpf).first()

        if email_existe or cpf_existe:
            flash("Este E-mail ou CPF já estão registados no sistema.", "danger")
            return render_template('cadastroProfissional.html', nome=nome, cpf=cpf_raw, email=email, profissao=profissao, regiao=regiao, descricao=descricao)

        senha_criptografada = bcrypt.generate_password_hash(senha).decode('utf-8')

        # 1. Criar o Usuário base
        novo_usuario = Usuario(nome=nome, cpf=cpf, email=email, senha=senha_criptografada, tipo_usuario='profissional')
        db.session.add(novo_usuario)
        db.session.commit() # Grava para gerar o ID

        # 2. Criar o Perfil Profissional ligado ao Usuário
        novo_profissional = Profissional(
            usuario_id=novo_usuario.id,
            profissao=profissao, 
            bairro=regiao, 
            descricao=descricao
        )
        db.session.add(novo_profissional)
        db.session.commit()

        login_user(novo_usuario)
        return redirect(url_for('index'))
        
    return render_template('cadastroProfissional.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        # Agora a verificação é feita apenas numa única tabela
        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and bcrypt.check_password_hash(usuario.senha, senha):
            login_user(usuario)
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
# GESTÃO DE PERFIL
# ==========================================

@app.route('/meu-perfil', methods=['GET', 'POST'])
@login_required
def meu_perfil():
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha_atual = request.form.get('senha_atual')
        nova_senha = request.form.get('nova_senha')
        confirma_senha = request.form.get('confirma_senha')

        current_user.nome = nome
        current_user.email = email

        # Se for Profissional, atualizamos os dados na tabela Profissional
        if current_user.tipo_usuario == 'profissional' and current_user.perfil_profissional:
            current_user.perfil_profissional.profissao = request.form.get('profissao')
            current_user.perfil_profissional.bairro = request.form.get('regiao')
            current_user.perfil_profissional.descricao = request.form.get('descricao')

        # Lógica de atualização de senha
        if nova_senha or confirma_senha:
            if not senha_atual:
                flash("Para alterar a sua palavra-passe, deve introduzir a palavra-passe atual.", "danger")
                return redirect(url_for('meu_perfil'))

            if bcrypt.check_password_hash(current_user.senha, senha_atual):
                if nova_senha == confirma_senha:
                    if len(nova_senha) < 6:
                        flash("A nova palavra-passe deve ter pelo menos 6 caracteres.", "danger")
                        return redirect(url_for('meu_perfil'))
                    
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

        db.session.commit()
        return redirect(url_for('meu_perfil'))

    # Renderiza consoante o tipo da conta
    if current_user.tipo_usuario == 'profissional':
        return render_template('meu_perfil_profissional.html')
    else:
        return render_template('meu_perfil_cliente.html')

if __name__ == '__main__':
    app.run(debug=True)