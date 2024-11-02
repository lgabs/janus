FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

ENV PYTHONPATH=/app

CMD ["streamlit", "run", "Homepage.py"]
