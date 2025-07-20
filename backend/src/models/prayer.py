from src.models.user import db
from datetime import datetime

class Prayer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='to_pray')  # to_pray, in_progress, answered
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_private = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    answered_at = db.Column(db.DateTime, nullable=True)
    
    # Relations
    prayer_supports = db.relationship('PrayerSupport', backref='prayer', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Prayer {self.title}>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'author_id': self.author_id,
            'author': self.author.to_dict() if self.author else None,
            'is_private': self.is_private,
            'supports_count': len(self.prayer_supports),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'answered_at': self.answered_at.isoformat() if self.answered_at else None
        }

class PrayerSupport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    prayer_id = db.Column(db.Integer, db.ForeignKey('prayer.id'), nullable=False)
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    user = db.relationship('User', backref='prayer_supports')
    
    __table_args__ = (db.UniqueConstraint('user_id', 'prayer_id', name='unique_user_prayer_support'),)

    def __repr__(self):
        return f'<PrayerSupport {self.user_id}-{self.prayer_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user': self.user.to_dict() if self.user else None,
            'prayer_id': self.prayer_id,
            'message': self.message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

