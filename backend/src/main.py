import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS

# Import des modèles
from src.models.user import db
from src.models.post import Post, PostLike, PostComment
from src.models.group import Group, GroupMembership
from src.models.prayer import Prayer, PrayerSupport
from src.models.event import Event, EventAttendance
from src.models.message import Message

# Import des routes
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.posts import posts_bp
from src.routes.groups import groups_bp
from src.routes.prayers import prayers_bp
from src.routes.events import events_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Configuration CORS pour permettre les requêtes cross-origin
CORS(app, origins="*")

# Configuration de la base de données PostgreSQL
# Pour le développement local, on peut utiliser SQLite
# Pour la production, utiliser PostgreSQL
database_url = os.environ.get('DATABASE_URL', f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Enregistrement des blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(posts_bp, url_prefix='/api/posts')
app.register_blueprint(groups_bp, url_prefix='/api/groups')
app.register_blueprint(prayers_bp, url_prefix='/api/prayers')
app.register_blueprint(events_bp, url_prefix='/api/events')

# Initialisation de la base de données
db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

