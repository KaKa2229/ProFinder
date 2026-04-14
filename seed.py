from app import app, db, Profissional

# Profissionais teste para popular a base de dados
profissionais_teste = [
    Profissional(
        nome='Jorge Cabral',
        cpf='11111111111',
        email='jorge@profinder.com',
        senha='senha_segura_123',
        profissao='Pedreiro',
        bairro='cabecudas',
        avaliacao=4.5,
        foto='https://images.unsplash.com/photo-1503387762-592deb58ef4e?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80'
    ),
    Profissional(
        nome='Marcos Silva',
        cpf='22222222222',
        email='marcos@profinder.com',
        senha='senha_segura_123',
        profissao='Pedreiro',
        bairro='centro_itajai',
        avaliacao=5.0,
        foto='https://images.unsplash.com/photo-1534398079543-7ae6d016b86c?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80'
    ),
    Profissional(
        nome='Roberto Nunes',
        cpf='33333333333',
        email='roberto@profinder.com',
        senha='senha_segura_123',
        profissao='Pedreiro',
        bairro='dom_bosco',
        avaliacao=3.0,
        foto='https://images.unsplash.com/photo-1622313620959-1586526ddfae?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80'
    ),
    Profissional(
        nome='Ana Costa',
        cpf='44444444444',
        email='ana@profinder.com',
        senha='senha_segura_123',
        profissao='Jardineiro',
        bairro='fazenda',
        avaliacao=4.8,
        foto='https://images.unsplash.com/photo-1592424001807-55099252c809?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80'
    ),
    Profissional(
        nome='Carlos Mendes',
        cpf='55555555555',
        email='carlos@profinder.com',
        senha='senha_segura_123',
        profissao='Encanador',
        bairro='cordeiros',
        avaliacao=4.2,
        foto='https://images.unsplash.com/photo-1584622650111-993a426fbf0a?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80'
    )
]

# O contexto da aplicação é necessário para interagir com a base de dados
with app.app_context():
    # Evitar loop, com profissionais duplicados
    print("limpaando a tabela de profissionais antigos...")
    db.session.query(Profissional).delete()
    
    print("adicionando novos profissionais de teste...")
    for p in profissionais_teste:
        db.session.add(p)
    
    db.session.commit()
    print("Base de dados populada com sucesso.")