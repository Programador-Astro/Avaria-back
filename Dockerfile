# Usando uma versão slim para manter o container leve
FROM python:3.11-slim

# Evita que o Python grave arquivos .pyc e força o log direto no terminal
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instala as dependências primeiro (aproveita o cache do Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código
COPY . .

# Expõe a porta padrão do Flask
EXPOSE 5000

# Comando para rodar a aplicação
#CMD ["flask", "run", "--host=0.0.0.0"]
CMD gunicorn --bind 0.0.0.0:$PORT app:app