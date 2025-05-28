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
    # Adiciona espaço entre número e letra (em qualquer ordem)
    texto = re.sub(r'(?<=\d)(?=[a-zA-Z])', ' ', texto)
    texto = re.sub(r'(?<=[a-zA-Z])(?=\d)', ' ', texto)
    
    # Remove caracteres especiais entre números e letras e adiciona espaço
    texto = re.sub(r'(\d)[^\w\s](\w)', r'\1 \2', texto)  # número + especial + letra
    texto = re.sub(r'(\w)[^\w\s](\d)', r'\1 \2', texto)  # letra + especial + número
    
    return texto

def limpar_dataframe(df, converter_minusculo=True, remover_especiais=True, caracteres_personalizados=None):
    df_limpo = df.copy()
    
    # Caracteres especiais padrão (sem colchetes)
    caracteres_padrao = r'.,;:!?@#$%^&*_+=|\\/<>\[\]{}()\-"\'`~'
    
    # Combina caracteres padrão com personalizados (se fornecidos)
    if caracteres_personalizados and caracteres_personalizados.strip():
        todos_caracteres = caracteres_padrao + caracteres_personalizados
    else:
        todos_caracteres = caracteres_padrao
    
    # Escapa caracteres especiais para regex
    caracteres_regex = re.escape(todos_caracteres)
    
    for col in df_limpo.columns:
        if df_limpo[col].dtype == 'object':
            df_limpo[col] = df_limpo[col].astype(str)
            if converter_minusculo:
                df_limpo[col] = df_limpo[col].str.lower()
            if remover_especiais:
                df_limpo[col] = df_limpo[col].apply(remover_acentos)
                # Remove caracteres especiais e adiciona espaços conforme necessário
                df_limpo[col] = df_limpo[col].apply(lambda x: re.sub(f'[{caracteres_regex}]', ' ', x))
            df_limpo[col] = df_limpo[col].apply(separar_num_letra)
            df_limpo[col] = df_limpo[col].str.replace(r'\s+', ' ', regex=True).str.strip()
    return df_limpo

@app.route("/", methods=["GET", "POST"])
def index():
    preview = None
    erro = None
    caracteres_padrao = '.,;:!?@#$%^&*_+=|\\/<>[]{}()\-"\'`~'  # Para exibir no campo

    if request.method == "POST":
        file = request.files.get("file")
        converter_minusculo = request.form.get("minusculo") == "on"
        remover_especiais = request.form.get("remover") == "on"
        caracteres_personalizados = request.form.get("caracteres", "").strip()

        if file and file.filename:
            try:
                df = pd.read_excel(file)
                df_processado = limpar_dataframe(
                    df, 
                    converter_minusculo, 
                    remover_especiais, 
                    caracteres_personalizados
                )

                buffer = BytesIO()
                df_processado.to_excel(buffer, index=False)
                buffer.seek(0)
                return send_file(
                    buffer, 
                    as_attachment=True, 
                    download_name="dados_processados.xlsx", 
                    mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                erro = f"Erro ao processar: {str(e)}"

    return render_template(
        "index.html", 
        erro=erro, 
        caracteres_padrao=caracteres_padrao
    )

if __name__ == "__main__":
    app.run(debug=True)
