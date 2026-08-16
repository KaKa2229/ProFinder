from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
from datetime import datetime
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader

load_dotenv()
app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')


# Config bd  
basedir = os.path.abspath(os.path.dirname(__file__))
uri = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'profinder.db'))

# Pequeno ajuste necessário porque o Render envia o link como "postgres://", mas o SQLAlchemy moderno exige "postgresql://"
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Config Cloudinary
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
)

def upload_to_cloudinary(file, folder="profinder"):
    """Faz upload de um arquivo para o Cloudinary e retorna a URL segura."""
    result = cloudinary.uploader.upload(file, folder=folder)
    return result["secure_url"]

# Extensões
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Por favor, inicie sessão para aceder a esta página."
login_manager.login_message_category = "info"

# MODELOS DA BASE DE DADOS

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
    
    # Colunas de Localização
    cidade = db.Column(db.String(100), nullable=False)
    regiao = db.Column(db.String(100), nullable=False)
    
    # Endereço Fixo
    endereco_fixo = db.Column(db.String(255), nullable=True)
    
    descricao = db.Column(db.Text, nullable=True) 
    avaliacao = db.Column(db.Float, default=5.0) 
    foto = db.Column(db.String(255), default='https://cdn-icons-png.flaticon.com/512/3135/3135715.png')
    tipo_conta = db.Column(db.String(20), default='profissional')
    verificado = db.Column(db.Boolean, default=False)
    
    # Relações
    trabalhos = db.relationship('Portfolio', backref='profissional', lazy=True, cascade='all, delete-orphan')
    solicitacoes_recebidas = db.relationship('SolicitacaoServico', backref='profissional_solicitado', lazy=True, cascade='all, delete-orphan')

    def get_id(self):
        return f"profissional_{self.id}"

class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    profissional_id = db.Column(db.Integer, db.ForeignKey('profissional.id'), nullable=False)
    titulo = db.Column(db.String(100), nullable=False)
    data_conclusao = db.Column(db.String(50), nullable=True)
    imagem_url = db.Column(db.String(255), nullable=False)

