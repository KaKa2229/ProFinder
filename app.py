from flask import Flask, render_template, request, redirect, url_for, flash
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, login_required, logout_user, current_user 
import os
import time
from werkzeug.utils import secure_filename

# Importamos a base de dados e os modelos do ficheiro models.py
from models import db, Usuario, Profissional, Portfolio

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.config['SECRET_KEY'] = 'uma_chave_secreta_muito_louca_e_segura_profinder' 

# CONFIGURAÇÃO DA BASE DE DADOS REAL
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'profinder.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Pasta onde as fotos serão guardadas
app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'img', 'perfil')

# Inicializa as extensões
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' 
login_manager.login_message = "Por favor, inicie sessão para aceder a esta página."
login_manager.login_message_category = "info"

@login_manager.user_loader
def load_user(user_id):
    # Todos os utilizadores (clientes ou profissionais) estão na tabela Usuario
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

@app.route('/busca-profissionais')
@app.route('/busca-profissionais/<categoria>')
def busca_profissionais(categoria=None):
    if categoria:
        profissionais_encontrados = Profissional.query.filter_by(profissao=categoria).all()
    else:
        profissionais_encontrados = Profissional.query.all()
        categoria = "Todos os Profissionais"
        
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

        # Verificamos apenas a tabela Usuario
        email_existe = Usuario.query.filter_by(email=email).first()
        cpf_existe = Usuario.query.filter_by(cpf=cpf).first()

        if email_existe or cpf_existe:
            flash("Este E-mail ou CPF já está registado no sistema.", "danger")
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
        telefone = request.form.get('telefone') # CAMPO DE TELEFONE
        senha = request.form.get('senha')
        confirma_senha = request.form.get('confirma_senha')
        profissao = request.form.get('profissao')
        regiao = request.form.get('regiao')
        descricao = request.form.get('descricao')

        cpf = cpf_raw.replace('.', '').replace('-', '') if cpf_raw else None

        if len(cpf) != 11:
            flash("O CPF deve conter exatamente 11 dígitos!", "danger")
            return render_template('cadastroProfissional.html', nome=nome, cpf=cpf_raw, email=email, telefone=telefone, profissao=profissao, regiao=regiao, descricao=descricao)

        if senha != confirma_senha:
            flash("As palavras-passe não coincidem. Tente novamente!", "danger")
            return render_template('cadastroProfissional.html', nome=nome, cpf=cpf_raw, email=email, telefone=telefone, profissao=profissao, regiao=regiao, descricao=descricao)

        email_existe = Usuario.query.filter_by(email=email).first()
        cpf_existe = Usuario.query.filter_by(cpf=cpf).first()

        if email_existe or cpf_existe:
            flash("Este E-mail ou CPF já está registado no sistema.", "danger")
            return render_template('cadastroProfissional.html', nome=nome, cpf=cpf_raw, email=email, telefone=telefone, profissao=profissao, regiao=regiao, descricao=descricao)

        senha_criptografada = bcrypt.generate_password_hash(senha).decode('utf-8')

        # UPLOAD DE FOTO NO REGISTO
        foto_path = '/static/img/default-avatar.png'
        if 'foto' in request.files:
            foto_file = request.files['foto']
            if foto_file and foto_file.filename != '':
                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    os.makedirs(app.config['UPLOAD_FOLDER'])
                
                timestamp = int(time.time())
                nome_seguro = secure_filename(f"novo_{timestamp}_{foto_file.filename}")
                caminho_salvar = os.path.join(app.config['UPLOAD_FOLDER'], nome_seguro)
                
                foto_file.save(caminho_salvar)
                foto_path = f"/static/img/perfil/{nome_seguro}"

        # 1. Criar o Utilizador base
        novo_usuario = Usuario(nome=nome, cpf=cpf, email=email, senha=senha_criptografada, tipo_usuario='profissional', foto=foto_path)
        db.session.add(novo_usuario)
        db.session.commit() # Grava para gerar o ID

        # 2. Criar o Perfil Profissional ligado ao Utilizador e GUARDAR O TELEFONE/DESCRIÇÃO
        novo_profissional = Profissional(
            usuario_id=novo_usuario.id,
            telefone=telefone, 
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
        
        # A verificação é feita apenas numa única tabela
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
# GESTÃO DE PERFIL E UPLOAD DE FOTOS
# ==========================================

@app.route('/meu-perfil', methods=['GET', 'POST'])
@login_required
def meu_perfil():
    if request.method == 'POST':
        # Busca o utilizador real na base de dados para garantir que vai gravar
        usuario = Usuario.query.get(current_user.id)
        
        usuario.nome = request.form.get('nome')
        usuario.email = request.form.get('email')

        # Lógica de Upload da Foto com Timestamp (Anti-Cache) e "foto" como chave
        if 'foto' in request.files:
            foto_file = request.files['foto']
            
            if foto_file and foto_file.filename != '':
                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    os.makedirs(app.config['UPLOAD_FOLDER'])
                
                timestamp = int(time.time())
                nome_seguro = secure_filename(f"user_{usuario.id}_{timestamp}_{foto_file.filename}")
                caminho_salvar = os.path.join(app.config['UPLOAD_FOLDER'], nome_seguro)
                
                foto_file.save(caminho_salvar)
                usuario.foto = f"/static/img/perfil/{nome_seguro}"

        # Se for Profissional, atualizamos os dados de trabalho na tabela correspondente
        if usuario.tipo_usuario == 'profissional':
            if usuario.perfil_profissional:
                usuario.perfil_profissional.telefone = request.form.get('telefone')
                usuario.perfil_profissional.profissao = request.form.get('profissao')
                usuario.perfil_profissional.bairro = request.form.get('regiao')
                usuario.perfil_profissional.descricao = request.form.get('descricao')
            else:
                # Segurança extra: se o perfil profissional não existir, cria um novo
                novo_perfil = Profissional(
                    usuario_id=usuario.id,
                    telefone=request.form.get('telefone'),
                    profissao=request.form.get('profissao'),
                    bairro=request.form.get('regiao'),
                    descricao=request.form.get('descricao')
                )
                db.session.add(novo_perfil)

        # Lógica de atualização de palavra-passe
        senha_atual = request.form.get('senha_atual')
        nova_senha = request.form.get('nova_senha')
        confirma_senha = request.form.get('confirma_senha')

        if nova_senha or confirma_senha:
            if not senha_atual:
                flash("Para alterar a sua palavra-passe, deve introduzir a palavra-passe atual.", "danger")
                return redirect(url_for('meu_perfil'))

            if bcrypt.check_password_hash(usuario.senha, senha_atual):
                if nova_senha == confirma_senha:
                    if len(nova_senha) < 6:
                        flash("A nova palavra-passe deve ter pelo menos 6 caracteres.", "danger")
                        return redirect(url_for('meu_perfil'))
                    
                    usuario.senha = bcrypt.generate_password_hash(nova_senha).decode('utf-8')
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