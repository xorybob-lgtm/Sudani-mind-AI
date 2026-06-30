# -*- coding: utf-8 -*-
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()
AI_NAME = "Sudani Mind AI" # <- الاسم الجديد حقنا

HTML_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sudani Mind AI - عقل سوداني</title>
<style>
body { font-family: 'Tahoma', sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 20px; }
.container { max-width: 700px; margin: 40px auto; background: #1e293b; padding: 30px; border-radius: 16px; box-shadow: 0 0 20px #22c55e; }
h1 { color: #4ade80; text-align: center; }
input[type=file], input[type=text], button { width: 100%; padding: 12px; margin-top: 10px; border-radius: 8px; border: none; font-size: 16px; }
input[type=text] { background: #334155; color: #fff; }
button { background: #22c55e; color: #fff; font-weight: bold; cursor: pointer; }
button:hover { background: #16a34a; }
#response { margin-top: 20px; padding: 15px; background: #0f172a; border-radius: 8px; white-space: pre-wrap; }
</style>
</head>
<body>
<div class="container">
  <h1>🤖 Sudani Mind AI - عقل سوداني</h1>
  <p>ارفع صورة، PDF، او اكتب سؤالك بالعربي السوداني</p>
  <form action="/chat" method="post" enctype="multipart/form-data">
    <input type="file" name="file" accept="image/*,.pdf,.txt">
    <input type="text" name="question" placeholder="اسألني هنا...">
    <button type="submit">ارسل</button>
  </form>
  <div id="response">{{response}}</div>
</div>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML_PAGE.replace("{{response}}", "")

@app.post("/chat", response_class=HTMLResponse)
async def chat(request: Request, file: UploadFile = File(None), question: str = Form("")):
    file_info = ""
    if file and file.filename:
        content = await file.read()
        file_info = f"استلمت ملف: {file.filename} بحجم {len(content)} بايت. "

    q = question if question else "ما عندك سؤال؟"
    answer = f"{file_info}انا {AI_NAME}. سؤالك: {q}. هسي دي نسخة تجريبية، لاحقا بربطك بـ GPT او Gemini عشان ارد رد حقي."

    return HTML_PAGE.replace("{{response}}", f"<b>الرد:</b><br>{answer}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
