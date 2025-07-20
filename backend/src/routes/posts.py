from flask import Blueprint, request, jsonify, session
from src.models.user import db, User
from src.models.post import Post, PostLike, PostComment
from datetime import datetime

posts_bp = Blueprint('posts', __name__)

def require_auth():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)

@posts_bp.route('/', methods=['GET'])
def get_posts():
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'Non authentifié'}), 401
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        group_id = request.args.get('group_id', type=int)
        
        query = Post.query
        
        if group_id:
            query = query.filter_by(group_id=group_id)
        
        posts = query.order_by(Post.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'posts': [post.to_dict() for post in posts.items],
            'total': posts.total,
            'pages': posts.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@posts_bp.route('/', methods=['POST'])
def create_post():
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'Non authentifié'}), 401
        
        data = request.get_json()
        
        if not data.get('content'):
            return jsonify({'error': 'Le contenu est requis'}), 400
        
        post = Post(
            content=data['content'],
            image_url=data.get('image_url'),
            author_id=user.id,
            group_id=data.get('group_id')
        )
        
        db.session.add(post)
        db.session.commit()
        
        return jsonify({
            'message': 'Post créé avec succès',
            'post': post.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@posts_bp.route('/<int:post_id>', methods=['GET'])
def get_post(post_id):
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'Non authentifié'}), 401
        
        post = Post.query.get_or_404(post_id)
        return jsonify({'post': post.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@posts_bp.route('/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'Non authentifié'}), 401
        
        post = Post.query.get_or_404(post_id)
        
        if post.author_id != user.id:
            return jsonify({'error': 'Non autorisé'}), 403
        
        data = request.get_json()
        
        if 'content' in data:
            post.content = data['content']
        if 'image_url' in data:
            post.image_url = data['image_url']
        
        post.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Post mis à jour avec succès',
            'post': post.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@posts_bp.route('/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'Non authentifié'}), 401
        
        post = Post.query.get_or_404(post_id)
        
        if post.author_id != user.id:
            return jsonify({'error': 'Non autorisé'}), 403
        
        db.session.delete(post)
        db.session.commit()
        
        return jsonify({'message': 'Post supprimé avec succès'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@posts_bp.route('/<int:post_id>/like', methods=['POST'])
def like_post(post_id):
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'Non authentifié'}), 401
        
        post = Post.query.get_or_404(post_id)
        
        # Vérifier si l'utilisateur a déjà liké ce post
        existing_like = PostLike.query.filter_by(user_id=user.id, post_id=post_id).first()
        
        if existing_like:
            # Retirer le like
            db.session.delete(existing_like)
            message = 'Like retiré'
            liked = False
        else:
            # Ajouter le like
            like = PostLike(user_id=user.id, post_id=post_id)
            db.session.add(like)
            message = 'Post liké'
            liked = True
        
        db.session.commit()
        
        return jsonify({
            'message': message,
            'liked': liked,
            'likes_count': len(post.likes)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@posts_bp.route('/<int:post_id>/comments', methods=['GET'])
def get_post_comments(post_id):
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'Non authentifié'}), 401
        
        post = Post.query.get_or_404(post_id)
        comments = PostComment.query.filter_by(post_id=post_id).order_by(PostComment.created_at.asc()).all()
        
        return jsonify({
            'comments': [comment.to_dict() for comment in comments]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@posts_bp.route('/<int:post_id>/comments', methods=['POST'])
def add_comment(post_id):
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'Non authentifié'}), 401
        
        post = Post.query.get_or_404(post_id)
        data = request.get_json()
        
        if not data.get('content'):
            return jsonify({'error': 'Le contenu du commentaire est requis'}), 400
        
        comment = PostComment(
            content=data['content'],
            user_id=user.id,
            post_id=post_id
        )
        
        db.session.add(comment)
        db.session.commit()
        
        return jsonify({
            'message': 'Commentaire ajouté avec succès',
            'comment': comment.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

