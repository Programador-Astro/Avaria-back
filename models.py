from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    sector = db.Column(db.String(50), nullable=False)
    current_jti = db.Column(db.String(36), nullable=True)

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True) # Ex: Açaí Tradicional
    franquia = db.Column(db.String(50), nullable=False) # DG, NTZ, SMO, MON
    embalagem = db.Column(db.String(50), nullable=False) # CX10L, PK6, CX5L, BAL3.6L, PICOLE, PALETA, 500ML
    avarias = db.relationship('Avaria', backref='produto', lazy=True)

class Avaria(db.Model):
    __tablename__ = 'avarias'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    # Detalhes da ocorrência com os domínios definidos
    
    tipo_avaria = db.Column(db.String(100), nullable=False)
    motivo = db.Column(db.Text, nullable=False)
    quantidade = db.Column(db.Float, nullable=False)
    motorista = db.Column(db.String(150), nullable=True)
    
    status = db.Column(db.String(50), default='Pendente') 
    
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    resolved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    resolved_by = db.relationship('User', foreign_keys=[resolved_by_id])




class AvariaHistory(db.Model):
    __tablename__ = 'avaria_history'
    
    id = db.Column(db.Integer, primary_key=True)
    avaria_id = db.Column(db.Integer, db.ForeignKey('avarias.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False) # Ex: "Atualização de quantidade", "Alteração de produto"
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User')







