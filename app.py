from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'chave_secreta_super_segura_para_producao')

# Banco de dados em memória temporário
RELATORIOS_JOGADORES = []

# Defina a senha e usuário da staff (você pode alterar aqui ou usar variáveis de ambiente)
STAFF_USER = os.environ.get('STAFF_USER', 'admin')
STAFF_PASS = os.environ.get('STAFF_PASS', 'sua_senha_segura')

# HTML da Tela de Login
HTML_LOGIN = """
<!DOCTYPE html>
<html>
<head><title>Login - Painel SS SA-MP</title><meta charset="utf-8"></head>
<body style="background:#121212; color:#fff; font-family:Arial; display:flex; justify-content:center; align-items:center; height:100vh; margin:0;">
    <div style="background:#1e1e1e; padding:30px; border-radius:8px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); width:300px;">
        <h2 style="text-align:center; color:#ff4444;">Painel Staff SS</h2>
        <form method="post" action="/login">
            <label>Usuário:</label><br>
            <input type="text" name="username" style="width:100%; padding:8px; margin:8px 0; background:#2a2a2a; border:1px solid #444; color:#fff;"><br>
            <label>Senha:</label><br>
            <input type="password" name="password" style="width:100%; padding:8px; margin:8px 0; background:#2a2a2a; border:1px solid #444; color:#fff;"><br>
            <button type="submit" style="width:100%; padding:10px; background:#ff4444; border:none; color:#fff; font-weight:bold; cursor:pointer; margin-top:10px;">Entrar</button>
        </form>
    </div>
</body>
</html>
"""

# HTML do Dashboard Principal da Staff
HTML_DASHBOARD = """
<!DOCTYPE html>
<html>
<head><title>Dashboard - Inspeções SA-MP</title><meta charset="utf-8"></head>
<body style="background:#121212; color:#fff; font-family:Arial; padding:20px;">
    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #333; padding-bottom:10px;">
        <h2>Painel de Inspeção & Revistas (SA-MP)</h2>
        <a href="/logout" style="color:#ff4444; text-decoration:none; font-weight:bold;">Sair</a>
    </div>
    <h3>Jogadores Analisados Recentemente:</h3>
    {% if not relatorios %}
        <p style="color:#888;">Nenhum relatório de varredura recebido ainda.</p>
    {% endif %}
    {% for r in relatorios %}
        <div style="background:#1e1e1e; border:1px solid #333; padding:15px; border-radius:6px; margin-bottom:15px;">
            <h3 style="margin-top:0; color:#4da6ff;">👤 Jogador: {{ r.nickname }} <span style="font-size:12px; color:#aaa; font-weight:normal;">(PC: {{ r.computador }})</span></h3>
            
            <h4 style="color:#ffaa00; margin-bottom:5px;">📁 Anomalias / Modificações na Pasta do GTA:</h4>
            {% if not r.anomalias %}
                <p style="color:#00ff88; margin:0;">Nenhuma anomalia evidente na pasta do jogo.</p>
            {% else %}
                <ul style="margin:5px 0; padding-left:20px;">
                {% for a in r.anomalias %}
                    <li style="color:#ff5555;"><b>Arquivo:</b> {{ a.arquivo }} | <b>Tipo:</b> {{ a.tipo }} | <i>{{ a.motivo }}</i></li>
                {% endfor %}
                </ul>
            {% endif %}

            <h4 style="color:#ffaa00; margin-bottom:5px; margin-top:15px;">💻 Executáveis / Rastros Encontrados no PC:</h4>
            {% if not r.executaveis %}
                <p style="color:#00ff88; margin:0;">Nenhum executável suspeito listado.</p>
            {% else %}
                <ul style="margin:5px 0; padding-left:20px; max-height: 150px; overflow-y: auto;">
                {% for ex in r.executaveis %}
                    <li style="font-size:13px; color:#ff9999;"><b>Caminho:</b> {{ ex.caminho }} | <b>Modificado:</b> {{ ex.modificado_em }}</li>
                {% endfor %}
                </ul>
            {% endif %}
        </div>
    {% endfor %}
</body>
</html>
"""

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template_string(HTML_LOGIN)

@app.route('/login', methods=['POST'])
def login():
    user = request.form.get('username')
    pwd = request.form.get('password')
    if user == STAFF_USER and pwd == STAFF_PASS:
        session['user'] = user
        return redirect(url_for('dashboard'))
    return "Credenciais inválidas! <a href='/'>Voltar</a>"

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('index'))
    return render_template_string(HTML_DASHBOARD, relatorios=RELATORIOS_JOGADORES)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

# API unificada para receber os dados enviados pelo Scanner do Jogador
@app.route('/api/enviar_scan', methods=['POST'])
def receber_scan():
    dados = request.json
    if not dados or 'nickname' not in dados:
        return jsonify({'erro': 'Dados inválidos'}), 400
    
    global RELATORIOS_JOGADORES
    # Remove relatório anterior do mesmo player para atualizar com o novo
    RELATORIOS_JOGADORES = [r for r in RELATORIOS_JOGADORES if r['nickname'] != dados['nickname']]
    
    # Adiciona o novo relatório no topo da lista
    RELATORIOS_JOGADORES.insert(0, dados)
    return jsonify({'status': 'sucesso'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)