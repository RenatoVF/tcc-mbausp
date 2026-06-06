FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY avaliador_llm.py .

CMD ["python", "avaliador_llm.py"]