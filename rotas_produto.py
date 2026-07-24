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