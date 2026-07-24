from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from flask import make_response
import uuid
from models import db, User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if User.query.filter_by(name=data['name']).first():
        return jsonify({"error": "Usuário já existe"}), 400
        
    hashed_password = generate_password_hash(data['password'])
    
    new_user = User(
        name=data['name'],
        password_hash=hashed_password,
        role=data['role'],
        sector=data.get('sector', 'geral')
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"message": "Usuário criado com sucesso"}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(name=data['name']).first()
    
    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({"error": "Credenciais inválidas"}), 401
        
    jti = str(uuid.uuid4())
    user.current_jti = jti
    db.session.commit()
    
    access_token = create_access_token(identity=str(user.id), additional_claims={"jti": jti})
    
    # O JSON retorna estritamente os dados de roteamento
    response = make_response(jsonify({
        "role": user.role,
        "sector": user.sector,
        "name": user.name
    }))
    
    # O token viaja seguro no cabeçalho
    response.headers['X-Access-Token'] = access_token
    
    return response, 200