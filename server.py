# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import secrets
from datetime import datetime, timedelta
import json

app = Flask(__name__)
CORS(app)  # Permite conexões de qualquer origem

# ==========================================================
# >>> ARQUIVO DE LICENCAS <<<
# ==========================================================
LICENCAS_FILE = "licencas.json"

def carregar_licencas():
    if not os.path.exists(LICENCAS_FILE):
        return {}
    try:
        with open(LICENCAS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar licenças: {e}")
        return {}

def salvar_licencas(licencas):
    try:
        with open(LICENCAS_FILE, "w", encoding="utf-8") as f:
            json.dump(licencas, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Erro ao salvar licenças: {e}")
        return False

# ==========================================================
# >>> ROTAS PÚBLICAS (CLIENTE) <<<
# ==========================================================

@app.route('/')
def home():
    return jsonify({
        "status": "online", 
        "service": "TecnoBots Licensing Server", 
        "version": "1.0.0"
    })

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
    
    # Verifica se o hardware já está registrado
    hardware_existente = False
    for m in maquinas:
        if m.get("hardware_id") == hardware_id:
            hardware_existente = True
            break
    
    if not hardware_existente and hardware_id:
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

# ==========================================================
# >>> ROTAS ADMIN COMPATÍVEIS COM O PAINEL DO CLIENTE <<<
# ==========================================================

@app.route('/api/admin/licencas', methods=['GET'])
def admin_listar_licencas():
    """Lista todas as licenças no formato esperado pelo cliente"""
    try:
        licencas = carregar_licencas()
        # Converte para o formato que o cliente espera (dicionário com chave como índice)
        resultado = {}
        for chave, info in licencas.items():
            resultado[chave] = {
                "key": chave,
                "email": info.get("email"),
                "status": info.get("status"),
                "expiration": info.get("expiration"),
                "plan": info.get("plan"),
                "max_activations": info.get("max_activations", 2),
                "activated_machines": info.get("activated_machines", [])
            }
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/criar', methods=['POST'])
def admin_criar_licenca():
    """Cria uma nova licença (formato compatível com o cliente)"""
    try:
        dados = request.json
        chave = dados.get("chave", "").upper()
        email = dados.get("email")
        expiracao = dados.get("expiracao")
        plano = dados.get("plano", "mensal")
        max_ativacoes = dados.get("max_ativacoes", 2)
        
        if not chave or not email:
            return jsonify({"success": False, "message": "Chave e email são obrigatórios"})
        
        if not chave.startswith("TECNO-"):
            return jsonify({"success": False, "message": "Chave deve começar com TECNO-"})
        
        licencas = carregar_licencas()
        
        if chave in licencas:
            return jsonify({"success": False, "message": "Chave já existe"})
        
        licencas[chave] = {
            "key": chave,
            "email": email,
            "status": "active",
            "expiration": expiracao,
            "plan": plano,
            "max_activations": max_ativacoes,
            "activated_machines": [],
            "created_at": datetime.now().isoformat()
        }
        
        if salvar_licencas(licencas):
            return jsonify({"success": True, "message": f"Licença {chave} criada com sucesso"})
        else:
            return jsonify({"success": False, "message": "Erro ao salvar licença"})
            
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro: {str(e)}"})

@app.route('/api/admin/revogar', methods=['POST'])
def admin_revogar_licenca():
    """Revoga uma licença (formato compatível com o cliente)"""
    try:
        dados = request.json
        chave = dados.get("chave", "").upper()
        
        licencas = carregar_licencas()
        
        if chave not in licencas:
            return jsonify({"success": False, "message": "Licença não encontrada"})
        
        licencas[chave]["status"] = "revoked"
        salvar_licencas(licencas)
        return jsonify({"success": True, "message": f"Licença {chave} revogada"})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro: {str(e)}"})

@app.route('/api/admin/ativar', methods=['POST'])
def admin_ativar_licenca():
    """Reativa uma licença (formato compatível com o cliente)"""
    try:
        dados = request.json
        chave = dados.get("chave", "").upper()
        
        licencas = carregar_licencas()
        
        if chave not in licencas:
            return jsonify({"success": False, "message": "Licença não encontrada"})
        
        licencas[chave]["status"] = "active"
        salvar_licencas(licencas)
        return jsonify({"success": True, "message": f"Licença {chave} ativada"})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro: {str(e)}"})

@app.route('/api/admin/estender', methods=['POST'])
def admin_estender_licenca():
    """Estende a data de expiração (formato compatível com o cliente)"""
    try:
        dados = request.json
        chave = dados.get("chave", "").upper()
        nova_expiracao = dados.get("nova_expiracao")
        
        licencas = carregar_licencas()
        
        if chave not in licencas:
            return jsonify({"success": False, "message": "Licença não encontrada"})
        
        licencas[chave]["expiration"] = nova_expiracao
        salvar_licencas(licencas)
        return jsonify({"success": True, "message": f"Licença estendida até {nova_expiracao}"})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro: {str(e)}"})

@app.route('/api/admin/limpar_tudo', methods=['POST'])
def admin_limpar_tudo():
    """Remove TODAS as licenças (cuidado!)"""
    try:
        salvar_licencas({})
        return jsonify({"success": True, "message": "Todas as licenças foram removidas"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro: {str(e)}"})

# ==========================================================
# >>> INICIALIZAÇÃO DO SERVIDOR <<<
# ==========================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Servidor TecnoBots iniciado na porta {port}")
    print(f"📁 Arquivo de licenças: {LICENCAS_FILE}")
    print(f"🔗 URL: http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
