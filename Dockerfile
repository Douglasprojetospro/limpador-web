# Usa imagem base oficial do Python
FROM python:3.10-slim

# Atualiza o pip
RUN pip install --upgrade pip

# Define diretório de trabalho
WORKDIR /app

# Copia arquivos para o container
COPY . .

# Instala as dependências
RUN pip install -r requirements.txt

# Expõe a porta padrão do Streamlit
EXPOSE 8501

# Comando de inicialização
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
