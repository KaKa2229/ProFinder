from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import time
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')

# Config flask
app.config['SECRET_KEY'] = 'uma_chave_secreta_muito_louca_e_segura_profinder'

# Config bd  
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'profinder.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuração de pastas de Upload
UPLOAD_PERFIL = os.path.join(app.static_folder, 'img', 'perfil')
UPLOAD_PORTFOLIO = os.path.join(app.static_folder, 'img', 'portfolio')
os.makedirs(UPLOAD_PERFIL, exist_ok=True)
os.makedirs(UPLOAD_PORTFOLIO, exist_ok=True)

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
    foto = db.Column(db.String(255), default='/static/img/default-avatar.png')

    def get_id(self):
        return f"usuario_{self.id}"

class Profissional(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(11), unique=True, nullable=False) 
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(128), nullable=False)
    telefone = db.Column(db.String(20), nullable=True) 
    profissao = db.Column(db.String(50), nullable=False)
    bairro = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.Text, nullable=True) 
    avaliacao = db.Column(db.Float, default=5.0) 
    foto = db.Column(db.String(255), default='https://cdn-icons-png.flaticon.com/512/3135/3135715.png')
    tipo_conta = db.Column(db.String(20), default='profissional')
    
    # Relação com os trabalhos (Portfólio)
    trabalhos = db.relationship('Portfolio', backref='profissional', lazy=True, cascade='all, delete-orphan')

    def get_id(self):
        return f"profissional_{self.id}"

