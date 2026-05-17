from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "online", "message": "Servidor TecnoBots funcionando!"})

@app.route('/api/criar', methods=['POST'])
def criar_licenca():
    return jsonify({"success": True, "chave": "TESTE-1234", "message": "Endpoint /api/criar funcionando!"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
