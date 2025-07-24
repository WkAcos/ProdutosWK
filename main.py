from flask import Flask, render_template, request, url_for, redirect, flash, jsonify
import requests
import json
from db import db
from models import Usuario
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-key-insegura')
lm = LoginManager(app)
lm.login_view = 'login'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ["DATABASE_URL"]
db.init_app(app)

def hash(txt):
    hash_obj = hashlib.sha256(txt.encode('utf-8'))
    return hash_obj.hexdigest()

@lm.user_loader
def user_loader(id):
    return db.session.query(Usuario).filter_by(id=id).first()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        email = request.form['emailForm']
        senha = request.form['senhaForm']

        user = db.session.query(Usuario).filter_by(email=email, senha=hash(senha)).first()
        if not user:
            flash('Email ou senha incorretos.', 'danger')
            return redirect(url_for('login'))

        login_user(user)
        return redirect(url_for('listar_produtos'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'GET':
        return render_template('registrar.html')
    elif request.method == 'POST':
        email = request.form['emailForm']
        senha = request.form['senhaForm']
        is_admin = True
        novo_usuario = Usuario(email=email, senha=hash(senha), is_admin=is_admin)
        db.session.add(novo_usuario)
        db.session.commit()

        login_user(novo_usuario)
        return redirect(url_for('home'))

@app.route('/registrarUser', methods=['GET', 'POST'])
def registrarUser():
    if request.method == 'GET':
        return render_template('registrar.html')
    elif request.method == 'POST':
        email = request.form['emailForm']
        senha = request.form['senhaForm']
        
        novo_usuario = Usuario(email=email, senha=hash(senha), is_admin=False)
        db.session.add(novo_usuario)
        db.session.commit()

        login_user(novo_usuario)
        return redirect(url_for('home'))


@app.route('/produtos', methods=['GET', 'POST'])
def listar_produtos():
    url_api = 'https://app.omie.com.br/api/v1/geral/produtos/'

    pagina = int(request.args.get('pagina', 1))
    pagina = min(pagina, 10)

    termo_busca = request.form.get('nome') if request.method == 'POST' else request.args.get('nome', '')
    percentual = request.form.get('percentual') if request.method == 'POST' else request.args.get('percentual', '')

    payload = {
        "call": "ListarProdutosResumido",
        "param": [
            {
                "pagina": pagina,
                "registros_por_pagina": 50,
                "apenas_importado_api": "N",
                "filtrar_apenas_omiepdv": "N"
            }
        ],
        "app_key": os.environ.get("OMIE_APP_KEY"),
        "app_secret": os.environ.get("OMIE_APP_SECRET")
    }

    headers = {'Content-Type': 'application/json'}
    produtos_filtrados = []

    try:
        resposta = requests.post(url_api, headers=headers, data=json.dumps(payload))
        resposta.raise_for_status()
        dados = resposta.json()

        total_paginas = min(dados.get('total_de_paginas', 1), 10)

        for produto in dados.get('produto_servico_resumido', []):
            nome = produto.get('descricao', '')
            if termo_busca.lower() in nome.lower():
                produtos_filtrados.append({
                    'codigo': produto.get('codigo'),
                    'nome': nome,
                    'codigo_produto': produto.get('codigo_produto'),
                    'valor_unitario': produto.get('valor_unitario')
                })

        # Recupera os percentuais dos usuários logados e não logados
        # Para usuários logados, passa a lista de percentuais do usuário
        # Para usuários não logados, passa uma lista vazia, mas os percentuais de todos os usuários ainda serão exibidos
        percentuais_adicionados = db.session.query(Usuario.percentuais).all()
        # Flatten the list of percentuais (since each user's percentuais is a list)
        todos_percentuais = []
        for p in percentuais_adicionados:
            todos_percentuais.extend(p[0])  # p[0] é a lista de percentuais do usuário

        # Remover duplicatas (caso haja)
        visto = set()
        unicos = []
        for p in todos_percentuais:
            chave = (p['percentual'], p.get('descricao', ''))
            if chave not in visto:
                visto.add(chave)
                unicos.append(p)
        todos_percentuais = unicos

        return render_template(
            'produtos.html',
            produtos=produtos_filtrados,
            busca=termo_busca,
            percentual=percentual,
            pagina_atual=pagina,
            total_paginas=total_paginas,
            usuario_logado=current_user.is_authenticated,
            percentuais_usuario=todos_percentuais,  # Passando todos os percentuais aqui
            percentuais_fixos=[10, 20, 25, 50]
        )

    except requests.RequestException as erro:
        return f"Erro ao acessar a API da Omie: {erro}", 500

# ✅ Nova rota protegida para "Adicionar Percentual"
@app.route('/api/adicionar_percentual', methods=['POST'])
@login_required
def api_adicionar_percentual():
    data = request.json
    percentual = data.get('percentual')
    descricao = data.get('descricao', '').strip()  # descrição opcional

    # Verifica se percentual é válido
    try:
        percentual_float = round(float(percentual), 2)
    except (ValueError, TypeError):
        return jsonify({'erro': 'Percentual inválido.'}), 400

    # Verifica se percentual já está na lista (comparando percentual dentro dos dicts)
    existe = any(p['percentual'] == percentual_float for p in current_user.percentuais)

    if not existe:
        current_user.percentuais.append({
            'percentual': percentual_float,
            'descricao': descricao
        })
        db.session.commit()

    return jsonify({'percentuais': current_user.percentuais})



@app.route('/api/remover_percentual', methods=['POST'])
@login_required
def api_remover_percentual():
    data = request.json
    percentual = data.get('percentual')
    descricao = data.get('descricao', '').strip()

    try:
        percentual_float = float(percentual)
    except (ValueError, TypeError):
        return jsonify({'erro': 'Percentual inválido.'}), 400

    # Remove o item da lista que tenha percentual e descricao iguais
    current_user.percentuais = [
        p for p in current_user.percentuais
        if not (p['percentual'] == percentual_float and p['descricao'] == descricao)
    ]

    db.session.commit()  # Atualiza o banco de dados

    return jsonify({'success': True})


with app.app_context():
    db.create_all()
if __name__ == '__main__':
    app.run()