from flask import Blueprint, request, jsonify, session
from src.models.user import db, User, InvitationCode
from datetime import datetime
import secrets
import string

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Vérification des champs requis
        required_fields = ['email', 'password', 'first_name', 'last_name', 'username', 'invitation_code']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Le champ {field} est requis'}), 400
        
        # Vérification du code d'invitation
        invitation = InvitationCode.query.filter_by(code=data['invitation_code'], is_used=False).first()
        if not invitation:
            return jsonify({'error': 'Code d\'invitation invalide ou déjà utilisé'}), 400
        
        # Vérification si l'email existe déjà
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Cet email est déjà utilisé'}), 400
        
        # Vérification si le nom d'utilisateur existe déjà
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Ce nom d\'utilisateur est déjà pris'}), 400
        
        # Création du nouvel utilisateur
        user = User(
            email=data['email'],
            username=data['username'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            bio=data.get('bio', '')
        )
        user.set_password(data['password'])
        
        # Marquer le code d'invitation comme utilisé
        invitation.is_used = True
        invitation.used_by = user.id
        invitation.used_at = datetime.utcnow()
        
        db.session.add(user)
        db.session.commit()
        
        # Mettre à jour l'invitation avec l'ID utilisateur
        invitation.used_by = user.id
        db.session.commit()
        
        # Connexion automatique après inscription
        session['user_id'] = user.id
        
        return jsonify({
            'message': 'Inscription réussie',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email et mot de passe requis'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Email ou mot de passe incorrect'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Compte désactivé'}), 401
        
        session['user_id'] = user.id
        
        return jsonify({
            'message': 'Connexion réussie',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Déconnexion réussie'}), 200

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Non authentifié'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/generate-invitation', methods=['POST'])
def generate_invitation():
    try:
        # Vérifier si l'utilisateur est connecté et autorisé
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Non authentifié'}), 401
        
        # Générer un code d'invitation unique
        code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        
        # Vérifier l'unicité du code
        while InvitationCode.query.filter_by(code=code).first():
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        
        invitation = InvitationCode(code=code)
        db.session.add(invitation)
        db.session.commit()
        
        return jsonify({
            'message': 'Code d\'invitation généré',
            'invitation': invitation.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/validate-invitation', methods=['POST'])
def validate_invitation():
    try:
        data = request.get_json()
        code = data.get('code')
        
        if not code:
            return jsonify({'error': 'Code d\'invitation requis'}), 400
        
        invitation = InvitationCode.query.filter_by(code=code, is_used=False).first()
        
        if invitation:
            return jsonify({'valid': True, 'message': 'Code d\'invitation valide'}), 200
        else:
            return jsonify({'valid': False, 'message': 'Code d\'invitation invalide ou déjà utilisé'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

