from flask import Flask, request, jsonify, render_template, session
import requests
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")

# المفتاح بيتجاب من Render تلقائي. ما مكتوب هنا نهائي ✅
API_KEY = os.getenv("GEMINI_API_KEY")
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"

conversations = {}

@app.route('/')
def index():
    if 'current_conv' not in session:
        new_id = str(uuid.uuid4())
        session['current_conv'] = new_id
        conversations[new_id] = []
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    conv_id = session.get('current_conv')
    if not conv_id or conv_id not in conversations:
        conv_id = str(uuid.uuid4()); session['current_conv'] = conv_id; conversations[conv_id] = []

    user_message = request.json.get('message')
    if not user_message: return jsonify({'error': 'الرجاء إدخال رسالة'}), 400

    conversations[conv_id].append({'role': 'user', 'text': user_message})
    contents = [{"role": "user" if msg['role']=='user' else "model", "parts": [{"text": msg['text']}]} for msg in conversations[conv_id]]

    if not API_KEY:
        return jsonify({'error': 'المفتاح السري غير مضبوط في السيرفر'}), 500

    try:
        response = requests.post(f"{API_URL}?key={API_KEY}", json={"contents": contents}, timeout=60)
        response.raise_for_status()
        reply = response.json()['candidates'][0]['content']['parts'][0]['text']
        conversations[conv_id].append({'role': 'bot', 'text': reply})
        return jsonify({'reply': reply, 'conv_id': conv_id})
    except Exception as e:
        return jsonify({'error': f'خطأ: {str(e)}'}), 500

@app.route('/new_chat', methods=['POST'])
def new_chat():
    new_id = str(uuid.uuid4()); session['current_conv'] = new_id; conversations[new_id] = []
    return jsonify({'conv_id': new_id, 'status': 'created'})

@app.route('/switch_chat', methods=['POST'])
def switch_chat():
    conv_id = request.json.get('conv_id')
    if conv_id in conversations: session['current_conv'] = conv_id; return jsonify({'history': conversations[conv_id], 'status': 'switched'})
    return jsonify({'error': 'المحادثة غير موجودة'}), 404

@app.route('/delete_chat', methods=['POST'])
def delete_chat():
    conv_id = request.json.get('conv_id')
    if conv_id in conversations: del conversations[conv_id]
    if session.get('current_conv') == conv_id: return new_chat()
    return jsonify({'status': 'deleted'})

@app.route('/get_history', methods=['GET'])
def get_history():
    conv_id = session.get('current_conv')
    return jsonify({'history': conversations.get(conv_id, []), 'conv_id': conv_id})

@app.route('/list_conversations', methods=['GET'])
def list_conversations():
    conv_list = [{'id': cid, 'preview': (msgs[0]['text'][:35] + '...' if msgs else 'محادثة جديدة')} for cid, msgs in conversations.items()]
    return jsonify({'conversations': conv_list})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
