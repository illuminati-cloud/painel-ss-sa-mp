from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import os
import random
import string
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'chave_secreta_super_segura')

# Armazenamento em memória para códigos e relatórios
CODIGOS_ATIVOS = {}  # { '2PKYVT': {'status': 'Aguardando launcher', 'expira': datetime, 'dados': None} }
RELATORIOS_SALVOS = []

STAFF_USER = os.environ.get('STAFF_USER', 'admin')
STAFF_PASS = os.environ.get('STAFF_PASS', 'sua_senha_segura')

# Layout HTML inspirado no LM Viewer
HTML_PAINEL = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>SA-MP Anti-Cheat - Leitor de Relatórios</title>
    <style>
        body { background-color: #121212; color: #e0e0e0; font-family: Arial, sans-serif; margin: 0; padding: 0; }
        header { background: #1a1a1a; border-bottom: 2px solid #2a2a2a; padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; }
        .logo { font-weight: bold; color: #fff; font-size: 16px; display: flex; align-items: center; gap: 10px; }
        .logo span { color: #ff3b3b; }
        .user-menu { display: flex; align-items: center; gap: 20px; font-size: 14px; color: #aaa; }
        .user-menu a { color: #ff4444; text-decoration: none; font-weight: bold; }
        
        .tabs { background: #181818; display: flex; padding: 0 30px; border-bottom: 1px solid #2a2a2a; }
        .tab { padding: 15px 20px; color: #888; text-decoration: none; font-size: 14px; border-bottom: 2px solid transparent; cursor: pointer; }
        .tab.active { color: #fff; border-bottom: 2px solid #ff3b3b; background: #1f1f1f; }
        
        .container { padding: 30px; }
        .btn-red { background: #ff3b3b; color: white; border: none; padding: 12px 25px; font-weight: bold; border-radius: 4px; cursor: pointer; font-size: 14px; }
        .btn-red:hover { background: #e03232; }
        
        .code-box { background: #1a1a1a; border: 1px solid #2a2a2a; width: 220px; padding: 20px; border-radius: 6px; text-align: center; margin-top: 20px; }
        .code-text { font-size: 24px; font-weight: bold; letter-spacing: 3px; color: #fff; background: #111; padding: 10px; border-radius: 4px; margin: 10px 0; border: 1px solid #333; }
        
        table { width: 100%; border-collapse: collapse; margin-top: 20px; background: #181818; border-radius: 6px; overflow: hidden; }
        th, td { padding: 12px 15px; text-align: left; font-size: 13px; border-bottom: 1px solid #2a2a2a; }
        th { background: #1f1f1f; color: #aaa; }
        tr:hover { background: #1c1c1c; }
    </style>
</head>
<body>

    <header>
        <div class="logo"><span>■</span> LM VIEWER <span style="font-size: 11px; color: #666; font-weight: normal;">SA-MP Anti-Cheat • Leitor de Relatórios</span></div>
        <div class="user-menu">
            <span>{{ user }}</span>
            <a href="/logout">Sair</a>
        </div>
    </header>

    <div class="tabs">
        <div class="tab active">Gerar Código</div>
        <div class="tab">Arquivos Suspeitos</div>
        <div class="tab">EXEs Executados</div>
        <div class="tab">Histórico de Modificações</div>
    </div>

    <div class="container">
        <form method="POST" action="/gerar-codigo">
            <button type="submit" class="btn-red">GERAR NOVO CÓDIGO</button>
        </form>

        {% if codigo_atual %}
        <div class="code-box">
            <div style="font-size: 11px; color: #888; text-transform: uppercase;">Código de Acesso</div>
            <div class="code-text">{{ codigo_atual }}</div>
            <div style="font-size: 11px; color: #f39c12;">Aguardando launcher...</div>
        </div>
        {% endif %}

        <h3 style="margin-top: 40px; color: #aaa; font-size: 14px; text-transform: uppercase;">Códigos Recentes / Relatórios</h3>
        <table>
            <thead>
                <tr>
                    <th>Código / Jogador</th>
                    <th>Gerado em</th>
                    <th>Status</th>
                    <th>Anomalias / Detalhes</th>
                </tr>
            </thead>
            <tbody>
                {% if not historico %}
                <tr><td colspan="4" style="color: #666; text-align: center;">Nenhum registro encontrado.</td></tr>
                {% endif %}
                {% for h in historico %}
                <tr>
                    <td><b>{{ h.codigo }}</b> {% if h.nickname %}({{ h.nickname }}){% endif %}</td>
                    <td>{{ h.gerado_em }}</td>
                    <td><span style="color: {% if h.status == 'Concluído' %}#2ecc71{% else %}#f39c12{% endif %};">{{ h.status }}</span></td>
                    <td>
                        {% if h.dados and h.dados.anomalias %}
                            <b style="color: #ff5555;">{{ h.dados.anomalias|length }} anomalias no GTA</b> | 
                            <b style="color: #ff9999;">{{ h.dados.executaveis|length }} EXEs no PC</b>
                        {% else %}
                            Aguardando envio...
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

</body>
</html>
"""

HTML_LOGIN = """
<!DOCTYPE html>
<html>
<head><title>Login - LM Viewer</title><meta charset="utf-8"></head>
<body style="background:#121212; color:#fff; font-family:Arial; display:flex; justify-content:center; align-items:center; height:100vh; margin:0;">
    <div style="background:#1a1a1a; padding:30px; border-radius:8px; border:1px solid #333; width:300px;">
        <h2 style="text-align:center; color:#ff3b3b; margin-top:0;">LM VIEWER</h2>
        <form method="post" action="/login">
            <label style="font-size:12px; color:#aaa;">Usuário:</label><br>
            <input type="text" name="username" style="width:100%; padding:8px; margin:6px 0 15px 0; background:#111; border:1px solid #333; color:#fff; border-radius:4px;"><br>
            <label style="font-size:12px; color:#aaa;">Senha:</label><br>
            <input type="password" name="password" style="width:100%; padding:8px; margin:6px 0 15px 0; background:#111; border:1px solid #333; color:#fff; border-radius:4px;"><br>
            <button type="submit" style="width:100%; padding:10px; background:#ff3b3b; border:none; color:#fff; font-weight:bold; cursor:pointer; border-radius:4px;">ENTRAR</button>
        </form>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    if 'user' not in session:
        return render_template_string(HTML_LOGIN)
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('username') == STAFF_USER and request.form.get('password') == STAFF_PASS:
        session['user'] = request.form.get('username')
        return redirect(url_for('dashboard'))
    return "Credenciais inválidas! <a href='/'>Voltar</a>"

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('index'))
    
    codigo_atual = session.get('ultimo_codigo')
    return render_template_string(HTML_PAINEL, user=session['user'], codigo_atual=codigo_atual, historico=RELATORIOS_SALVOS)

@app.route('/gerar-codigo', methods=['POST'])
def gerar_codigo():
    if 'user' not in session:
        return redirect(url_for('index'))
    
    # Gera um código aleatório de 6 caracteres igual ao print
    codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    CODIGOS_ATIVOS[codigo] = {
        'status': 'Aguardando launcher',
        'gerado_em': datetime.now().strftime('%d/%m/%Y, %H:%M:%S'),
        'dados': None
    }
    
    RELATORIOS_SALVOS.insert(0, {
        'codigo': codigo,
        'gerado_em': datetime.now().strftime('%d/%m/%Y, %H:%M:%S'),
        'status': 'Aguardando launcher',
        'dados': None,
        'nickname': ''
    })
    
    session['ultimo_codigo'] = codigo
    return redirect(url_for('dashboard'))

# API chamada pelo Launcher/Scanner do Jogador informando o Código gerado
@app.route('/api/enviar_scan', methods=['POST'])
def receber_scan():
    dados = request.json
    codigo = dados.get('codigo')
    
    if not codigo or codigo not in CODIGOS_ATIVOS:
        return jsonify({'erro': 'Código de acesso inválido ou expirado'}), 400
    
    # Atualiza os dados do relatório com o scan do player
    CODIGOS_ATIVOS[codigo]['status'] = 'Concluído'
    CODIGOS_ATIVOS[codigo]['dados'] = dados
    
    for r in RELATORIOS_SALVOS:
        if r['codigo'] == codigo:
            r['status'] = 'Concluído'
            r['nickname'] = dados.get('nickname', 'Desconhecido')
            r['dados'] = dados
            
    return jsonify({'status': 'sucesso', 'mensagem': 'Relatório processado com sucesso!'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
