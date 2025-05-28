#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DataClean Pro - Aplicação Flask para limpeza de dados em Excel
Arquivo principal: limpador_web.py
Versão: 2.1.0
"""

import os
import re
import sys
import unicodedata
from io import BytesIO
import numpy as np
import pandas as pd
from flask import Flask, render_template, request, send_file
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename

# =============================================
# VERIFICAÇÃO DE VERSÕES
# =============================================

def check_versions():
    """Verifica compatibilidade entre NumPy e Pandas"""
    required_numpy = "1.24.3"
    required_pandas = "2.0.3"
    
    current_numpy = np.__version__
    current_pandas = pd.__version__
    
    if current_numpy != required_numpy or current_pandas != required_pandas:
        error_msg = (
            f"ERRO DE COMPATIBILIDADE:\n"
            f"Requerido - NumPy {required_numpy}, Pandas {required_pandas}\n"
            f"Instalado - NumPy {current_numpy}, Pandas {current_pandas}\n\n"
            f"Execute:\n"
            f"pip install --force-reinstall numpy=={required_numpy} pandas=={required_pandas}"
        )
        raise ImportError(error_msg)

check_versions()

# =============================================
# CONFIGURAÇÃO DA APLICAÇÃO FLASK
# =============================================

app = Flask(__name__)

# Configurações básicas
app.config.update({
    'MAX_CONTENT_LENGTH': 10 * 1024 * 1024,  # 10MB
    'UPLOAD_FOLDER': os.getenv('UPLOAD_FOLDER', '/tmp'),
    'SECRET_KEY': os.getenv('SECRET_KEY', 'dev-key-123')
})

# Configuração de segurança
Talisman(
    app,
    content_security_policy={
        'default-src': "'self'",
        'script-src': [
            "'self'",
            "'unsafe-inline'",
            "cdn.jsdelivr.net"
        ],
        'style-src': [
            "'self'",
            "'unsafe-inline'",
            "cdn.jsdelivr.net"
        ],
        'img-src': ["'self'", "data:"]
    },
    force_https=True
)

# Configuração de rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
    strategy="fixed-window"
)

# =============================================
# FUNÇÕES DE PROCESSAMENTO DE DADOS
# =============================================

def remover_acentos(texto):
    """Remove acentos e caracteres especiais"""
    if not isinstance(texto, str):
        return texto
        
    texto = unicodedata.normalize('NFKD', texto)
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    texto = texto.replace('ç', 'c').replace('Ç', 'C')
    return texto

def separar_num_letra(texto):
    """Adiciona espaços entre números e letras"""
    if not isinstance(texto, str):
        return texto
        
    texto = re.sub(r'(?<=\d)(?=[a-zA-Z])', ' ', texto)
    texto = re.sub(r'(?<=[a-zA-Z])(?=\d)', ' ', texto)
    texto = re.sub(r'(\d)[^\w\s](\w)', r'\1 \2', texto)
    texto = re.sub(r'(\w)[^\w\s](\d)', r'\1 \2', texto)
    return texto

def limpar_dataframe(df, converter_minusculo=True, remover_especiais=True, caracteres_personalizados=None):
    """Processa o DataFrame com as opções de limpeza"""
    df_limpo = df.copy()
    caracteres_padrao = r'.,;:!?@#$%^&*_+=|\\/<>[]{}()\-"\'`~'
    
    if caracteres_personalizados and isinstance(caracteres_personalizados, str):
        todos_caracteres = caracteres_padrao + caracteres_personalizados
    else:
        todos_caracteres = caracteres_padrao
    
    caracteres_regex = re.escape(todos_caracteres)
    
    for col in df_limpo.columns:
        if pd.api.types.is_string_dtype(df_limpo[col]):
            df_limpo[col] = df_limpo[col].astype(str).str.strip()
            
            if converter_minusculo:
                df_limpo[col] = df_limpo[col].str.lower()
            
            if remover_especiais:
                df_limpo[col] = df_limpo[col].apply(remover_acentos)
                df_limpo[col] = df_limpo[col].apply(lambda x: re.sub(f'[{caracteres_regex}]', ' ', x))
            
            df_limpo[col] = df_limpo[col].apply(separar_num_letra)
            df_limpo[col] = df_limpo[col].str.replace(r'\s+', ' ', regex=True).str.strip()
    
    return df_limpo

# =============================================
# ROTAS DA APLICAÇÃO
# =============================================

@app.route("/", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def index():
    """Rota principal para upload e processamento"""
    caracteres_padrao = '.,;:!?@#$%^&*_+=|\\/<>[]{}()\-"\'`~'
    erro = None
    
    if request.method == "POST":
        try:
            file = request.files.get("file")
            converter_minusculo = request.form.get("minusculo") == "on"
            remover_especiais = request.form.get("remover") == "on"
            caracteres_personalizados = request.form.get("caracteres", "").strip()
            
            if not file or file.filename == "":
                raise ValueError("Nenhum arquivo selecionado")
                
            if not file.filename.lower().endswith(('.xlsx', '.xls')):
                raise ValueError("Formato inválido. Use .xlsx ou .xls")
            
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            try:
                df = pd.read_excel(filepath, engine='openpyxl')
                df_processado = limpar_dataframe(
                    df, 
                    converter_minusculo, 
                    remover_especiais, 
                    caracteres_personalizados
                )
                
                buffer = BytesIO()
                df_processado.to_excel(buffer, index=False, engine='openpyxl')
                buffer.seek(0)
                
                if os.path.exists(filepath):
                    os.remove(filepath)
                
                return send_file(
                    buffer,
                    as_attachment=True,
                    download_name="dados_processados.xlsx",
                    mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
            except Exception as e:
                if os.path.exists(filepath):
                    os.remove(filepath)
                raise e
                
        except Exception as e:
            erro = f"Erro no processamento: {str(e)}"
    
    return render_template("index.html", erro=erro, caracteres_padrao=caracteres_padrao)

# =============================================
# INICIALIZAÇÃO
# =============================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
