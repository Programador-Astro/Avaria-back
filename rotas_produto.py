from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models import db, Product

products_bp = Blueprint('products', __name__)



# Domínios permitidos baseados na regra de negócio
VALID_FRANQUIAS = ["DG", "NTZ", "SMO", "MON"]
VALID_EMBALAGENS = ["CX10L", "PK6", "CX5L", "BAL3.6L", "PICOLE", "PALETA", "500ML"]

@products_bp.route('/', methods=['POST'])
@jwt_required()
def create_product():
    data = request.get_json()
    name = data.get('name')
    
    if not name:
        return jsonify({"error": "O nome do produto é obrigatório"}), 400
        
    if Product.query.filter_by(name=name).first():
        return jsonify({"error": "Produto já cadastrado"}), 400

        # Validando se a franquia enviada é permitida
    franquia = data['franquia'].upper()
    if franquia not in VALID_FRANQUIAS:
        return jsonify({"error": f"Franquia inválida. Escolha entre: {', '.join(VALID_FRANQUIAS)}"}), 400

    # Validando se a embalagem enviada é permitida
    embalagem = data['embalagem'].upper()
    if embalagem not in VALID_EMBALAGENS:
        return jsonify({"error": f"Embalagem inválida. Escolha entre: {', '.join(VALID_EMBALAGENS)}"}), 400

    new_product = Product(name=name, franquia=data.get('franquia'), embalagem=data.get('embalagem'))
    db.session.add(new_product)
    db.session.commit()
    
    return jsonify({"message": "Produto cadastrado com sucesso", "id": new_product.id}), 201

@products_bp.route('/', methods=['GET'])
@jwt_required()
def list_products():
    products = Product.query.all()
    resultado = [{"id": p.id, "name": p.name, "franquia": p.franquia, "embalagem": p.embalagem} for p in products]
    return jsonify(resultado), 200


import pandas as pd
from flask import Blueprint, request, jsonify
from models import db, Product  # Ajuste conforme a importação do seu modelo


@products_bp.route('/upload', methods=['POST'])
def upload_products_excel():
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "Nome de arquivo inválido"}), 400
        
    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({"error": "Apenas arquivos Excel (.xlsx ou .xls) são permitidos"}), 400

    try:
        # Lê o arquivo Excel enviado
        df = pd.read_excel(file)
        
        # Valida se as colunas da imagem existem no arquivo
        colunas_necessarias = ['Código', 'Franquia', 'Embalagem', 'Descrição']
        for coluna in colunas_necessarias:
            if coluna not in df.columns:
                return jsonify({"error": f"Coluna obrigatória ausente na planilha: '{coluna}'"}), 400

        importados = 0
        
        for _, row in df.iterrows():
            # Converte os valores para string e trata possíveis nulos
            cod_peform = str(row['Código']).strip()
            franquia = str(row['Franquia']).strip()
            embalagem = str(row['Embalagem']).strip()
            descricao = str(row['Descrição']).strip()

            if not cod_peform or cod_peform == 'nan':
                continue

            # Verifica se o produto já existe (para atualizar ou criar)
            product = Product.query.filter_by(cod_peform=cod_peform).first()
            
            if product:
                product.franquia = franquia
                product.embalagem = embalagem
                product.name = descricao
            else:
                novo_produto = Product(
                    cod_peform=cod_peform,
                    franquia=franquia,
                    embalagem=embalagem,
                    name=descricao
                )
                db.session.add(novo_produto)
            
            importados += 1

        db.session.commit()
        return jsonify({"message": f"Sucesso! {importados} produtos processados e salvos."}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro ao processar planilha: {str(e)}"}), 500