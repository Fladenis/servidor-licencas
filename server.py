from flask import Flask, jsonify, request
import os

app = Flask(__name__)

@app.route('/')
def home():
    return 'Servidor online!'

@app.route('/api/criar', methods=['POST'])
def criar():
    return 'OK'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
