from flask import Flask, render_template, request, send_file
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import pandas as pd
import re
import unicodedata
from io import BytesIO
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', '/tmp')

# Security middleware
Talisman(app, content_security_policy={
    'default-src': "'self'",
    'script-src': ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net"],
    'style-src': ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net"],
    'img-src': ["'self'", "data:"]
})

# Rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

def remover_acentos(texto):
    texto = unicodedata.normalize('NFKD', texto)
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    texto = texto.replace('ç', 'c').replace('Ç', 'C')
    return texto

def separar_num_letra(texto):
    texto = re.sub(r'(?<=\d)(?=[a-zA-Z])', ' ', texto)
    texto = re.sub(r'(?<=[a-zA-Z])(?=\d)', ' ', texto)
    texto = re.sub(r'(\d)[^\w\s](\w)', r'\1 \2', texto)
    texto = re.sub(r'(\w)[^\w\s](\d)', r'\1 \2', texto)
    return texto

def limpar_dataframe(df, converter_minusculo=True, remover_especiais=True, caracteres_personalizados=None):
    df_limpo = df.copy()
    caracteres_padrao = r'.,;:!?@#$%^&*_+=|\\/<>\[\]{}()\-"\'`~'
    
    if caracteres_personalizados and caracteres_personalizados.strip():
        todos_caracteres = caracteres_padrao + caracteres_personalizados
    else:
        todos_caracteres = caracteres_padrao
    
    caracteres_regex = re.escape(todos_caracteres)
    
    for col in df_limpo.columns:
        if df_limpo[col].dtype == 'object':
            df_limpo[col] = df_limpo[col].astype(str)
            if converter_minusculo:
                df_limpo[col] = df_limpo[col].str.lower()
            if remover_especiais:
                df_limpo[col] = df_limpo[col].apply(remover_acentos)
                df_limpo[col] = df_limpo[col].apply(lambda x: re.sub(f'[{caracteres_regex}]', ' ', x))
            df_limpo[col] = df_limpo[col].apply(separar_num_letra)
            df_limpo[col] = df_limpo[col].str.replace(r'\s+', ' ', regex=True).str.strip()
    return df_limpo

@app.route("/", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def index():
    preview = None
    erro = None
    caracteres_padrao = '.,;:!?@#$%^&*_+=|\\/<>[]{}()\-"\'`~'

    if request.method == "POST":
        file = request.files.get("file")
        converter_minusculo = request.form.get("minusculo") == "on"
        remover_especiais = request.form.get("remover") == "on"
        caracteres_personalizados = request.form.get("caracteres", "").strip()

        if file and file.filename:
            try:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                df = pd.read_excel(filepath)
                df_processado = limpar_dataframe(
                    df, 
                    converter_minusculo, 
                    remover_especiais, 
                    caracteres_personalizados
                )

                buffer = BytesIO()
                df_processado.to_excel(buffer, index=False, engine='openpyxl')
                buffer.seek(0)
                
                os.remove(filepath)  # Clean up
                
                return send_file(
                    buffer,
                    as_attachment=True,
                    download_name="dados_processados.xlsx",
                    mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                if os.path.exists(filepath):
                    os.remove(filepath)
                erro = f"Erro ao processar: {str(e)}"

    return render_template(
        "index.html", 
        erro=erro, 
        caracteres_padrao=caracteres_padrao
    )

if __name__ == "__main__":
    app.run(debug=True)
