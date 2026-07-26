import os
from flask import Flask
from models import User
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from auth import auth_bp
from rotas_avaria import avarias_bp
from rotas_produto import products_bp
from models import db
from flask_cors import CORS

import os
from dotenv import load_dotenv
load_dotenv()  # Carrega variáveis de ambiente do arquivo .env

migrate = Migrate()

def create_app():
    app = Flask(__name__)

    CORS(app, resources={r"/api/*": {"origins": f"{os.getenv('FRONTEND_URL', 'http://localhost:5137')}"}} , supports_credentials=True,
    expose_headers=["X-Access-Token"])

    # Configurações do Banco e JWT
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL',)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY') 
    db.init_app(app)
    migrate.init_app(app, db)
  
    jwt = JWTManager(app)

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        user_id = jwt_payload["sub"]
        token_jti = jwt_payload["jti"]
        
        user = User.query.get(user_id)

        # Se o usuário não existir ou o JTI do token não bater com o banco, bloqueia o acesso
        if not user or user.current_jti != token_jti:
            return True # True significa que o token está revogado/bloqueado
            
        return False

    # Registro do Blueprint de autenticação
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(avarias_bp, url_prefix='/api/avarias')
    app.register_blueprint(products_bp, url_prefix='/api/products')
    @app.route('/')
    def index():
        return {"status": "Sistema de Avarias rodando!"}, 200
        
    return app


app = create_app()

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)

