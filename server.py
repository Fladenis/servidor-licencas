# server.py - Servidor de Licenciamento para TecnoBots
import json
import os
import secrets
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ==========================================================
# >>> CONFIGURAÇÕES <<<
# ==========================================================
LICENCAS_FILE = "licencas.json"

def carregar_licencas():
    if not os.path.exists(LICENCAS_FILE):
        return {}
    with open(LICENCAS_FILE, "r") as f:
        return json.load(f)

def salvar_licencas(licencas):
    with open(LICENCAS_FILE, "w") as f:
        json.dump(licencas, f, indent=2)

# ==========================================================
# >>> ENDPOINTS <<<
# ==========================================================

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "online",
        "service": "TecnoBots Licensing Server",
        "version": "1.0.0"
    })

@app.route("/api/validar", methods=["POST"])
def validar_licenca():
    dados = request.get_json()
    chave = dados.get("chave", "").strip().upper()
    
    licencas = carregar_licencas()
    
    if chave not in licencas:
        return jsonify({"valid": False, "message": "Chave inválida"})
    
    licenca = licencas[chave]
    
    if licenca.get("status") != "active":
        return jsonify({"valid": False, "message": "Licença revogada"})
    
    expiracao = datetime.strptime(licenca.get("expiration", "2000-01-01"), "%Y-%m-%d")
    if datetime.now() > expiracao:
        return jsonify({"valid": False, "message": "Licença expirada"})
    
    return jsonify({
        "valid": True,
        "message": "Licença válida",
        "expiration": licenca.get("expiration"),
        "plan": licenca.get("plan")
    })

@app.route("/api/ativar", methods=["POST"])
def ativar_licenca():
    dados = request.get_json()
    chave = dados.get("chave", "").strip().upper()
    hardware_id = dados.get("hardware_id", "")
    
    licencas = carregar_licencas()
    
    if chave not in licencas:
        return jsonify({"success": False, "message": "Chave inválida"})
    
    licenca = licencas[chave]
    
    if licenca.get("status") != "active":
        return jsonify({"success": False, "message": "Licença revogada"})
    
    expiracao = datetime.strptime(licenca.get("expiration", "2000-01-01"), "%Y-%m-%d")
    if datetime.now() > expiracao:
        return jsonify({"success": False, "message": "Licença expirada"})
    
    # Adiciona hardware_id se não existir
    maquinas = licenca.get("activated_machines", [])
    if hardware_id and hardware_id not in maquinas:
        maquinas.append(hardware_id)
        licenca["activated_machines"] = maquinas
        salvar_licencas(licencas)
    
    return jsonify({
        "success": True,
        "message": "Licença ativada",
        "expiration": licenca.get("expiration"),
        "plan": licenca.get("plan"),
        "machines_used": len(maquinas),
        "machine_limit": licenca.get("max_activations", 2)
    })

@app.route("/api/criar", methods=["POST"])
def criar_licenca():
    dados = request.get_json()
    senha = dados.get("senha", "")
    
    if senha != "admin123":
        return jsonify({"success": False, "message": "Acesso negado"})
    
    chave = f"TECNO-{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}"
    email = dados.get("email", "")
    plano = dados.get("plano", "mensal")
    
    dias = {"mensal": 30, "trimestral": 90, "vitalicio": 3650}.get(plano, 30)
    expiracao = (datetime.now() + timedelta(days=dias)).strftime("%Y-%m-%d")
    
    licencas = carregar_licencas()
    licencas[chave] = {
        "key": chave,
        "email": email,
        "status": "active",
        "expiration": expiracao,
        "plan": plano,
        "max_activations": 2,
        "activated_machines": [],
        "created_at": datetime.now().isoformat()
    }
    salvar_licencas(licencas)
    
    return jsonify({
        "success": True,
        "chave": chave,
        "expiration": expiracao,
        "plan": plano
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
