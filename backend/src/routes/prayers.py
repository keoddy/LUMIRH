from flask import Blueprint, request, jsonify, session
from src.models.user import db, User
from src.models.prayer import Prayer, PrayerSupport
from datetime import datetime

prayers_bp = Blueprint('prayers', __name__)

def require_auth():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)

@prayers_bp.route('/', methods=['GET'])
def get_prayers():
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'Non authentifié'}), 401
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')
        my_prayers = request.args.get('my_prayers', 'false').lower() == 'true'
        
        query = Prayer.query
        
        if my_prayers:
            query = query.filter_by(author_id=user.id)
        else:
            # Afficher seulement les prières publiques ou celles de l'utilisateur
            query = query.filter(
                (Prayer.is_private == False) | (Prayer.author_id == user.id)
            )
        
        if status:
            query = query.filter_by(status=status)
        
        prayers = query.order_by(Prayer.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'prayers': [prayer.to_dict() for prayer in prayers.items],
            'total': prayers.total,
            'pages': prayers.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@prayers_bp.route('/', methods=['POST'])
def create_prayer():
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'Non authentifié'}), 401
        
        data = request.get_json()
        
        if not data.get('title') or not data.get('description'):
            return jsonify({'error': 'Le titre et la description sont requis'}), 400
        
        prayer = Prayer(
            title=data['title'],
            description=data['description'],
            author_id=user.id,
            is_private=data.get('is_private', False),
            status='to_pray'
        )
        
        db.session.add(prayer)
        db.session.commit()
        
        return jsonify({
            'message': 'Demande de prière créée avec succès',
            'prayer': prayer.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@prayers_bp.route('/<int:prayer_id>', methods=['GET'])
def get_prayer(prayer_id):
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'Non authentifié'}), 401
        
        prayer = Prayer.query.get_or_404(prayer_id)
        
        # Vérifier si l'utilisateur peut voir cette prière
        if prayer.is_private and prayer.author_id != user.id:
            return jsonify({'error': 'Accès refusé'}), 403
        
        return jsonify({'prayer': prayer.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@prayers_bp.route('/<int:prayer_id>', methods=['PUT'])
def update_prayer(prayer_id):
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'Non authentifié'}), 401
        
        prayer = Prayer.query.get_or_404(prayer_id)
        
        if prayer.author_id != user.id:
            return jsonify({'error': 'Non autorisé'}), 403
        
        data = request.get_json()
        
        if 'title' in data:
            prayer.title = data['title']
        if 'description' in data:
            prayer.description = data['description']
        if 'status' in data:
            prayer.status = data['status']
            if data['status'] == 'answered':
                prayer.answered_at = datetime.utcnow()
        if 'is_private' in data:
            prayer.is_private = data['is_private']
        
        prayer.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Demande de prière mise à jour avec succès',
            'prayer': prayer.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@prayers_bp.route('/<int:prayer_id>', methods=['DELETE'])
def delete_prayer(prayer_id):
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'Non authentifié'}), 401
        
        prayer = Prayer.query.get_or_404(prayer_id)
        
        if prayer.author_id != user.id:
            return jsonify({'error': 'Non autorisé'}), 403
        
        db.session.delete(prayer)
        db.session.commit()
        
        return jsonify({'message': 'Demande de prière supprimée avec succès'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@prayers_bp.route('/<int:prayer_id>/support', methods=['POST'])
def support_prayer(prayer_id):
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'Non authentifié'}), 401
        
        prayer = Prayer.query.get_or_404(prayer_id)
        
        # Vérifier si l'utilisateur peut voir cette prière
        if prayer.is_private and prayer.author_id != user.id:
            return jsonify({'error': 'Accès refusé'}), 403
        
        # Vérifier si l'utilisateur soutient déjà cette prière
        existing_support = PrayerSupport.query.filter_by(user_id=user.id, prayer_id=prayer_id).first()
        
        if existing_support:
            return jsonify({'error': 'Vous soutenez déjà cette prière'}), 400
        
        data = request.get_json()
        
        support = PrayerSupport(
            user_id=user.id,
            prayer_id=prayer_id,
            message=data.get('message', '')
        )
        
        db.session.add(support)
        db.session.commit()
        
        return jsonify({
            'message': 'Soutien ajouté avec succès',
            'support': support.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@prayers_bp.route('/<int:prayer_id>/supports', methods=['GET'])
def get_prayer_supports(prayer_id):
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'Non authentifié'}), 401
        
        prayer = Prayer.query.get_or_404(prayer_id)
        
        # Vérifier si l'utilisateur peut voir cette prière
        if prayer.is_private and prayer.author_id != user.id:
            return jsonify({'error': 'Accès refusé'}), 403
        
        supports = PrayerSupport.query.filter_by(prayer_id=prayer_id).order_by(PrayerSupport.created_at.desc()).all()
        
        return jsonify({
            'supports': [support.to_dict() for support in supports]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

