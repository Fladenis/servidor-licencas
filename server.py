# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request
import os
import secrets
from datetime import datetime, timedelta
import json

app = Flask(__name__)

# ==========================================================
# >>> ARQUIVO DE LICENCAS <<<
# ==========================================================
LICENCAS_FILE = "licencas.json"

def carregar_licencas():
    if not os.path.exists(LICENCAS_FILE):
        return {}
    with open(LICENCAS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_licencas(licencas):
    with open(LICENCAS_FILE, "w", encoding="utf-8") as f:
        json.dump(licencas, f, indent=2, ensure_ascii=False)

# ==========================================================
# >>> ENDPOINTS <<<
# ==========================================================

@app.route('/')
def home():
    return jsonify({"status": "online", "service": "TecnoBots Licensing Server", "version": "1.0.0"})

@app.route('/api/criar', methods=['POST'])
def criar_licenca():
    """Cria uma nova licenca (requer senha admin)"""
    dados = request.get_json()
    if not dados:
        return jsonify({"success": False, "message": "Dados nao fornecidos"})
    
    senha = dados.get("senha", "")
    
    if senha != "admin123":
        return jsonify({"success": False, "message": "Acesso negado"})
    
    email = dados.get("email", "")
    plano = dados.get("plano", "mensal")
    
    # Gera chave unica
    chave = f"TECNO-{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}"
    
    # Calcula expiracao baseada no plano
    dias_plano = {"mensal": 30, "trimestral": 90, "vitalicio": 3650}.get(plano, 30)
    expiracao = (datetime.now() + timedelta(days=dias_plano)).strftime("%Y-%m-%d")
    
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
        "plan": plano,
        "message": "Licenca criada com sucesso"
    })

@app.route('/api/validar', methods=['POST'])
def validar_licenca():
    """Valida uma chave de licenca"""
    dados = request.get_json()
    if not dados:
        return jsonify({"valid": False, "message": "Dados nao fornecidos"})
    
    chave = dados.get("chave", "").strip().upper()
    
    licencas = carregar_licencas()
    
    if chave not in licencas:
        return jsonify({"valid": False, "message": "Chave invalida"})
    
    licenca = licencas[chave]
    
    if licenca.get("status") != "active":
        return jsonify({"valid": False, "message": "Licenca revogada"})
    
    expiracao = datetime.strptime(licenca.get("expiration", "2000-01-01"), "%Y-%m-%d")
    if datetime.now() > expiracao:
        return jsonify({"valid": False, "message": "Licenca expirada"})
    
    return jsonify({
        "valid": True,
        "message": "Licenca valida",
        "expiration": licenca.get("expiration"),
        "plan": licenca.get("plan", "mensal")
    })

@app.route('/api/ativar', methods=['POST'])
def ativar_licenca():
    """Ativa uma licenca em uma maquina (registra hardware_id)"""
    dados = request.get_json()
    if not dados:
        return jsonify({"success": False, "message": "Dados nao fornecidos"})
    
    chave = dados.get("chave", "").strip().upper()
    hardware_id = dados.get("hardware_id", "")
    nome_maquina = dados.get("maquina_nome", "")
    
    licencas = carregar_licencas()
    
    if chave not in licencas:
        return jsonify({"success": False, "message": "Chave invalida"})
    
    licenca = licencas[chave]
    
    if licenca.get("status") != "active":
        return jsonify({"success": False, "message": "Licenca revogada"})
    
    expiracao = datetime.strptime(licenca.get("expiration", "2000-01-01"), "%Y-%m-%d")
    if datetime.now() > expiracao:
        return jsonify({"success": False, "message": "Licenca expirada"})
    
    maquinas = licenca.get("activated_machines", [])
    max_maquinas = licenca.get("max_activations", 2)
    
    if hardware_id and hardware_id not in maquinas:
        if len(maquinas) >= max_maquinas:
            return jsonify({"success": False, "message": f"Limite de {max_maquinas} maquinas atingido"})
        
        maquinas.append({
            "hardware_id": hardware_id,
            "nome": nome_maquina,
            "data_ativacao": datetime.now().isoformat()
        })
        licenca["activated_machines"] = maquinas
        salvar_licencas(licencas)
    
    return jsonify({
        "success": True,
        "message": "Licenca ativada com sucesso",
        "expiration": licenca.get("expiration"),
        "plan": licenca.get("plan", "mensal"),
        "machines_used": len(maquinas),
        "machine_limit": max_maquinas
    })

@app.route('/api/revogar', methods=['POST'])
def revogar_licenca():
    """Revoga uma licenca (requer senha admin)"""
    dados = request.get_json()
    if not dados:
        return jsonify({"success": False, "message": "Dados nao fornecidos"})
    
    senha = dados.get("senha", "")
    chave = dados.get("chave", "").strip().upper()
    
    if senha != "admin123":
        return jsonify({"success": False, "message": "Acesso negado"})
    
    licencas = carregar_licencas()
    
    if chave not in licencas:
        return jsonify({"success": False, "message": "Licenca nao encontrada"})
    
    licencas[chave]["status"] = "revoked"
    salvar_licencas(licencas)
    
    return jsonify({"success": True, "message": "Licenca revogada com sucesso"})

@app.route('/api/listar', methods=['POST'])
def listar_licencas():
    """Lista todas as licencas (requer senha admin)"""
    dados = request.get_json()
    if not dados:
        return jsonify({"success": False, "message": "Dados nao fornecidos"})
    
    senha = dados.get("senha", "")
    
    if senha != "admin123":
        return jsonify({"success": False, "message": "Acesso negado"})
    
    licencas = carregar_licencas()
    
    resultado = []
    for chave, info in licencas.items():
        resultado.append({
            "chave": chave,
            "email": info.get("email"),
            "status": info.get("status"),
            "expiration": info.get("expiration"),
            "plan": info.get("plan"),
            "maquinas_ativas": len(info.get("activated_machines", [])),
            "max_maquinas": info.get("max_activations", 2),
            "created_at": info.get("created_at")
        })
    
    return jsonify({"success": True, "licencas": resultado})

@app.route('/api/buscar', methods=['POST'])
def buscar_licenca():
    """Busca uma licenca especifica pelo email (requer senha admin)"""
    dados = request.get_json()
    if not dados:
        return jsonify({"success": False, "message": "Dados nao fornecidos"})
    
    senha = dados.get("senha", "")
    email = dados.get("email", "").strip().lower()
    
    if senha != "admin123":
        return jsonify({"success": False, "message": "Acesso negado"})
    
    licencas = carregar_licencas()
    
    resultados = []
    for chave, info in licencas.items():
        if info.get("email", "").lower() == email:
            resultados.append({
                "chave": chave,
                "email": info.get("email"),
                "status": info.get("status"),
                "expiration": info.get("expiration"),
                "plan": info.get("plan"),
                "maquinas_ativas": len(info.get("activated_machines", [])),
                "max_maquinas": info.get("max_activations", 2),
                "created_at": info.get("created_at")
            })
    
    return jsonify({"success": True, "licencas": resultados})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
