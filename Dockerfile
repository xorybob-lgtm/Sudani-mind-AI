FROM python:3.10-slim
WORKDIR /code
COPY requirements.txt . <- مسافة هنا قبل النقطة
RUN pip install --no-cache-dir -r requirements.txt
COPY . <- مسافة هنا قبل النقطة
CMD ["python", "app.py"]
