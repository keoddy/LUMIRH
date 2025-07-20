from flask import Blueprint, request, jsonify, session
from src.models.user import db, User
from src.models.group import Group, GroupMembership

groups_bp = Blueprint('groups', __name__)

def require_auth():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)

@groups_bp.route('/', methods=['GET'])
def get_groups():
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'Non authentifié'}), 401
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        my_groups = request.args.get('my_groups', 'false').lower() == 'true'
        
        if my_groups:
            # Récupérer les groupes dont l'utilisateur est membre
            user_group_ids = [membership.group_id for membership in user.group_memberships]
            query = Group.query.filter(Group.id.in_(user_group_ids))
        else:
            # Récupérer tous les groupes publics
            query = Group.query.filter_by(is_private=False)
        
        groups = query.order_by(Group.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'groups': [group.to_dict() for group in groups.items],
            'total': groups.total,
            'pages': groups.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@groups_bp.route('/', methods=['POST'])
def create_group():
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'Non authentifié'}), 401
        
        data = request.get_json()
        
        if not data.get('name'):
            return jsonify({'error': 'Le nom du groupe est requis'}), 400
        
        group = Group(
            name=data['name'],
            description=data.get('description', ''),
            image_url=data.get('image_url'),
            is_private=data.get('is_private', False),
            created_by=user.id
        )
        
        db.session.add(group)
        db.session.flush()  # Pour obtenir l'ID du groupe
        
        # Ajouter le créateur comme admin du groupe
        membership = GroupMembership(
            user_id=user.id,
            group_id=group.id,
            role='admin'
        )
        
        db.session.add(membership)
        db.session.commit()
        
        return jsonify({
            'message': 'Groupe créé avec succès',
            'group': group.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@groups_bp.route('/<int:group_id>', methods=['GET'])
def get_group(group_id):
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'Non authentifié'}), 401
        
        group = Group.query.get_or_404(group_id)
        
        # Vérifier si l'utilisateur peut voir ce groupe
        if group.is_private:
            membership = GroupMembership.query.filter_by(user_id=user.id, group_id=group_id).first()
            if not membership:
                return jsonify({'error': 'Accès refusé'}), 403
        
        return jsonify({'group': group.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@groups_bp.route('/<int:group_id>/join', methods=['POST'])
def join_group(group_id):
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'Non authentifié'}), 401
        
        group = Group.query.get_or_404(group_id)
        
        # Vérifier si l'utilisateur est déjà membre
        existing_membership = GroupMembership.query.filter_by(user_id=user.id, group_id=group_id).first()
        if existing_membership:
            return jsonify({'error': 'Vous êtes déjà membre de ce groupe'}), 400
        
        # Pour les groupes privés, il faudrait une logique d'invitation
        if group.is_private:
            return jsonify({'error': 'Ce groupe est privé'}), 403
        
        membership = GroupMembership(
            user_id=user.id,
            group_id=group_id,
            role='member'
        )
        
        db.session.add(membership)
        db.session.commit()
        
        return jsonify({
            'message': 'Vous avez rejoint le groupe avec succès',
            'membership': membership.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@groups_bp.route('/<int:group_id>/leave', methods=['POST'])
def leave_group(group_id):
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'Non authentifié'}), 401
        
        membership = GroupMembership.query.filter_by(user_id=user.id, group_id=group_id).first()
        if not membership:
            return jsonify({'error': 'Vous n\'êtes pas membre de ce groupe'}), 400
        
        # Empêcher le créateur de quitter son propre groupe
        group = Group.query.get(group_id)
        if group.created_by == user.id:
            return jsonify({'error': 'Le créateur ne peut pas quitter son propre groupe'}), 400
        
        db.session.delete(membership)
        db.session.commit()
        
        return jsonify({'message': 'Vous avez quitté le groupe avec succès'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@groups_bp.route('/<int:group_id>/members', methods=['GET'])
def get_group_members(group_id):
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'Non authentifié'}), 401
        
        group = Group.query.get_or_404(group_id)
        
        # Vérifier si l'utilisateur peut voir les membres
        if group.is_private:
            membership = GroupMembership.query.filter_by(user_id=user.id, group_id=group_id).first()
            if not membership:
                return jsonify({'error': 'Accès refusé'}), 403
        
        members = db.session.query(GroupMembership, User).join(User).filter(
            GroupMembership.group_id == group_id
        ).all()
        
        members_data = []
        for membership, member_user in members:
            member_data = member_user.to_dict()
            member_data['role'] = membership.role
            member_data['joined_at'] = membership.joined_at.isoformat() if membership.joined_at else None
            members_data.append(member_data)
        
        return jsonify({'members': members_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