class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    profissional_id = db.Column(db.Integer, db.ForeignKey('profissional.id'), nullable=False)
    titulo = db.Column(db.String(100), nullable=False)
    data_conclusao = db.Column(db.String(50), nullable=True)
    imagem_url = db.Column(db.String(255), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    try:
        # Agora divide o prefixo do número real (Ex: "usuario_1" -> tipo="usuario", real_id=1)
        tipo, real_id = user_id.split('_')
        if tipo == 'usuario':
            return Usuario.query.get(int(real_id))
        elif tipo == 'profissional':
            return Profissional.query.get(int(real_id))
    except ValueError:
        # Fallback de segurança para sessões antigas que só tinham o número
        user = Usuario.query.get(int(user_id))
        if user:
            return user
        return Profissional.query.get(int(user_id))
    return None

with app.app_context():
    db.create_all()

# ROTAS DE NAVEGAÇÃO BÁSICAS

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
    # Buscamos também os trabalhos deste profissional
    trabalhos_portfolio = Portfolio.query.filter_by(profissional_id=id).all()
    return render_template('perfil.html', profissional=profissional_selecionado, portfolio=trabalhos_portfolio)


# ROTAS DE AUTENTICAÇÃO E REGISTO

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
        telefone = request.form.get('telefone')
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

        email_existe = Usuario.query.filter_by(email=email).first() or Profissional.query.filter_by(email=email).first()
        cpf_existe = Usuario.query.filter_by(cpf=cpf).first() or Profissional.query.filter_by(cpf=cpf).first()

        if email_existe or cpf_existe:
            flash("Este E-mail ou CPF já estão registados no sistema.", "danger")
            return render_template('cadastroProfissional.html', nome=nome, cpf=cpf_raw, email=email, telefone=telefone, profissao=profissao, regiao=regiao, descricao=descricao)

        senha_criptografada = bcrypt.generate_password_hash(senha).decode('utf-8')

        novo_profissional = Profissional(
            nome=nome, cpf=cpf, email=email, senha=senha_criptografada, 
            telefone=telefone, profissao=profissao, bairro=regiao, descricao=descricao
        )
        
        # 1. Primeiro guardamos no banco para gerar um ID para este profissional
        db.session.add(novo_profissional)
        db.session.commit()

        # 2. AGORA SIM: Se ele enviou uma foto no momento do cadastro, nós guardamos!
        if 'foto' in request.files:
            foto_file = request.files['foto']
            if foto_file and foto_file.filename != '':
                timestamp = int(time.time())
                # Usamos o ID recém-criado para nomear o ficheiro de forma segura
                nome_seguro = secure_filename(f"user_{novo_profissional.id}_{timestamp}_{foto_file.filename}")
                caminho_salvar = os.path.join(UPLOAD_PERFIL, nome_seguro)
                
                # Salva a imagem na pasta estática
                foto_file.save(caminho_salvar)
                
                # Atualiza a foto do profissional e faz um segundo commit
                novo_profissional.foto = f"/static/img/perfil/{nome_seguro}"
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


# ROTA: MEU PERFIL (Dinâmica para Cliente ou Profissional)

@app.route('/meu-perfil', methods=['GET', 'POST'])
@login_required
def meu_perfil():
    if request.method == 'POST':
        # Busca o usuário real no banco para garantir que vai salvar
        if current_user.tipo_conta == 'profissional':
            db_user = Profissional.query.get(current_user.id)
        else:
            db_user = Usuario.query.get(current_user.id)

        # Lógica de Upload de Foto Principal
        if 'foto' in request.files:
            foto_file = request.files['foto']
            if foto_file and foto_file.filename != '':
                timestamp = int(time.time())
                nome_seguro = secure_filename(f"user_{db_user.id}_{timestamp}_{foto_file.filename}")
                caminho_salvar = os.path.join(UPLOAD_PERFIL, nome_seguro)
                foto_file.save(caminho_salvar)
                db_user.foto = f"/static/img/perfil/{nome_seguro}"

        # Atualiza os dados básicos
        db_user.nome = request.form.get('nome')
        db_user.email = request.form.get('email')

        # Se o utilizador for Profissional, atualiza os campos extra
        if db_user.tipo_conta == 'profissional':
            db_user.profissao = request.form.get('profissao')
            db_user.bairro = request.form.get('regiao')
            db_user.descricao = request.form.get('descricao')
            db_user.telefone = request.form.get('telefone')

        senha_atual = request.form.get('senha_atual')
        nova_senha = request.form.get('nova_senha')
        confirma_senha = request.form.get('confirma_senha')

        # Lógica de atualização de segurança (Palavra-passe)
        if nova_senha or confirma_senha:
            if not senha_atual:
                flash("Para alterar a sua palavra-passe, deve introduzir a palavra-passe atual.", "danger")
                return redirect(url_for('meu_perfil'))

            # Verifica se a senha atual está correta na base de dados
            if bcrypt.check_password_hash(db_user.senha, senha_atual):
                if nova_senha == confirma_senha:
                    if len(nova_senha) < 6:
                        flash("A nova palavra-passe deve ter pelo menos 6 caracteres.", "danger")
                        return redirect(url_for('meu_perfil'))
                    
                    # Encripta a nova senha e substitui
                    db_user.senha = bcrypt.generate_password_hash(nova_senha).decode('utf-8')
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
        trabalhos_portfolio = Portfolio.query.filter_by(profissional_id=current_user.id).all()
        return render_template('meu_perfil_profissional.html', trabalhos=trabalhos_portfolio)
    else:
        return render_template('meu_perfil_cliente.html')

# ==========================================
# ROTAS DO PORTFÓLIO (FASE 2)
# ==========================================

@app.route('/adicionar-portfolio', methods=['POST'])
@login_required
def adicionar_portfolio():
    if current_user.tipo_conta != 'profissional':
        return redirect(url_for('index'))

    titulo = request.form.get('titulo')
    data_conclusao = request.form.get('data_conclusao')
    
    if 'foto_trabalho' in request.files:
        foto_file = request.files['foto_trabalho']
        if foto_file and foto_file.filename != '':
            timestamp = int(time.time())
            nome_seguro = secure_filename(f"work_{current_user.id}_{timestamp}_{foto_file.filename}")
            caminho_salvar = os.path.join(UPLOAD_PORTFOLIO, nome_seguro)
            
            foto_file.save(caminho_salvar)
            foto_url = f"/static/img/portfolio/{nome_seguro}"
            
            novo_trabalho = Portfolio(
                profissional_id=current_user.id,
                titulo=titulo,
                data_conclusao=data_conclusao,
                imagem_url=foto_url
            )
            db.session.add(novo_trabalho)
            db.session.commit()
            flash("Trabalho adicionado ao seu portfólio com sucesso!", "success")
        else:
            flash("Erro ao enviar a imagem do trabalho.", "danger")
            
    return redirect(url_for('meu_perfil'))

@app.route('/excluir-portfolio/<int:id>', methods=['POST'])
@login_required
def excluir_portfolio(id):
    if current_user.tipo_conta != 'profissional':
        return redirect(url_for('index'))
        
    trabalho = Portfolio.query.get_or_404(id)
    
    # Segurança: Garante que o profissional só pode apagar os seus próprios trabalhos
    if trabalho.profissional_id == current_user.id:
        db.session.delete(trabalho)
        db.session.commit()
        flash("Trabalho removido do seu portfólio.", "success")
    else:
        flash("Não tem permissão para excluir este trabalho.", "danger")
        
    return redirect(url_for('meu_perfil'))

if __name__ == '__main__':
    app.run(debug=True)