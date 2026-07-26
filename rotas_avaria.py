from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Avaria, Product, User, AvariaHistory
from sqlalchemy import func

avarias_bp = Blueprint('avarias', __name__)

@avarias_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard_stats():
    """Alimenta os cards superiores da tela de Home"""
    total_pendentes = Avaria.query.filter_by(status='Pendente').count()
    total_resolvidos = Avaria.query.filter_by(status='Dado Baixa').count()
    
    # Soma da quantidade total de avariass
    volume_total = db.session.query(func.sum(Avaria.quantidade)).scalar() or 0
    
    return jsonify({
        "pendentes": total_pendentes,
        "resolvidos": total_resolvidos,
        "volume_total": float(volume_total)
    }), 200

@avarias_bp.route('/', methods=['GET'])
@jwt_required()
def get_avarias():
    status_filter = request.args.get('status')
    franquia_filter = request.args.get('franquia')

    query = Avaria.query

    if status_filter:
        query = query.filter_by(status=status_filter)
    
    if franquia_filter:
        # Como franquia agora está na tabela Product, filtramos via join
        query = query.join(Product).filter(Product.franquia == franquia_filter)

    avarias = query.all()
    
    resultado = []
    for av in avarias:
        resultado.append({
            "id": av.id,
            "produto": av.produto.name,
            "franquia": av.produto.franquia,     # Buscado direto do produto
            "embalagem": av.produto.embalagem,   # Buscado direto do produto
            "tipo_avaria": av.tipo_avaria,
            "quantidade": av.quantidade,
            "status": av.status,
            "criado_por": av.created_by.name if av.created_by else "Desconhecido",
            "data_criacao": av.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })

    return jsonify(resultado), 200



@avarias_bp.route('/', methods=['POST'])
@jwt_required()
def create_avaria():
    data = request.get_json()
    user_id = get_jwt_identity()
    
    # Validação de campos obrigatórios
    required_fields = ['product_id', 'tipo_avaria', 'motivo', 'quantidade']
    for field in required_fields:
        if field not in data or data[field] is None:
            return jsonify({"error": f"O campo '{field}' é obrigatório."}), 400


    # Verifica se o produto existe
    product = Product.query.get(data['product_id'])
    if not product:
        return jsonify({"error": "Produto não encontrado."}), 404

    try:
        nova_avaria = Avaria(
            product_id=data['product_id'],
            tipo_avaria=data['tipo_avaria'],
            motivo=data['motivo'],
            quantidade=float(data['quantidade']),
            motorista=data.get('motorista'),
            created_by_id=user_id,
            status='Pendente'
        )
        
        db.session.add(nova_avaria)
        db.session.commit()
        
        return jsonify({
            "message": "Avaria registrada com sucesso",
            "id": nova_avaria.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400



@avarias_bp.route('/<int:id>/baixa', methods=['PATCH'])
@jwt_required()
def dar_baixa_avaria(id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    if not current_user or current_user.role != 'GERENTE':
        return jsonify({"error": "Acesso negado. Apenas gerentes podem dar baixa."}), 403
    
    avaria = Avaria.query.get(id)
    if not avaria:
        return jsonify({"error": "Avaria não encontrada."}), 404
        
    if avaria.status == 'Dado Baixa':
        return jsonify({"error": "Esta avaria já foi baixada anteriormente."}), 400

    try:
        avaria.status = 'Dado Baixa'
        avaria.resolved_by_id = user_id
        avaria.baixada_at = func.now()  # Marca a data de baixa
        db.session.commit()
        
        return jsonify({"message": "Baixa realizada com sucesso na avaria!"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400



@avarias_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_avaria_detail(id):
    """Retorna os detalhes completos de uma avaria específica"""
    avaria = Avaria.query.get_or_404(id)
    
    return jsonify({
        "id": avaria.id,
        "product_id": avaria.product_id,
        "produto": avaria.produto.name,
        "franquia": avaria.produto.franquia,
        "embalagem": avaria.produto.embalagem,
        "tipo_avaria": avaria.tipo_avaria,
        "motivo": avaria.motivo,
        "quantidade": avaria.quantidade,
        "motorista": avaria.motorista,
        "status": avaria.status,
        "criado_por": avaria.created_by.name if avaria.created_by else "Desconhecido",
        "resolvido_por": avaria.resolved_by.name if avaria.resolved_by else None,
        "data_criacao": avaria.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        "baixada_at": avaria.baixada_at.strftime('%Y-%m-%d %H:%M:%S') if avaria.baixada_at else None
    }), 200


@avarias_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_avaria(id):
    user_id = get_jwt_identity()
    avaria = Avaria.query.get_or_404(id)
    data = request.get_json()

    # Dicionário para guardar as mudanças detectadas
    changes = []

    # Compara cada campo enviado com o valor atual no banco
    new_product_id = data.get('product_id')
    if new_product_id and int(new_product_id) != avaria.product_id:
        old_prod_name = avaria.produto.name
        new_prod = Product.query.get(new_product_id)
        changes.append(f"Produto alterado de '{old_prod_name}' para '{new_prod.name if new_prod else 'Desconhecido'}'")
        avaria.product_id = int(new_product_id)

    new_tipo = data.get('tipo_avaria')
    if new_tipo and new_tipo != avaria.tipo_avaria:
        changes.append(f"Tipo de avaria alterado de '{avaria.tipo_avaria}' para '{new_tipo}'")
        avaria.tipo_avaria = new_tipo

    new_qtd = data.get('quantidade')
    if new_qtd is not None and float(new_qtd) != avaria.quantidade:
        changes.append(f"Quantidade alterada de {avaria.quantidade} para {float(new_qtd)}")
        avaria.quantidade = float(new_qtd)

    new_motorista = data.get('motorista')
    if new_motorista != avaria.motorista:
        changes.append(f"Motorista alterado de '{avaria.motorista or 'Nenhum'}' para '{new_motorista or 'Nenhum'}'")
        avaria.motorista = new_motorista

    new_motivo = data.get('motivo')
    if new_motivo and new_motivo != avaria.motivo:
        changes.append("O motivo/observação foi atualizado.")
        avaria.motivo = new_motivo

    try:
        # Se houver alterações, salvamos no histórico
        if changes:
            details_str = " | ".join(changes)
            history = AvariaHistory(
                avaria_id=avaria.id,
                user_id=user_id,
                action="Atualização de dados",
                details=details_str
            )
            db.session.add(history)
            
        db.session.commit()
        return jsonify({"message": "Avaria atualizada com sucesso!"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

    
@avarias_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_avaria(id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    if not current_user or current_user.role != 'GERENTE':
        return jsonify({"error": "Acesso negado. Apenas gerentes podem deletar."}), 403
    avaria = Avaria.query.get_or_404(id)

    try:
        db.session.delete(avaria)
        db.session.commit()
        return jsonify({"message": "Avaria excluída com sucesso!"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400



@avarias_bp.route('/<int:id>/history', methods=['GET'])
@jwt_required()
def get_avaria_history(id):
    history = AvariaHistory.query.filter_by(avaria_id=id).order_by(AvariaHistory.created_at.desc()).all()
    res = []
    for h in history:
        res.append({
            "id": h.id,
            "usuario": h.user.name if h.user else "Desconhecido",
            "acao": h.action,
            "detalhes": h.details,
            "data": h.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    return jsonify(res), 200




