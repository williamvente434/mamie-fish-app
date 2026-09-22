import os, requests
from flask import Flask, render_template, request, jsonify, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# --- BASE DE DONNÉES ---
db_url = os.environ.get('DATABASE_URL', 'sqlite:///mamie_fish.db')
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Commande(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client = db.Column(db.String(100), nullable=False)
    telephone = db.Column(db.String(20), nullable=False)
    adresse = db.Column(db.String(200))
    plat = db.Column(db.String(100), nullable=False)
    quantite = db.Column(db.Integer, nullable=False)
    prix_total = db.Column(db.Integer, nullable=False)
    statut = db.Column(db.String(20), default='en_attente') # en_attente, payee, prete, livree
    date = db.Column(db.DateTime, default=datetime.utcnow)
    transaction_id = db.Column(db.String(100))

with app.app_context():
    db.create_all()

MENU = [
    {"id": 1, "nom": "Poulet DG", "desc": "Poulet bien grillé, accompagnement maison", "prix": 5000, "cat": "poulet"},
    {"id": 2, "nom": "Poisson Braisé", "desc": "Poisson frais et savoureux", "prix": 4500, "cat": "poisson"},
    {"id": 3, "nom": "Eru", "desc": "Plat traditionnel du pays", "prix": 3000, "cat": "tradition"},
    {"id": 4, "nom": "Riz Sauté", "desc": "Riz parfumé aux légumes", "prix": 2500, "cat": "riz"},
    {"id": 5, "nom": "Salade Mixte", "desc": "Légumes frais et goûté", "prix": 2200, "cat": "salade"}
]

@app.route('/')
def index():
    return render_template('index.html', plats=MENU, public_key=os.environ.get('NOTCHPAY_PUBLIC_KEY'))

@app.route('/api/menu')
def get_menu():
    return jsonify(MENU)

@app.route('/admin')
def admin():
    commandes = Commande.query.order_by(Commande.date.desc()).all()
    total_commandes = len(commandes)
    total_revenu = sum(c.prix_total or 0 for c in commandes)
    en_attente = sum(1 for c in commandes if c.statut == 'en_attente')
    livrees = sum(1 for c in commandes if c.statut == 'livree')
    paiement_cash = sum(1 for c in commandes if c.statut == 'payee')

    return render_template(
        'admin.html',
        commandes=commandes,
        total_commandes=total_commandes,
        total_revenu=total_revenu,
        en_attente=en_attente,
        livrees=livrees,
        paiement_cash=paiement_cash
    )

@app.route('/api/commander', methods=['POST'])
def commander():
    data = request.json
    prix_unitaire = next((item['prix'] for item in MENU if item['nom'] == data['plat']), 0)
    prix_total = prix_unitaire * int(data['quantite'])
    
    nouvelle_commande = Commande(
        client=data['client'], telephone=data['telephone'],
        adresse=data['adresse'], plat=data['plat'],
        quantite=data['quantite'], prix_total=prix_total
    )
    db.session.add(nouvelle_commande)
    db.session.commit()

    # Création paiement NotchPay
    try:
        secret = os.environ.get('NOTCHPAY_SECRET_KEY')
        if secret:
            headers = {"Authorization": secret, "Content-Type": "application/json"}
            payload = {
                "email": f"{data['telephone']}@mamiefish.cm",
                "amount": prix_total,
                "currency": "XAF",
                "description": f"Commande {data['plat']} x{data['quantite']}",
                "reference": f"CMD-{nouvelle_commande.id}",
                "callback": os.environ.get('NOTCHPAY_CALLBACK')
            }
            r = requests.post("https://api.notchpay.co/payments/initialize", json=payload, headers=headers, timeout=10)
            if r.status_code in [200,201]:
                link = r.json().get('authorization_url') or r.json().get('payment',{}).get('authorization_url')
                return jsonify({"success": True, "payment_url": link, "id": nouvelle_commande.id})
    except Exception as e:
        print(f"Erreur NotchPay: {e}")

    return jsonify({"success": True, "payment_url": None, "id": nouvelle_commande.id})

@app.route('/callback')
def callback():
    # NotchPay te redirige ici après paiement
    return "Paiement reçu ! Merci. Mamie Fish vous appelle bientôt."

@app.route('/api/update/<int:id>', methods=['POST'])
def update(id):
    cmd = Commande.query.get_or_404(id)
    cmd.statut = request.json['statut']
    db.session.commit()
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True)