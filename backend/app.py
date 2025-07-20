# backend/app.py

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json
import os
import psycopg2 # Import pour PostgreSQL
from psycopg2 import sql
from datetime import datetime # Pour gérer les dates

# Configuration de l'application
app = Flask(__name__, static_folder='static', static_url_path='')
# La clé secrète est toujours nécessaire pour les sessions Flask
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'une-cle-secrete-par-defaut-tres-faible') # Utiliser une variable d'environnement

# Initialisation CORS
CORS(app)

# --- Configuration et fonctions de base de données ---
# Lire l'URL de la DB depuis les variables d'environnement
# Render fournira cette variable automatiquement
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL non configurée.")
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def initialize_db():
    if not DATABASE_URL:
        print("AVERTISSEMENT: DATABASE_URL non configurée. L'initialisation de la base de données est ignorée.")
        return

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Créer la table users si elle n'existe pas
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL, -- En production, utilisez un hachage de mot de passe (bcrypt)
                nom VARCHAR(255),
                prenom VARCHAR(255),
                email VARCHAR(255),
                role VARCHAR(50)
            );
        """)

        # Créer la table employees si elle n'existe pas
        cur.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id SERIAL PRIMARY KEY,
                nom VARCHAR(255),
                prenom VARCHAR(255),
                email VARCHAR(255),
                poste VARCHAR(255),
                departement VARCHAR(255),
                telephone VARCHAR(255),
                date_embauche DATE,
                salaire DECIMAL,
                statut VARCHAR(50),
                missions TEXT,
                actifs TEXT,
                objectifs TEXT,
                competences TEXT,
                score_performance DECIMAL
            );
        """)

        # Insérer un utilisateur admin par défaut si la table users est vide
        cur.execute("SELECT COUNT(*) FROM users;")
        count = cur.fetchone()[0]
        if count == 0:
            # Note: En production, le mot de passe 'admin123' devrait être haché
            cur.execute("""
                INSERT INTO users (username, password, nom, prenom, email, role)
                VALUES (%s, %s, %s, %s, %s, %s);
            """, ('admin', 'admin123', 'Administrateur', 'SLOMAH', 'admin@slomah.com', 'admin'))
            print("Utilisateur admin par défaut créé.")

        conn.commit()
        print("Base de données initialisée avec succès.")

    except Exception as e:
        print(f"Erreur lors de l'initialisation de la base de données : {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

# Initialiser la base de données au démarrage de l'application
# Note: Dans un environnement de production, une migration de base de données est préférable
# mais pour cet exemple, l'initialisation au démarrage est suffisante.
initialize_db()

# Données en mémoire pour les sessions (simple, non persistant)
# ATTENTION: Les sessions seront perdues à chaque redémarrage du serveur.
# Pour une application de production, utilisez une gestion de session persistante (DB, Redis, JWT...)
sessions = {}

# --- Routes de l'application ---

# Route principale pour servir le frontend statique
@app.route('/')
def index():
    # Assurez-vous que le dossier 'static' existe et contient index.html
    return app.send_static_file('index.html')

# Route de connexion
@app.route('/api/auth/login', methods=['POST'])
def login():
    conn = None
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données manquantes'}), 400

        username = data.get('username', '').strip()
        password = data.get('password', '').strip() # En production, comparez avec le hachage stocké

        if not username or not password:
            return jsonify({'error': 'Nom d\'utilisateur et mot de passe requis'}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        # Vérification des identifiants dans la base de données
        # En production, utilisez une comparaison sécurisée pour le mot de passe haché
        cur.execute("SELECT id, username, nom, prenom, email, role FROM users WHERE username = %s AND password = %s;", (username, password))
        user_data = cur.fetchone() # (id, username, nom, prenom, email, role)

        if user_data:
            # Création d'une session simple (en mémoire)
            session_id = f"session_{user_data[1]}_" + os.urandom(16).hex() # Générer un ID unique
            sessions[session_id] = {
                'username': user_data[1],
                'user_data': {
                    'id': user_data[0],
                    'username': user_data[1],
                    'nom': user_data[2],
                    'prenom': user_data[3],
                    'nom_complet': f"{user_data[3]} {user_data[2]}",
                    'email': user_data[4],
                    'role': user_data[5]
                }
            }

            response = jsonify({'message': 'Connexion réussie', 'user': sessions[session_id]['user_data']})
            # secure=True en production si vous utilisez HTTPS
            response.set_cookie('session_id', session_id, httponly=True, secure=False)
            return response
        else:
            return jsonify({'error': 'Nom d\'utilisateur ou mot de passe incorrect'}), 401

    except Exception as e:
        print(f"Erreur de connexion: {e}")
        return jsonify({'error': f'Erreur serveur: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

# Route de vérification de session
@app.route('/api/auth/check-session', methods=['GET'])
def check_auth():
    try:
        session_id = request.cookies.get('session_id')
        if session_id and session_id in sessions:
            return jsonify({'authenticated': True, 'user': sessions[session_id]['user_data']})
        else:
            return jsonify({'authenticated': False}), 401
    except Exception as e:
        print(f"Erreur vérification auth: {e}")
        return jsonify({'authenticated': False, 'error': str(e)}), 500

# Route de déconnexion
@app.route('/api/auth/logout', methods=['POST'])
def logout():
    try:
        session_id = request.cookies.get('session_id')
        if session_id and session_id in sessions:
            del sessions[session_id]
        response = jsonify({'message': 'Déconnexion réussie'})
        response.set_cookie('session_id', '', expires=0)
        return response
    except Exception as e:
        print(f"Erreur déconnexion: {e}")
        return jsonify({'message': 'Erreur déconnexion', 'error': str(e)}), 500

# Route d'inscription
@app.route('/api/auth/register', methods=['POST'])
def register():
    conn = None
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données manquantes'}), 400
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        nom = data.get('nom', '').strip()
        prenom = data.get('prenom', '').strip()
        email = data.get('email', '').strip()
        role = data.get('role', 'user').strip()
        if not username or not password:
            return jsonify({'error': "Nom d'utilisateur et mot de passe requis"}), 400
        conn = get_db_connection()
        cur = conn.cursor()
        # Vérifier si l'utilisateur existe déjà
        cur.execute("SELECT id FROM users WHERE username = %s;", (username,))
        if cur.fetchone():
            return jsonify({'error': "Nom d'utilisateur déjà utilisé"}), 409
        # En production, hacher le mot de passe ici
        cur.execute("""
            INSERT INTO users (username, password, nom, prenom, email, role)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, username, nom, prenom, email, role;
        """, (username, password, nom, prenom, email, role))
        user_data = cur.fetchone()
        conn.commit()
        return jsonify({
            'message': 'Inscription réussie',
            'user': {
                'id': user_data[0],
                'username': user_data[1],
                'nom': user_data[2],
                'prenom': user_data[3],
                'email': user_data[4],
                'role': user_data[5]
            }
        }), 201
    except Exception as e:
        print(f"Erreur inscription: {e}")
        if conn:
            conn.rollback()
        return jsonify({'error': f'Erreur serveur: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

# Routes des employés
@app.route('/api/employees', methods=['GET'])
def get_employees():
    # Vérification simple de l'authentification via cookie (session en mémoire)
    session_id = request.cookies.get('session_id')
    if not session_id or session_id not in sessions:
        return jsonify({'error': 'Non authentifié'}), 401

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, nom, prenom, email, poste, departement, telephone, date_embauche, salaire, statut, missions, actifs, objectifs, competences, score_performance FROM employees;")
        # Récupérer les noms de colonnes pour créer une liste de dictionnaires
        column_names = [desc[0] for desc in cur.description]
        employees_list = []
        for row in cur.fetchall():
             employee = dict(zip(column_names, row))
             # Convertir les dates en string si nécessaire pour JSON
             if isinstance(employee.get('date_embauche'), datetime):
                 employee['date_embauche'] = employee['date_embauche'].isoformat()
             employees_list.append(employee)


        return jsonify(employees_list)

    except Exception as e:
        print(f"Erreur get employees: {e}")
        return jsonify({'error': f'Erreur serveur: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/employees', methods=['POST'])
def create_employee():
    # Vérification simple de l'authentification via cookie (session en mémoire)
    session_id = request.cookies.get('session_id')
    if not session_id or session_id not in sessions:
        return jsonify({'error': 'Non authentifié'}), 401

    conn = None
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données manquantes'}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        # Convertir la date d'embauche si elle est fournie
        date_embauche_str = data.get('date_embauche')
        date_embauche_obj = None
        if date_embauche_str:
            try:
                # Assurez-vous que le format de date correspond à ce que vous attendez (ex: YYYY-MM-DD)
                date_embauche_obj = datetime.strptime(date_embauche_str, '%Y-%m-%d').date()
            except ValueError:
                print(f"Format de date invalide: {date_embauche_str}")
                # Gérer l'erreur ou laisser date_embauche_obj à None

        # Insérer le nouvel employé dans la base de données
        cur.execute("""
            INSERT INTO employees (nom, prenom, email, poste, departement, telephone, date_embauche, salaire, statut, missions, actifs, objectifs, competences, score_performance)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            data.get('nom', ''),
            data.get('prenom', ''),
            data.get('email', ''),
            data.get('poste', ''),
            data.get('departement', ''),
            data.get('telephone', ''),
            date_embauche_obj, # Utiliser l'objet date ou None
            data.get('salaire', 0),
            data.get('statut', 'Actif'),
            data.get('missions', ''),
            data.get('actifs', ''),
            data.get('objectifs', ''),
            data.get('competences', ''),
            data.get('score_performance', 5)
        ))
        employee_id = cur.fetchone()[0]
        conn.commit()

        # Récupérer l'employé inséré pour le retourner dans la réponse
        cur.execute("SELECT id, nom, prenom, email, poste, departement, telephone, date_embauche, salaire, statut, missions, actifs, objectifs, competences, score_performance FROM employees WHERE id = %s;", (employee_id,))
        column_names = [desc[0] for desc in cur.description]
        new_employee_row = cur.fetchone()
        new_employee = dict(zip(column_names, new_employee_row))
        if isinstance(new_employee.get('date_embauche'), datetime):
             new_employee['date_embauche'] = new_employee['date_embauche'].isoformat()


        return jsonify({
            'message': 'Employé créé avec succès',
            'employee': new_employee
        })

    except Exception as e:
        print(f"Erreur création employé: {e}")
        if conn:
            conn.rollback()
        return jsonify({'error': f'Erreur serveur: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()


# Route de chat IA simplifiée (les réponses sont maintenant basées sur les données de la DB)
@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    # Vérification simple de l'authentification via cookie (session en mémoire)
    session_id = request.cookies.get('session_id')
    if not session_id or session_id not in sessions:
        return jsonify({'error': 'Non authentifié'}), 401

    conn = None
    try:
        data = request.get_json()
        message = data.get('message', '').lower()
        response_text = "Je suis votre assistant IA pour SLOMAH ACT 1. Posez-moi des questions sur les performances, l\'équipe, ou demandez un rapport !" # Réponse par défaut

        conn = get_db_connection()
        cur = conn.cursor()

        # Réponses basées sur les données de la DB
        if 'performance' in message or 'performances' in message:
            cur.execute("SELECT COUNT(*) FROM employees;")
            nb_employes = cur.fetchone()[0]
            cur.execute("SELECT AVG(score_performance) FROM employees;")
            perf_moyenne = cur.fetchone()[0] or 0 # Gérer le cas où il n'y a pas d'employés
            response_text = f'Voici un résumé des performances : Vous avez {nb_employes} employé(s). La performance moyenne est de {perf_moyenne:.2f}.'

        elif 'équipe' in message or 'equipe' in message:
             cur.execute("SELECT COUNT(*) FROM employees;")
             nb_employes = cur.fetchone()[0]
             response_text = f'Votre équipe compte actuellement {nb_employes} employé(s) enregistré(s).'

        elif 'rapport' in message:
            # Ici, on pourrait générer un rapport plus complexe en interrogeant la DB
            response_text = 'Rapport généré : Performances globales satisfaisantes. Tous les employés sont actifs (basé sur les données disponibles).' # Exemple simple

        elif 'aide' in message:
            response_text = 'Je peux vous aider avec l\'analyse des performances, la gestion d\'équipe, et les rapports. Posez-moi vos questions !'

        elif 'hello' in message or 'bonjour' in message:
            response_text = 'Bonjour ! Comment puis-je vous aider avec la gestion de votre équipe SLOMAH ACT 1 ?'

        # Note: L'intégration d'un modèle IA réel (OpenAI, etc.) pour des réponses plus dynamiques
        # nécessiterait d'appeler une API externe ici, en utilisant une clé API sécurisée
        # via les variables d'environnement.

        return jsonify({'response': response_text})

    except Exception as e:
        print(f"Erreur IA: {e}")
        return jsonify({'error': f'Erreur serveur IA: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

# Route pour le traitement des fichiers (à implémenter avec l'analyse)
# Cette route devra lire le fichier uploadé, le parser, analyser les données
# et potentiellement mettre à jour la base de données des employés ou générer des rapports.
# L'intégration de bibliothèques comme pandas, openpyxl, PyPDF2, python-docx, etc.
# sera nécessaire ici.
@app.route('/api/files/upload', methods=['POST'])
def upload_file():
     # Vérification simple de l'authentification via cookie (session en mémoire)
    session_id = request.cookies.get('session_id')
    if not session_id or session_id not in sessions:
        return jsonify({'error': 'Non authentifié'}), 401

    # Le code de traitement de fichier de l'exemple précédent (avec multer côté Node.js)
    # doit être adapté ici pour Flask. Flask utilise request.files.
    # L'analyse et l'interprétation des fichiers (Excel, CSV, PDF, etc.)
    # est une fonctionnalité complexe qui nécessite une implémentation détaillée ici.
    # Vous devrez lire le fichier (request.files['file']), déterminer son type,
    # utiliser la bibliothèque appropriée pour le parser, puis traiter les données.

    return jsonify({'message': 'Route d\'upload de fichier à implémenter'})


# Route de test (mise à jour pour refléter l'utilisation de la DB)
@app.route('/api/test', methods=['GET'])
def test():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users;")
        nb_users = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM employees;")
        nb_employees = cur.fetchone()[0]

        return jsonify({
            'message': 'SLOMAH ACT 1 - API fonctionnelle (connectée à la DB)',
            'status': 'OK',
            'users_count_in_db': nb_users,
            'employees_count_in_db': nb_employees,
            'active_sessions_in_memory': len(sessions) # Les sessions sont toujours en mémoire
        })
    except Exception as e:
        print(f"Erreur test: {e}")
        return jsonify({
            'message': 'SLOMAH ACT 1 - API Erreur (problème DB?)',
            'status': 'Error',
            'error': str(e)
        }), 500
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    # En local, vous pouvez définir DATABASE_URL manuellement pour tester
    # Exemple (pour une DB locale): os.environ['DATABASE_URL'] = 'postgresql://user:password@host:port/database_name'
    # Assurez-vous d'avoir une DB PostgreSQL qui tourne et les identifiants corrects.
    # Pour Render, cette variable sera configurée automatiquement.
    if not DATABASE_URL:
         print("AVERTISSEMENT: DATABASE_URL n'est pas définie. L'application ne pourra pas se connecter à la base de données.")
         print("Veuillez définir la variable d'environnement DATABASE_URL pour le déploiement.")
         # En local pour le développement sans DB, vous pourriez commenter la ligne initialize_db()
         # et utiliser les listes/dictionnaires en mémoire comme avant, mais ce code est fait pour la DB.


    # Le port 5000 est souvent utilisé pour Flask en local, mais Render utilisera un port défini par l'environnement
    PORT = int(os.environ.get('PORT', 5000))
    # debug=True est utile en développement, mais doit être False en production pour la sécurité et la performance
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
