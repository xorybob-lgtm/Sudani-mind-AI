from flask import Flask, request, jsonify, render_template, session
import requests
import json
import uuid

app = Flask(__name__)
app.secret_key = '7d8f9a2b3c4d5e6f7g8h9i0j1k2l3m4n'  # مفتاح تشفير الجلسات

# مفتاح API الخاص بـ Gemini
API_KEY = "AIzaSyA_AVDSifB00CuyFySj-ePwc0YnntthU8A"
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"

# تخزين المحادثات في الذاكرة (للاستخدام المؤقت)
conversations = {}

@app.route('/')
def index():
    """الصفحة الرئيسية - إنشاء محادثة جديدة إذا لم توجد"""
    if 'current_conv' not in session:
        new_id = str(uuid.uuid4())
        session['current_conv'] = new_id
        conversations[new_id] = []
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """معالجة رسائل الدردشة مع الحفاظ على السياق"""
    conv_id = session.get('current_conv')
    if not conv_id or conv_id not in conversations:
        conv_id = str(uuid.uuid4())
        session['current_conv'] = conv_id
        conversations[conv_id] = []

    user_message = request.json.get('message')
    if not user_message:
        return jsonify({'error': 'الرجاء إدخال رسالة'}), 400

    # إضافة رسالة المستخدم إلى التاريخ
    conversations[conv_id].append({'role': 'user', 'text': user_message})

    # بناء السياق الكامل للمحادثة
    history_parts = []
    for msg in conversations[conv_id]:
        history_parts.append({"text": msg['text']})

    payload = {
        "contents": [
            {"parts": history_parts}
        ]
    }

    headers = {'Content-Type': 'application/json'}
    url = f"{API_URL}?key={API_KEY}"

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        reply = data['candidates'][0]['content']['parts'][0]['text']

        # إضافة رد البوت إلى التاريخ
        conversations[conv_id].append({'role': 'bot', 'text': reply})

        return jsonify({'reply': reply, 'conv_id': conv_id})
    
    except requests.exceptions.Timeout:
        return jsonify({'error': 'انتهى وقت الاتصال، حاول مرة أخرى'}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'خطأ في الاتصال: {str(e)}'}), 500
    except KeyError:
        return jsonify({'error': 'خطأ في استجابة API'}), 500

@app.route('/new_chat', methods=['POST'])
def new_chat():
    """إنشاء محادثة جديدة"""
    new_id = str(uuid.uuid4())
    session['current_conv'] = new_id
    conversations[new_id] = []
    return jsonify({'conv_id': new_id, 'status': 'created'})

@app.route('/switch_chat', methods=['POST'])
def switch_chat():
    """التبديل إلى محادثة موجودة"""
    conv_id = request.json.get('conv_id')
    if conv_id in conversations:
        session['current_conv'] = conv_id
        history = conversations[conv_id]
        formatted = [{'role': msg['role'], 'text': msg['text']} for msg in history]
        return jsonify({'history': formatted, 'status': 'switched'})
    return jsonify({'error': 'المحادثة غير موجودة'}), 404

@app.route('/delete_chat', methods=['POST'])
def delete_chat():
    """حذف محادثة"""
    conv_id = request.json.get('conv_id')
    if conv_id in conversations:
        del conversations[conv_id]
        if session.get('current_conv') == conv_id:
            # إنشاء محادثة جديدة تلقائياً
            new_id = str(uuid.uuid4())
            session['current_conv'] = new_id
            conversations[new_id] = []
        return jsonify({'status': 'deleted'})
    return jsonify({'error': 'المحادثة غير موجودة'}), 404

@app.route('/get_history', methods=['GET'])
def get_history():
    """جلب تاريخ المحادثة الحالية"""
    conv_id = session.get('current_conv')
    if conv_id and conv_id in conversations:
        history = conversations[conv_id]
        formatted = [{'role': msg['role'], 'text': msg['text']} for msg in history]
        return jsonify({'history': formatted, 'conv_id': conv_id})
    return jsonify({'history': [], 'conv_id': None})

@app.route('/list_conversations', methods=['GET'])
def list_conversations():
    """عرض قائمة جميع المحادثات مع معاينة"""
    conv_list = []
    for cid, msgs in conversations.items():
        if msgs:
            first_msg = msgs[0]['text']
            preview = first_msg[:35] + '...' if len(first_msg) > 35 else first_msg
        else:
            preview = 'محادثة جديدة'
        conv_list.append({'id': cid, 'preview': preview})
    return jsonify({'conversations': conv_list})

@app.route('/clear_all', methods=['POST'])
def clear_all():
    """مسح جميع المحادثات (للصيانة)"""
    conversations.clear()
    new_id = str(uuid.uuid4())
    session['current_conv'] = new_id
    conversations[new_id] = []
    return jsonify({'status': 'all_cleared'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
