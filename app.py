import os
import re
import unicodedata
import pandas as pd
from flask import Flask, request, render_template, send_file
from werkzeug.utils import secure_filename
from io import BytesIO

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'xlsx'}

def eh_arquivo_valido(arquivo):
    filename = secure_filename(arquivo.filename)
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def remover_acentos(texto):
    texto = unicodedata.normalize('NFKD', texto)
    return ''.join(c for c in texto if not unicodedata.combining(c)).replace('ç', 'c').replace('Ç', 'C')

def separar_num_letra(texto):
    texto = re.sub(r'(?<=\d)(?=[a-zA-Z])', ' ', texto)
    texto = re.sub(r'(?<=[a-zA-Z])(?=\d)', ' ', texto)
    return texto

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        arquivo = request.files.get('file')
        caracteres = request.form.get('caracteres', r'[.,;:!?@#$%^&*_+=|\\/<>\[\]{}()\-"\'`~]')
        minusculo = request.form.get('minusculo') == 'on'
        remover_especiais = request.form.get('remover_especiais') == 'on'

        if not arquivo or not eh_arquivo_valido(arquivo):
            return "Erro: apenas arquivos .xlsx válidos são permitidos.", 400

        try:
            arquivo_bytes = arquivo.read()
            df = pd.read_excel(BytesIO(arquivo_bytes))
        except Exception as e:
            return f"Erro ao processar o arquivo Excel: {str(e)}", 400

        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str)

                if minusculo:
                    df[col] = df[col].str.lower()

                if remover_especiais:
                    df[col] = df[col].apply(remover_acentos)
                    df[col] = df[col].apply(lambda x: re.sub(caracteres, ' ', x))

                df[col] = df[col].apply(separar_num_letra)
                df[col] = df[col].str.replace(r'\s+', ' ', regex=True).str.strip()

        output = BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)

        return send_file(
            output,
            as_attachment=True,
            download_name='dados_processados.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    return render_template('index.html', max_size_mb=10)

@app.errorhandler(413)
def too_large(e):
    return "Erro: o arquivo excede o tamanho máximo permitido (10 MB).", 413
