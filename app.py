"""
API Recettes de cuisine
Auteur : Grâce Destinée LEBIKI LAVANYA
Description : API REST pour gérer des recettes de cuisine
              Base de données SQLite intégrée
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app)

DB_PATH = os.path.join(os.path.dirname(__file__), 'recettes.db')

# ── BASE DE DONNÉES ──
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS recettes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nom         TEXT    NOT NULL,
            description TEXT,
            ingredients TEXT    NOT NULL,
            etapes      TEXT    NOT NULL,
            temps       INTEGER,
            difficulte  TEXT    DEFAULT 'Facile',
            categorie   TEXT    DEFAULT 'Plat principal'
        )
    ''')
    # Données de départ
    c.execute("SELECT COUNT(*) FROM recettes")
    if c.fetchone()[0] == 0:
        recettes_initiales = [
            ("Pâtes carbonara", "Un classique italien crémeux", "Pâtes, lardons, œufs, parmesan, poivre", "1. Cuire les pâtes\n2. Faire revenir les lardons\n3. Mélanger œufs et parmesan\n4. Mélanger hors feu", 20, "Facile", "Plat principal"),
            ("Salade niçoise", "Salade fraîche du sud de la France", "Thon, œufs, tomates, olives, haricots verts, anchois", "1. Cuire les œufs durs\n2. Cuire les haricots verts\n3. Assembler tous les ingrédients\n4. Assaisonner", 25, "Facile", "Entrée"),
            ("Tarte aux pommes", "Dessert traditionnel français", "Pâte brisée, pommes, sucre, beurre, cannelle", "1. Étaler la pâte\n2. Éplucher et couper les pommes\n3. Disposer les pommes\n4. Cuire 35min à 180°C", 60, "Moyen", "Dessert"),
            ("Poulet rôti", "Le grand classique du dimanche", "Poulet entier, herbes, ail, beurre, citron", "1. Préparer le poulet\n2. Badigeonner de beurre et herbes\n3. Cuire 1h à 200°C\n4. Laisser reposer 10min", 80, "Facile", "Plat principal"),
            ("Soupe à l'oignon", "Soupe gratinée réconfortante", "Oignons, bouillon de bœuf, pain, gruyère, beurre", "1. Caraméliser les oignons\n2. Ajouter le bouillon\n3. Faire gratiner avec pain et gruyère", 45, "Facile", "Entrée"),
        ]
        c.executemany("INSERT INTO recettes (nom, description, ingredients, etapes, temps, difficulte, categorie) VALUES (?,?,?,?,?,?,?)", recettes_initiales)
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def recette_to_dict(r):
    return {
        'id': r['id'],
        'nom': r['nom'],
        'description': r['description'],
        'ingredients': r['ingredients'].split(', '),
        'etapes': r['etapes'].split('\n'),
        'temps': r['temps'],
        'difficulte': r['difficulte'],
        'categorie': r['categorie']
    }

# ════════════════════════════════════
#   ROUTES
# ════════════════════════════════════

# GET / → Info API
@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'message': 'API Recettes — Grâce Destinée LEBIKI LAVANYA',
        'version': '1.0',
        'routes': {
            'GET  /recettes':              'Toutes les recettes',
            'GET  /recettes/<id>':         'Une recette par ID',
            'GET  /recettes/search?q=...': 'Recherche par nom',
            'POST /recettes':              'Ajouter une recette',
            'DELETE /recettes/<id>':       'Supprimer une recette'
        }
    }), 200

# GET /recettes → Toutes les recettes
@app.route('/recettes', methods=['GET'])
def get_recettes():
    categorie = request.args.get('categorie')
    conn = get_db()
    if categorie:
        rows = conn.execute('SELECT * FROM recettes WHERE categorie = ? ORDER BY id', (categorie,)).fetchall()
    else:
        rows = conn.execute('SELECT * FROM recettes ORDER BY id').fetchall()
    conn.close()
    return jsonify([recette_to_dict(r) for r in rows]), 200

# GET /recettes/search?q=... → Recherche
@app.route('/recettes/search', methods=['GET'])
def search_recettes():
    q = request.args.get('q', '')
    if not q:
        return jsonify({'erreur': 'Paramètre q requis'}), 400
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM recettes WHERE nom LIKE ? OR ingredients LIKE ?',
        (f'%{q}%', f'%{q}%')
    ).fetchall()
    conn.close()
    return jsonify([recette_to_dict(r) for r in rows]), 200

# GET /recettes/<id> → Une recette
@app.route('/recettes/<int:id>', methods=['GET'])
def get_recette(id):
    conn = get_db()
    r = conn.execute('SELECT * FROM recettes WHERE id = ?', (id,)).fetchone()
    conn.close()
    if not r:
        return jsonify({'erreur': 'Recette introuvable'}), 404
    return jsonify(recette_to_dict(r)), 200

# POST /recettes → Ajouter
@app.route('/recettes', methods=['POST'])
def add_recette():
    data = request.get_json()
    champs = ['nom', 'ingredients', 'etapes']
    for c in champs:
        if not data or c not in data or not data[c]:
            return jsonify({'erreur': f'Champ obligatoire manquant : {c}'}), 400

    conn = get_db()
    cursor = conn.execute(
        'INSERT INTO recettes (nom, description, ingredients, etapes, temps, difficulte, categorie) VALUES (?,?,?,?,?,?,?)',
        (
            data['nom'],
            data.get('description', ''),
            data['ingredients'] if isinstance(data['ingredients'], str) else ', '.join(data['ingredients']),
            data['etapes'] if isinstance(data['etapes'], str) else '\n'.join(data['etapes']),
            data.get('temps', 0),
            data.get('difficulte', 'Facile'),
            data.get('categorie', 'Plat principal')
        )
    )
    conn.commit()
    new_id = cursor.lastrowid
    r = conn.execute('SELECT * FROM recettes WHERE id = ?', (new_id,)).fetchone()
    conn.close()
    return jsonify(recette_to_dict(r)), 201

# DELETE /recettes/<id> → Supprimer
@app.route('/recettes/<int:id>', methods=['DELETE'])
def delete_recette(id):
    conn = get_db()
    r = conn.execute('SELECT * FROM recettes WHERE id = ?', (id,)).fetchone()
    if not r:
        conn.close()
        return jsonify({'erreur': 'Recette introuvable'}), 404
    conn.execute('DELETE FROM recettes WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'message': f'Recette "{r["nom"]}" supprimée'}), 200

# ── LANCEMENT ──
init_db()

if __name__ == '__main__':
    print("🍽️ API Recettes démarrée sur http://localhost:5000")
    app.run(debug=True, port=5000)
