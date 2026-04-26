from app import app, db, Profissional
from werkzeug.security import generate_password_hash

# Lista de Pedreiros Baseada EXCLUSIVAMENTE nas imagens locais
pedreiros_realistas = [
    Profissional(
        nome='Sr. José Almeida',
        cpf='10101010101',
        email='jose.almeida@profinder.com',
        senha=generate_password_hash('senha123'), 
        profissao='Pedreiro',
        bairro='vila_rezende',
        avaliacao=4.9,
        descricao='Mais de 35 anos de experiência. Especialista em fundações, alvenaria estrutural e leitura de plantas. Trabalho sério e com garantia.',
        foto='/static/img/profissionais/pedreiro.webp'
    ),
    Profissional(
        nome='Marcos Oliveira',
        cpf='10202020202',
        email='marcos.oliveira@profinder.com',
        senha=generate_password_hash('senha123'),
        profissao='Pedreiro',
        bairro='centro',
        avaliacao=4.7,
        descricao='Faço todo tipo de reforma, do básico ao acabamento fino. Assentamento de porcelanato, azulejos e pastilhas com capricho e limpeza.',
        foto='/static/img/profissionais/pedreiro2.jpg'
    ),
    Profissional(
        nome='Carlos "Alemão" da Silva',
        cpf='10303030303',
        email='carlos.silva@profinder.com',
        senha=generate_password_hash('senha123'),
        profissao='Pedreiro',
        bairro='santa_teresinha',
        avaliacao=4.5,
        descricao='Especializado em levantamento de paredes, reboco e contrapiso. Serviço rápido, organizado e com orçamento justo. Pequenos e grandes reparos.',
        foto='/static/img/profissionais/pedreiro 3.jpg'
    ),
    Profissional(
        nome='Mestre Roberto',
        cpf='10404040404',
        email='roberto.mestre@profinder.com',
        senha=generate_password_hash('senha123'),
        profissao='Pedreiro',
        bairro='bairro_alto',
        avaliacao=5.0,
        descricao='Experiência como mestre de obras. Leitura e execução rigorosa de projetos arquitetônicos e estruturais. Acompanho sua obra do início ao fim.',
        foto='/static/img/profissionais/pedreiro 4.jpg'
    ),
    Profissional(
        nome='Paulo Mendes',
        cpf='10505050505',
        email='paulo.mendes@profinder.com',
        senha=generate_password_hash('senha123'),
        profissao='Pedreiro',
        bairro='centro',
        avaliacao=4.8,
        descricao='Pedreiro caprichoso, focado em reformas de banheiros e cozinhas. Instalação de pias, bancadas, nichos e revestimentos em geral.',
        foto='/static/img/profissionais/pedreiro 5.jpg'
    ),
    Profissional(
        nome='Fernando Costa',
        cpf='10606060606',
        email='fernando.costa@profinder.com',
        senha=generate_password_hash('senha123'),
        profissao='Pedreiro',
        bairro='vila_rezende',
        avaliacao=4.3,
        descricao='Experiência em serviços pesados: calçadas, muros de arrimo, concretagem de lajes e fundações. Trabalho resistente e duradouro.',
        foto='/static/img/profissionais/pedreiro 6.jpg'
    ),
    Profissional(
        nome='Seu Jorge "Telhadista"',
        cpf='10707070707',
        email='jorge.telhados@profinder.com',
        senha=generate_password_hash('senha123'),
        profissao='Pedreiro',
        bairro='santa_teresinha',
        avaliacao=4.6,
        descricao='Especialista em coberturas. Construção e reforma de telhados, instalação de calhas e rufo, impermeabilização de lajes e eliminação de goteiras.',
        foto='/static/img/profissionais/pedreiro 7.jpg'
    )
]

with app.app_context():
    print("--- INICIANDO POVOAMENTO DA BASE DE DADOS ---")
    
    # Limpa APENAS os pedreiros antigos para recriá-los com as novas fotos
    print("A limpar pedreiros antigos...")
    db.session.query(Profissional).filter_by(profissao='Pedreiro').delete()
    
    print(f"A adicionar {len(pedreiros_realistas)} novos perfis de Pedreiros realistas...")
    
    count = 0
    for p in pedreiros_realistas:
        existe = Profissional.query.filter_by(cpf=p.cpf).first()
        if not existe:
            db.session.add(p)
            count += 1
            print(f" -> Adicionado: {p.nome} ({p.profissao})")
        else:
             print(f" -> Pulado (CPF já existe): {p.nome}")
    
    db.session.commit()
    print(f"--- SUCESSO! {count} novos pedreiros foram adicionados à base de dados. ---")