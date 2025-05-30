import os
import time
from flask import Flask, request, render_template, send_file, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import pandas as pd
from io import BytesIO
import uuid

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['TEMPLATE_FOLDER'] = 'templates'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['TEMPLATE_FOLDER'], exist_ok=True)

# Sample transportadoras data (replace with your actual data)
TRANSPORTADORAS = {
    'JADLOG': {
        'name': 'Jadlog',
        'modality': 'Expresso'
    },
    'CORREIOS': {
        'name': 'Correios',
        'modality': 'PAC'
    },
    'TOTAL': {
        'name': 'Total Express',
        'modality': 'Standard'
    }
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
    
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Read the Excel file
            df = pd.read_excel(filepath)
            
            # Validate required columns
            required_columns = ['CEP_Origem', 'CEP_Destino', 'Peso', 'Valor_NF', 'Volume']
            if not all(col in df.columns for col in required_columns):
                missing = [col for col in required_columns if col not in df.columns]
                return jsonify({'error': f'Colunas obrigatórias faltando: {", ".join(missing)}'}), 400
            
            # Process each row and get quotes
            results = []
            for _, row in df.iterrows():
                for transportadora, info in TRANSPORTADORAS.items():
                    # Here you would call your actual freight calculation API
                    # This is just a simulation with random values
                    quote = calculate_freight(
                        row['CEP_Origem'],
                        row['CEP_Destino'],
                        row['Peso'],
                        row['Valor_NF'],
                        row['Volume'],
                        transportadora
                    )
                    
                    results.append({
                        'Nota': row.get('Nota', 'N/A'),
                        'Descricao': row.get('Descricao', 'N/A'),
                        'Transportadora': info['name'],
                        'Modalidade': info['modality'],
                        'ValorFrete': f"R$ {quote['valor']:,.2f}".replace('.', ','),
                        'Prazo': quote['prazo'],
                        'ICMS': f"R$ {quote['icms']:,.2f}".replace('.', ','),
                        'AliquotaICMS': f"{quote['aliquota_icms']}%"
                    })
            
            # Clean up
            os.remove(filepath)
            
            return jsonify({'data': results})
        
        except Exception as e:
            return jsonify({'error': f'Erro ao processar arquivo: {str(e)}'}), 500
    
    return jsonify({'error': 'Tipo de arquivo não permitido'}), 400

def calculate_freight(cep_origem, cep_destino, peso, valor_nf, volume, transportadora):
    """Simulate freight calculation (replace with actual API calls)"""
    # This is just a placeholder - implement your actual freight calculation logic
    base_value = (peso * 1.5) + (volume * 0.8)
    distance_factor = abs(int(cep_origem[:5]) - int(cep_destino[:5])) / 10000
    
    # Simulate different values per carrier
    if transportadora == 'JADLOG':
        valor = base_value * (0.9 + distance_factor)
        prazo = max(2, min(5, int(distance_factor * 10)))
    elif transportadora == 'CORREIOS':
        valor = base_value * (0.7 + distance_factor * 1.2)
        prazo = max(3, min(10, int(distance_factor * 15)))
    else:
        valor = base_value * (1.0 + distance_factor * 0.8)
        prazo = max(4, min(8, int(distance_factor * 12)))
    
    # Calculate ICMS (12% for simulation)
    aliquota_icms = 12
    icms = valor * (aliquota_icms / 100)
    
    return {
        'valor': round(valor, 2),
        'prazo': prazo,
        'icms': round(icms, 2),
        'aliquota_icms': aliquota_icms
    }

@app.route('/download-template')
def download_template():
    """Generate and serve a sample template file"""
    try:
        # Create a sample DataFrame with the required columns
        sample_data = {
            'Nota': ['EXEMPLO1', 'EXEMPLO2'],
            'Descricao': ['Produto A', 'Produto B'],
            'CEP_Origem': ['01001000', '02002000'],
            'CEP_Destino': ['80000000', '90000000'],
            'Peso': [1.5, 3.2],
            'Valor_NF': [150.00, 320.50],
            'Volume': [0.5, 1.2]
        }
        
        df = pd.DataFrame(sample_data)
        
        # Save to BytesIO
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Cotações')
        
        output.seek(0)
        
        return send_file(
            output,
            as_attachment=True,
            download_name='Modelo_Cotacao_Frete.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    except Exception as e:
        return jsonify({'error': f'Erro ao gerar template: {str(e)}'}), 500

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'xlsx', 'xls'}

if __name__ == '__main__':
    app.run(debug=True)
