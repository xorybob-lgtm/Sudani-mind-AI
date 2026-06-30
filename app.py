import os
import uuid
import base64
from flask import Flask, render_template, request, jsonify, session
from google import genai
from google.genai import types

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "sudani2026")
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024 # 20MB max

conversations = {}

API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY) if API_KEY else None
MODEL_NAME = "gemini-2.0-flash-exp"

@app.route("/")
def home():
    return render_template('index.html')

@app.route("/chat", methods=["POST"])
def chat():
    if not client: return jsonify({"error": "المفتاح السري غير مضبوط"}), 500

    message = request.form.get("message", "").strip()
    file = request.files.get('file')

    if not message and not file: return jsonify({"error": "ارسل نص او ملف"}), 400

    conv_id = session.get("conv_id")
    if not conv_id or conv_id not in conversations:
        conv_id = str(uuid.uuid4())
        session["conv_id"] = conv_id
        conversations[conv_id] = []

    history = conversations[conv_id]
    user_parts = []
    file_data_for_ui = None

    if message:
        user_parts.append(types.Part.from_text(text=message))
        history.append({"role": "user", "text": message, "file": None})

    if file:
        file_bytes = file.read()
        mime_type = file.mimetype
        user_parts.append(types.Part.from_bytes(data=file_bytes, mime_type=mime_type))
        file_data_for_ui = {"name": file.filename, "type": mime_type}
        if mime_type.startswith('image/'):
            b64 = base64.b64encode(file_bytes).decode('utf-8')
            file_data_for_ui["url"] = f"data:{mime_type};base64,{b64}"
        history.append({"role": "user", "text": f"[ملف: {file.filename}]", "file": file_data_for_ui})

    if not history or history[-1]["role"]!= "user":
        conversations[conv_id].append({"role": "user", "text": message, "file": file_data_for_ui})

    try:
        contents = []
        for msg in history:
            role = "user" if msg["role"] == "user" else "model"
            parts = [types.Part.from_text(text=msg["text"])]
            contents.append(types.Content(role=role, parts=parts))

        contents[-1].parts = user_parts # استبدال اخر رسالة بالمرفقات الحقيقية

        response = client.models.generate_content(model=MODEL_NAME, contents=contents)
        reply = response.text
        history.append({"role": "model", "text": reply, "file": None})
        return jsonify({"reply": reply, "conv_id": conv_id})
    except Exception as e:
        print(f"Gemini Error: {e}")
        return jsonify({"error": f"خطأ من Gemini: {e}"}), 500

@app.route("/get_history")
def get_history():
    conv_id = session.get("conv_id")
    return jsonify({"history": conversations.get(conv_id, []), "conv_id": conv_id})

@app.route("/list_conversations")
def list_conversations():
    convs = [{"id": cid, "preview": msgs[0]["text"][:30] + "..." if msgs else "محادثة جديدة"} for cid, msgs in conversations.items()]
    return jsonify({"conversations": convs})

@app.route("/switch_chat", methods=["POST"])
def switch_chat():
    conv_id = request.get_json().get("conv_id")
    session["conv_id"] = conv_id
    return jsonify({"history": conversations.get(conv_id, [])})

@app.route("/new_chat", methods=["POST"])
def new_chat():
    conv_id = str(uuid.uuid4())
    session["conv_id"] = conv_id
    conversations[conv_id] = []
    return jsonify({"conv_id": conv_id})

@app.route("/delete_chat", methods=["POST"])
def delete_chat():
    conv_id = request.get_json().get("conv_id")
    if conv_id in conversations: del conversations[conv_id]
    if session.get("conv_id") == conv_id: session.pop("conv_id", None)
    return jsonify({"status": "deleted"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
