
from flask import Flask, render_template, request, send_file
import pandas as pd
import re
import unicodedata
from io import BytesIO

app = Flask(__name__)

def remover_acentos(texto):
    texto = unicodedata.normalize('NFKD', texto)
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    texto = texto.replace('ç', 'c').replace('Ç', 'C')
    return texto

def separar_num_letra(texto):
    texto = re.sub(r'(?<=\d)(?=[a-zA-Z])', ' ', texto)
    texto = re.sub(r'(?<=[a-zA-Z])(?=\d)', ' ', texto)
    return texto

def limpar_dataframe(df, converter_minusculo=True, remover_especiais=True, caracteres_regex=None):
    df_limpo = df.copy()
    if not caracteres_regex:
        caracteres_regex = r'[.,;:!?@#$%^&*_+=|\\/<>\[\]{}()\-"\'\`~]'

    for col in df_limpo.columns:
        if df_limpo[col].dtype == 'object':
            df_limpo[col] = df_limpo[col].astype(str)
            if converter_minusculo:
                df_limpo[col] = df_limpo[col].str.lower()
            if remover_especiais:
                df_limpo[col] = df_limpo[col].apply(remover_acentos)
                df_limpo[col] = df_limpo[col].apply(lambda x: re.sub(caracteres_regex, ' ', x))
            df_limpo[col] = df_limpo[col].apply(separar_num_letra)
            df_limpo[col] = df_limpo[col].str.replace(r'\s+', ' ', regex=True).str.strip()
    return df_limpo

@app.route("/", methods=["GET", "POST"])
def index():
    preview = None
    if request.method == "POST":
        file = request.files.get("file")
        converter_minusculo = request.form.get("minusculo") == "on"
        remover_especiais = request.form.get("remover") == "on"
        caracteres = request.form.get("caracteres") or r'[.,;:!?@#$%^&*_+=|\\/<>\[\]{}()\-"\'\`~]'

        if file and file.filename:
            try:
                df = pd.read_excel(file)
                df_processado = limpar_dataframe(df, converter_minusculo, remover_especiais, caracteres)
                preview = df_processado.head(10).to_html(classes="table table-striped", index=False)

                buffer = BytesIO()
                df_processado.to_excel(buffer, index=False)
                buffer.seek(0)
                return send_file(buffer, as_attachment=True, download_name="dados_processados.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            except Exception as e:
                return f"Erro ao processar: {str(e)}", 500

    return render_template("index.html", preview=preview)

if __name__ == "__main__":
    app.run(debug=True)
