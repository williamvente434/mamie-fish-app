from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mamie_fish.db'
db = SQLAlchemy(app)

# --- BASE DE DONNEES ---
class Commande(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom_client = db.Column(db.String(100))
    telephone = db.Column(db.String(20))
    heure_retrait = db.Column(db.String(10))
    plats = db.Column(db.Text) # JSON
    total = db.Column(db.Integer)
    paiement = db.Column(db.String(20)) # OM, MoMo, Cash
    statut = db.Column(db.String(20), default="En attente")
    date = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

MENU = [
    {"id":1, "nom":"Salade Mixte", "desc":"Avocat + oeuf", "prix":1500, "cat":"salade"},
    {"id":2, "nom":"Poulet Braisé 1/4", "desc":"Plantain + piment", "prix":3000, "cat":"poulet"},
    {"id":3, "nom":"Poulet Entier", "desc":"Pour 3-4 pers", "prix":11000, "cat":"poulet"},
    {"id":4, "nom":"Riz Sauté", "desc":"Légumes + poulet", "prix":2000, "cat":"riz"},
    {"id":5, "nom":"Riz + Sauce Ara", "desc":"Viande + plantain", "prix":2500, "cat":"riz"},
    {"id":6, "nom":"Poisson Braisé", "desc":"Maquereau + bobolo", "prix":3500, "cat":"poisson"},
    {"id":7, "nom":"Ndolé", "desc":"Crevettes + plantain", "prix":3000, "cat":"tradition"},
]

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/menu')
def get_menu():
    return jsonify(MENU)

@app.route('/api/commander', methods=['POST'])
def commander():
    data = request.json
    nouvelle = Commande(
        nom_client=data['nom'],
        telephone=data['tel'],
        heure_retrait=data['heure'],
        plats=json.dumps(data['cart']),
        total=data['total'],
        paiement=data['paiement']
    )
    db.session.add(nouvelle)
    db.session.commit()
    
    # SIMULATION PAIEMENT MOBILE MONEY
    if data['paiement'] != 'Cash':
        print(f" -> Paiement {data['paiement']} de {data['total']}F à initier pour {data['tel']}")
    
    return jsonify({"success":True, "id": nouvelle.id, "message": f"Commande #{nouvelle.id} reçue!"})

@app.route('/admin')
def admin():
    commandes = Commande.query.order_by(Commande.date.desc()).all()
    total_commandes = len(commandes)
    total_revenu = sum(c.total or 0 for c in commandes)
    en_attente = sum(1 for c in commandes if c.statut == 'En attente')
    livrees = sum(1 for c in commandes if c.statut == 'Livrée')
    paiement_cash = sum(1 for c in commandes if c.paiement == 'Cash')

    return render_template(
        'admin.html',
        commandes=commandes,
        total_commandes=total_commandes,
        total_revenu=total_revenu,
        en_attente=en_attente,
        livrees=livrees,
        paiement_cash=paiement_cash
    )

@app.route('/api/admin/update/<int:id>', methods=['POST'])
def update_statut(id):
    cmd = Commande.query.get(id)
    cmd.statut = request.json['statut']
    db.session.commit()
    return jsonify({"success":True})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)