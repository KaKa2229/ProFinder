from app import app, db, Profissional, bcrypt

with app.app_context():
    print("--- INICIANDO POVOAMENTO DA BASE DE DADOS ---")
    
    print("Limpando pedreiros antigos...")
    db.session.query(Profissional).filter_by(profissao='Pedreiro').delete()
    
    # A MÁGICA ACONTECE AQUI: Usamos o Bcrypt do seu app.py para garantir os 60 caracteres!
    senha_criptografada = bcrypt.generate_password_hash('senha123').decode('utf-8')
    
    pedreiros_realistas = [
        Profissional(
            nome='Sr. José Almeida',
            cpf='10101010101',
            email='jose.almeida@profinder.com',
            senha=senha_criptografada, 
            profissao='Pedreiro',
            cidade='Itajaí',
            regiao='fazenda',
            endereco_fixo='',
            avaliacao=4.9,
            descricao='Mais de 35 anos de experiência. Especialista em fundações, alvenaria estrutural e leitura de plantas. Trabalho sério e com garantia.',
            foto='/static/img/profissionais/pedreiro.webp'
        ),
        Profissional(
            nome='Marcos Oliveira',
            cpf='10202020202',
            email='marcos.oliveira@profinder.com',
            senha=senha_criptografada,
            profissao='Pedreiro',
            cidade='Balneário Camboriú',
            regiao='centro',
            endereco_fixo='',
            avaliacao=4.7,
            descricao='Faço todo tipo de reforma, do básico ao acabamento fino. Assentamento de porcelanato, azulejos e pastilhas com capricho e limpeza.',
            foto='/static/img/profissionais/pedreiro2.jpg'
        ),
        Profissional(
            nome='Carlos "Alemão" da Silva',
            cpf='10303030303',
            email='carlos.silva@profinder.com',
            senha=senha_criptografada,
            profissao='Pedreiro',
            cidade='Itapema',
            regiao='meia_praia',
            endereco_fixo='Rua 254, nº 10',
            avaliacao=4.5,
            descricao='Especializado em levantamento de paredes, reboco e contrapiso. Serviço rápido, organizado e com orçamento justo. Pequenos e grandes reparos.',
            foto='/static/img/profissionais/pedreiro 3.jpg'
        ),
        Profissional(
            nome='Mestre Roberto',
            cpf='10404040404',
            email='roberto.mestre@profinder.com',
            senha=senha_criptografada,
            profissao='Pedreiro',
            cidade='Navegantes',
            regiao='gravata',
            endereco_fixo='',
            avaliacao=5.0,
            descricao='Experiência como mestre de obras. Leitura e execução rigorosa de projetos arquitetônicos e estruturais. Acompanho sua obra do início ao fim.',
            foto='/static/img/profissionais/pedreiro 4.jpg'
        ),
        Profissional(
            nome='Paulo Mendes',
            cpf='10505050505',
            email='paulo.mendes@profinder.com',
            senha=senha_criptografada,
            profissao='Pedreiro',
            cidade='Itajaí',
            regiao='centro',
            endereco_fixo='Rua Hercílio Luz, Sala 2',
            avaliacao=4.8,
            descricao='Pedreiro caprichoso, focado em reformas de banheiros e cozinhas. Instalação de pias, bancadas, nichos e revestimentos em geral.',
            foto='/static/img/profissionais/pedreiro 5.jpg'
        ),
        Profissional(
            nome='Fernando Costa',
            cpf='10606060606',
            email='fernando.costa@profinder.com',
            senha=senha_criptografada,
            profissao='Pedreiro',
            cidade='Balneário Camboriú',
            regiao='nacoes',
            endereco_fixo='',
            avaliacao=4.3,
            descricao='Experiência em serviços pesados: calçadas, muros de arrimo, concretagem de lajes e fundações. Trabalho resistente e duradouro.',
            foto='/static/img/profissionais/pedreiro 6.jpg'
        ),
        Profissional(
            nome='Seu Jorge "Telhadista"',
            cpf='10707070707',
            email='jorge.telhados@profinder.com',
            senha=senha_criptografada,
            profissao='Pedreiro',
            cidade='Itajaí',
            regiao='cordeiros',
            endereco_fixo='',
            avaliacao=4.6,
            descricao='Especialista em coberturas. Construção e reforma de telhados, instalação de calhas e rufo, impermeabilização de lajes e eliminação de goteiras.',
            foto='/static/img/profissionais/pedreiro 7.jpg'
        )
    ]

    print(f"Adicionando {len(pedreiros_realistas)} novos perfis de Pedreiros realistas...")
    
    count = 0
    for p in pedreiros_realistas:
        existe = Profissional.query.filter_by(cpf=p.cpf).first()
        if not existe:
            db.session.add(p)
            count += 1
            print(f" -> Adicionado: {p.nome} ({p.cidade} - {p.regiao})")
        else:
             print(f" -> Pulado (CPF já existe): {p.nome}")
    
    db.session.commit()
    print(f"--- SUCESSO! {count} novos pedreiros foram adicionados à base de dados. ---")