class SolicitacaoServico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    profissional_id = db.Column(db.Integer, db.ForeignKey('profissional.id'), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    data_solicitacao = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pendente')
    avaliado = db.Column(db.Boolean, default=False)
    cep = db.Column(db.String(9), nullable=True)
    endereco = db.Column(db.String(255), nullable=True)
    prazo_desejado = db.Column(db.String(50), nullable=True)
    
    cliente = db.relationship('Usuario', backref='minhas_solicitacoes', lazy=True)

class Avaliacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    profissional_id = db.Column(db.Integer, db.ForeignKey('profissional.id'), nullable=False)
    nota = db.Column(db.Integer, nullable=False) 
    comentario = db.Column(db.Text, nullable=True)
    data_avaliacao = db.Column(db.DateTime, default=datetime.utcnow)

    cliente = db.relationship('Usuario', backref='avaliacoes_dadas', lazy=True)
    profissional = db.relationship('Profissional', backref='avaliacoes_recebidas', lazy=True)

class Favorito(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    profissional_id = db.Column(db.Integer, db.ForeignKey('profissional.id'), nullable=False)
    data_favoritado = db.Column(db.DateTime, default=datetime.utcnow)

    cliente = db.relationship('Usuario', backref='favoritos', lazy=True)
    profissional = db.relationship('Profissional', backref='favoritado_por', lazy=True)

@login_manager.user_loader
def load_user(user_id):
    try:
        tipo, real_id = user_id.split('_')
        if tipo == 'usuario':
            return Usuario.query.get(int(real_id))
        elif tipo == 'profissional':
            return Profissional.query.get(int(real_id))
    except ValueError:
        user = Usuario.query.get(int(user_id))
        if user:
            return user
        return Profissional.query.get(int(user_id))
    return None

with app.app_context():
    db.create_all()
    # Migration: adicionar colunas novas em tabelas existentes (seguro para rodar múltiplas vezes)
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)
    
    # Colunas novas no Profissional
    colunas_profissional = [col['name'] for col in inspector.get_columns('profissional')]
    if 'verificado' not in colunas_profissional:
        db.session.execute(text('ALTER TABLE profissional ADD COLUMN verificado BOOLEAN DEFAULT 0'))
        db.session.commit()
    
    # Colunas novas no SolicitacaoServico
    colunas_solicitacao = [col['name'] for col in inspector.get_columns('solicitacao_servico')]
    if 'cep' not in colunas_solicitacao:
        db.session.execute(text('ALTER TABLE solicitacao_servico ADD COLUMN cep VARCHAR(9)'))
        db.session.execute(text('ALTER TABLE solicitacao_servico ADD COLUMN endereco VARCHAR(255)'))
        db.session.execute(text("ALTER TABLE solicitacao_servico ADD COLUMN prazo_desejado VARCHAR(50)"))
        db.session.commit()

# ROTAS DE NAVEGAÇÃO BÁSICAS E PWA
from flask import send_from_directory

@app.route('/manifest.json')
def manifest():
    return send_from_directory(app.static_folder, 'manifest.json', mimetype='application/json')

@app.route('/service-worker.js')
def service_worker():
    return send_from_directory(app.static_folder, 'service-worker.js', mimetype='application/javascript')

@app.route('/offline')
def offline():
    return render_template('offline.html')

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
    ids_favoritos = []
    if current_user.is_authenticated and current_user.tipo_conta == 'cliente':
        ids_favoritos = [f.profissional_id for f in Favorito.query.filter_by(cliente_id=current_user.id).all()]
    return render_template('busca_profissionais.html', profissionais=profissionais_encontrados, categoria=categoria, ids_favoritos=ids_favoritos)

@app.route('/perfil/<int:id>')
def perfil(id):
    profissional_selecionado = Profissional.query.get_or_404(id)
    trabalhos_portfolio = Portfolio.query.filter_by(profissional_id=id).all()
    avaliacoes = Avaliacao.query.filter_by(profissional_id=id).order_by(Avaliacao.data_avaliacao.desc()).all()
    is_favorito = False
    if current_user.is_authenticated and current_user.tipo_conta == 'cliente':
        is_favorito = Favorito.query.filter_by(cliente_id=current_user.id, profissional_id=id).first() is not None
    return render_template('perfil.html', profissional=profissional_selecionado, portfolio=trabalhos_portfolio, avaliacoes=avaliacoes, is_favorito=is_favorito)

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
        
        cidade = request.form.get('cidade')
        regiao = request.form.get('regiao')
        endereco_fixo = request.form.get('endereco_fixo')
        
        descricao = request.form.get('descricao')

        cpf = cpf_raw.replace('.', '').replace('-', '') if cpf_raw else None

        if len(cpf) != 11:
            flash("O CPF deve conter exatamente 11 dígitos!", "danger")
            return render_template('cadastroProfissional.html', nome=nome, cpf=cpf_raw, email=email, telefone=telefone, profissao=profissao, cidade=cidade, regiao=regiao, endereco_fixo=endereco_fixo, descricao=descricao)

        if senha != confirma_senha:
            flash("As palavras-passe não coincidem. Tente novamente!", "danger")
            return render_template('cadastroProfissional.html', nome=nome, cpf=cpf_raw, email=email, telefone=telefone, profissao=profissao, cidade=cidade, regiao=regiao, endereco_fixo=endereco_fixo, descricao=descricao)

        email_existe = Usuario.query.filter_by(email=email).first() or Profissional.query.filter_by(email=email).first()
        cpf_existe = Usuario.query.filter_by(cpf=cpf).first() or Profissional.query.filter_by(cpf=cpf).first()

        if email_existe or cpf_existe:
            flash("Este E-mail ou CPF já estão registados no sistema.", "danger")
            return render_template('cadastroProfissional.html', nome=nome, cpf=cpf_raw, email=email, telefone=telefone, profissao=profissao, cidade=cidade, regiao=regiao, endereco_fixo=endereco_fixo, descricao=descricao)

        senha_criptografada = bcrypt.generate_password_hash(senha).decode('utf-8')

        # Grava os dados do profissional no banco de dados
        novo_profissional = Profissional(
            nome=nome, cpf=cpf, email=email, senha=senha_criptografada, 
            telefone=telefone, profissao=profissao, cidade=cidade, regiao=regiao, 
            endereco_fixo=endereco_fixo, descricao=descricao
        )
        
        db.session.add(novo_profissional)
        db.session.commit()

        if 'foto' in request.files:
            foto_file = request.files['foto']
            if foto_file and foto_file.filename != '':
                novo_profissional.foto = upload_to_cloudinary(foto_file, folder="profinder/perfil")
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

# ROTA: MEU PERFIL (Cliente/Profissional)

@app.route('/meu-perfil', methods=['GET', 'POST'])
@login_required
def meu_perfil():
    if request.method == 'POST':
        if current_user.tipo_conta == 'profissional':
            db_user = Profissional.query.get(current_user.id)
        else:
            db_user = Usuario.query.get(current_user.id)

        if 'foto' in request.files:
            foto_file = request.files['foto']
            if foto_file and foto_file.filename != '':
                db_user.foto = upload_to_cloudinary(foto_file, folder="profinder/perfil")

        db_user.nome = request.form.get('nome')
        db_user.email = request.form.get('email')

        # ATUALIZAÇÃO DA LOCALIDADE PARA PROFISSIONAIS
        if db_user.tipo_conta == 'profissional':
            db_user.profissao = request.form.get('profissao')
            db_user.cidade = request.form.get('cidade')
            db_user.regiao = request.form.get('regiao')
            db_user.endereco_fixo = request.form.get('endereco_fixo')
            db_user.descricao = request.form.get('descricao')
            db_user.telefone = request.form.get('telefone')

        senha_atual = request.form.get('senha_atual')
        nova_senha = request.form.get('nova_senha')
        confirma_senha = request.form.get('confirma_senha')

        if nova_senha or confirma_senha:
            if not senha_atual:
                flash("Para alterar a sua palavra-passe, deve introduzir a palavra-passe atual.", "danger")
                return redirect(url_for('meu_perfil'))

            if bcrypt.check_password_hash(db_user.senha, senha_atual):
                if nova_senha == confirma_senha:
                    if len(nova_senha) < 6:
                        flash("A nova palavra-passe deve ter pelo menos 6 caracteres.", "danger")
                        return redirect(url_for('meu_perfil'))
                    
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

        db.session.commit()
        return redirect(url_for('meu_perfil'))

    if current_user.tipo_conta == 'profissional':
        trabalhos_portfolio = Portfolio.query.filter_by(profissional_id=current_user.id).all()
        solicitacoes_recebidas = SolicitacaoServico.query.filter_by(profissional_id=current_user.id).order_by(SolicitacaoServico.data_solicitacao.desc()).all()
        return render_template('meu_perfil_profissional.html', trabalhos=trabalhos_portfolio, solicitacoes=solicitacoes_recebidas)
    else:
        minhas_solicitacoes = SolicitacaoServico.query.filter_by(cliente_id=current_user.id).order_by(SolicitacaoServico.data_solicitacao.desc()).all()
        meus_favoritos = Favorito.query.filter_by(cliente_id=current_user.id).all()
        profissionais_favoritos = [Profissional.query.get(f.profissional_id) for f in meus_favoritos]
        profissionais_favoritos = [p for p in profissionais_favoritos if p is not None]
        return render_template('meu_perfil_cliente.html', solicitacoes=minhas_solicitacoes, favoritos=profissionais_favoritos)

# ROTAS DO PORTFÓLIO E WORKFLOWS

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
            foto_url = upload_to_cloudinary(foto_file, folder="profinder/portfolio")
            
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
    
    if trabalho.profissional_id == current_user.id:
        db.session.delete(trabalho)
        db.session.commit()
        flash("Trabalho removido do seu portfólio.", "success")
    else:
        flash("Não tem permissão para excluir este trabalho.", "danger")
        
    return redirect(url_for('meu_perfil'))

@app.route('/solicitar-servico/<int:id>', methods=['POST'])
@login_required
def solicitar_servico(id):
    if current_user.tipo_conta != 'cliente':
        flash("Apenas clientes registados podem solicitar serviços. Por favor, inicie sessão com uma conta de cliente.", "danger")
        return redirect(url_for('perfil', id=id))
        
    descricao_servico = request.form.get('descricao')
    cep = request.form.get('cep')
    endereco = request.form.get('endereco')
    prazo_desejado = request.form.get('prazo_desejado')
    if not descricao_servico:
        flash("A descrição do serviço é obrigatória.", "danger")
        return redirect(url_for('perfil', id=id))
        
    nova_solicitacao = SolicitacaoServico(
        cliente_id=current_user.id,
        profissional_id=id,
        descricao=descricao_servico,
        cep=cep,
        endereco=endereco,
        prazo_desejado=prazo_desejado
    )
    
    db.session.add(nova_solicitacao)
    db.session.commit()
    
    flash("A sua solicitação foi enviada com sucesso! O profissional irá ser notificado.", "success")
    return redirect(url_for('perfil', id=id))

@app.route('/atualizar-solicitacao/<int:id>/<acao>', methods=['POST'])
@login_required
def atualizar_solicitacao(id, acao):
    if current_user.tipo_conta != 'profissional':
        return redirect(url_for('index'))
        
    solicitacao = SolicitacaoServico.query.get_or_404(id)
    
    if solicitacao.profissional_id == current_user.id:
        if acao == 'aceitar':
            solicitacao.status = 'aceito'
            flash("Você ACEITOU o pedido! Entre em contato com o cliente.", "success")
        elif acao == 'recusar':
            solicitacao.status = 'recusado'
            flash("Você RECUSOU o pedido.", "info")
        db.session.commit()
        
    return redirect(url_for('meu_perfil'))

@app.route('/avaliar/<int:solicitacao_id>', methods=['POST'])
@login_required
def avaliar_servico(solicitacao_id):
    if current_user.tipo_conta != 'cliente':
        return redirect(url_for('index'))
        
    solicitacao = SolicitacaoServico.query.get_or_404(solicitacao_id)
    
    if solicitacao.cliente_id == current_user.id and solicitacao.status == 'aceito' and not solicitacao.avaliado:
        nota = int(request.form.get('nota'))
        comentario = request.form.get('comentario')
        
        nova_avaliacao = Avaliacao(
            cliente_id=current_user.id,
            profissional_id=solicitacao.profissional_id,
            nota=nota,
            comentario=comentario
        )
        
        solicitacao.avaliado = True
        db.session.add(nova_avaliacao)
        db.session.commit()
        
        profissional = Profissional.query.get(solicitacao.profissional_id)
        todas_avaliacoes = Avaliacao.query.filter_by(profissional_id=profissional.id).all()
        
        if todas_avaliacoes:
            media = sum(av.nota for av in todas_avaliacoes) / len(todas_avaliacoes)
            profissional.avaliacao = round(media, 1)
            db.session.commit()
            
        flash("Avaliação enviada com sucesso! Obrigado pelo seu feedback.", "success")
    else:
        flash("Ação inválida. Apenas pode avaliar serviços que foram concluídos.", "danger")
        
    return redirect(url_for('meu_perfil'))

# ROTA: FAVORITAR/DESFAVORITAR PROFISSIONAL

@app.route('/favoritar/<int:id>', methods=['POST'])
@login_required
def favoritar(id):
    if current_user.tipo_conta != 'cliente':
        return jsonify({'error': 'Apenas clientes podem favoritar'}), 403
    
    existente = Favorito.query.filter_by(cliente_id=current_user.id, profissional_id=id).first()
    if existente:
        db.session.delete(existente)
        db.session.commit()
        return jsonify({'status': 'removido'})
    else:
        novo = Favorito(cliente_id=current_user.id, profissional_id=id)
        db.session.add(novo)
        db.session.commit()
        return jsonify({'status': 'adicionado'})

# ROTA: EXCLUIR CONTA

@app.route('/excluir-conta', methods=['POST'])
@login_required
def excluir_conta():
    senha = request.form.get('senha_confirmacao')
    
    if not senha:
        flash("É necessário confirmar a sua senha para excluir a conta.", "danger")
        return redirect(url_for('meu_perfil'))
    
    if not bcrypt.check_password_hash(current_user.senha, senha):
        flash("Senha incorreta. A conta não foi excluída.", "danger")
        return redirect(url_for('meu_perfil'))
    
    user_to_delete = current_user
    tipo = user_to_delete.tipo_conta
    user_id = user_to_delete.id
    
    logout_user()
    
    if tipo == 'profissional':
        # Deletar favoritos associados
        Favorito.query.filter_by(profissional_id=user_id).delete()
        # Deletar avaliações recebidas
        Avaliacao.query.filter_by(profissional_id=user_id).delete()
        # Portfolio e Solicitações são deletados via cascade
        prof = Profissional.query.get(user_id)
        if prof:
            db.session.delete(prof)
    else:
        # Deletar favoritos do cliente
        Favorito.query.filter_by(cliente_id=user_id).delete()
        # Deletar avaliações dadas
        Avaliacao.query.filter_by(cliente_id=user_id).delete()
        # Deletar solicitações feitas
        SolicitacaoServico.query.filter_by(cliente_id=user_id).delete()
        user = Usuario.query.get(user_id)
        if user:
            db.session.delete(user)
    
    db.session.commit()
    flash("A sua conta foi excluída permanentemente. Sentiremos a sua falta!", "info")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')