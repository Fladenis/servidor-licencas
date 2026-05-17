from flask import Flask, jsonify
import json
import os

app = Flask(__name__)

# Carrega licenças do arquivo (ou variável de ambiente)
LICENSAS_FILE = "licencas.json"

def carregar_licencas():
    if not os.path.exists(LICENSAS_FILE):
        return {}
    with open(LICENSAS_FILE, "r") as f:
        return json.load(f)

@app.route('/validar/<chave>')
def validar(chave):
    licencas = carregar_licencas()
    if chave not in licencas:
        return jsonify({"valid": False, "message": "Chave inválida"})
    
    licenca = licencas[chave]
    if licenca.get("status") != "active":
        return jsonify({"valid": False, "message": "Licença revogada"})
    
    from datetime import datetime
    expiracao = datetime.strptime(licenca.get("expiration", "2000-01-01"), "%Y-%m-%d")
    if datetime.now() > expiracao:
        return jsonify({"valid": False, "message": "Licença expirada"})
    
    return jsonify({
        "valid": True,
        "plan": licenca.get("plan", "mensal"),
        "expiration": licenca.get("expiration", "")
    })

@app.route('/licencas')
def listar_licencas():
    return jsonify(carregar_licencas())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
