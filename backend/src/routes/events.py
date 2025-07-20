from flask import Blueprint, request, jsonify, session
from src.models.user import db, User
from src.models.event import Event, EventAttendance
from datetime import datetime

events_bp = Blueprint('events', __name__)

def require_auth():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)

@events_bp.route('/', methods=['GET'])
def get_events():
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'Non authentifié'}), 401
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        upcoming = request.args.get('upcoming', 'false').lower() == 'true'
        my_events = request.args.get('my_events', 'false').lower() == 'true'
        
        query = Event.query
        
        if my_events:
            # Événements créés par l'utilisateur ou auxquels il participe
            user_event_ids = [attendance.event_id for attendance in user.event_attendances]
            query = query.filter(
                (Event.created_by == user.id) | (Event.id.in_(user_event_ids))
            )
        else:
            # Événements publics seulement
            query = query.filter_by(is_public=True)
        
        if upcoming:
            query = query.filter(Event.start_date >= datetime.utcnow())
        
        events = query.order_by(Event.start_date.asc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'events': [event.to_dict() for event in events.items],
            'total': events.total,
            'pages': events.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@events_bp.route('/', methods=['POST'])
def create_event():
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'Non authentifié'}), 401
        
        data = request.get_json()
        
        required_fields = ['title', 'start_date']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Le champ {field} est requis'}), 400
        
        # Conversion de la date
        try:
            start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
            end_date = None
            if data.get('end_date'):
                end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'error': 'Format de date invalide'}), 400
        
        event = Event(
            title=data['title'],
            description=data.get('description', ''),
            location=data.get('location', ''),
            start_date=start_date,
            end_date=end_date,
            image_url=data.get('image_url'),
            is_public=data.get('is_public', True),
            created_by=user.id
        )
        
        db.session.add(event)
        db.session.flush()  # Pour obtenir l'ID de l'événement
        
        # Ajouter automatiquement le créateur comme participant
        attendance = EventAttendance(
            user_id=user.id,
            event_id=event.id,
            status='attending'
        )
        
        db.session.add(attendance)
        db.session.commit()
        
        return jsonify({
            'message': 'Événement créé avec succès',
            'event': event.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@events_bp.route('/<int:event_id>', methods=['GET'])
def get_event(event_id):
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'Non authentifié'}), 401
        
        event = Event.query.get_or_404(event_id)
        
        # Vérifier si l'utilisateur peut voir cet événement
        if not event.is_public:
            attendance = EventAttendance.query.filter_by(user_id=user.id, event_id=event_id).first()
            if not attendance and event.created_by != user.id:
                return jsonify({'error': 'Accès refusé'}), 403
        
        return jsonify({'event': event.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@events_bp.route('/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'Non authentifié'}), 401
        
        event = Event.query.get_or_404(event_id)
        
        if event.created_by != user.id:
            return jsonify({'error': 'Non autorisé'}), 403
        
        data = request.get_json()
        
        if 'title' in data:
            event.title = data['title']
        if 'description' in data:
            event.description = data['description']
        if 'location' in data:
            event.location = data['location']
        if 'start_date' in data:
            try:
                event.start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Format de date de début invalide'}), 400
        if 'end_date' in data:
            if data['end_date']:
                try:
                    event.end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
                except ValueError:
                    return jsonify({'error': 'Format de date de fin invalide'}), 400
            else:
                event.end_date = None
        if 'image_url' in data:
            event.image_url = data['image_url']
        if 'is_public' in data:
            event.is_public = data['is_public']
        
        event.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Événement mis à jour avec succès',
            'event': event.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@events_bp.route('/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'Non authentifié'}), 401
        
        event = Event.query.get_or_404(event_id)
        
        if event.created_by != user.id:
            return jsonify({'error': 'Non autorisé'}), 403
        
        db.session.delete(event)
        db.session.commit()
        
        return jsonify({'message': 'Événement supprimé avec succès'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@events_bp.route('/<int:event_id>/attend', methods=['POST'])
def attend_event(event_id):
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'Non authentifié'}), 401
        
        event = Event.query.get_or_404(event_id)
        
        # Vérifier si l'utilisateur peut voir cet événement
        if not event.is_public and event.created_by != user.id:
            return jsonify({'error': 'Accès refusé'}), 403
        
        data = request.get_json()
        status = data.get('status', 'attending')
        
        if status not in ['attending', 'maybe', 'not_attending']:
            return jsonify({'error': 'Statut invalide'}), 400
        
        # Vérifier si l'utilisateur a déjà une réponse
        existing_attendance = EventAttendance.query.filter_by(user_id=user.id, event_id=event_id).first()
        
        if existing_attendance:
            existing_attendance.status = status
            message = 'Statut de participation mis à jour'
        else:
            attendance = EventAttendance(
                user_id=user.id,
                event_id=event_id,
                status=status
            )
            db.session.add(attendance)
            message = 'Participation enregistrée'
        
        db.session.commit()
        
        return jsonify({'message': message}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@events_bp.route('/<int:event_id>/attendees', methods=['GET'])
def get_event_attendees(event_id):
    try:
        user = require_auth()
        if not user:
            return jsonify({'error': 'Non authentifié'}), 401
        
        event = Event.query.get_or_404(event_id)
        
        # Vérifier si l'utilisateur peut voir cet événement
        if not event.is_public:
            attendance = EventAttendance.query.filter_by(user_id=user.id, event_id=event_id).first()
            if not attendance and event.created_by != user.id:
                return jsonify({'error': 'Accès refusé'}), 403
        
        attendees = db.session.query(EventAttendance, User).join(User).filter(
            EventAttendance.event_id == event_id
        ).all()
        
        attendees_data = []
        for attendance, attendee_user in attendees:
            attendee_data = attendee_user.to_dict()
            attendee_data['status'] = attendance.status
            attendee_data['registered_at'] = attendance.registered_at.isoformat() if attendance.registered_at else None
            attendees_data.append(attendee_data)
        
        return jsonify({'attendees': attendees_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

