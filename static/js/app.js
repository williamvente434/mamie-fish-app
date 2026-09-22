const sel = document.getElementById('plat');
const menuDiv = document.getElementById('menu');

MENU.forEach((p) => {
  const option = document.createElement('option');
  option.value = p.nom;
  option.textContent = `${p.nom} - ${p.prix} FCFA`;
  sel.appendChild(option);

  const row = document.createElement('div');
  row.className = 'plat';
  row.innerHTML = `
    <div>
      <b>${p.nom}</b>
      <small>${p.desc}</small>
    </div>
    <span>${p.prix} FCFA</span>
  `;
  menuDiv.appendChild(row);
});

document.getElementById('btn').onclick = async () => {
  const data = {
    client: document.getElementById('client').value,
    telephone: document.getElementById('telephone').value,
    adresse: document.getElementById('adresse').value,
    plat: document.getElementById('plat').value,
    quantite: document.getElementById('quantite').value
  };

  if (!data.client || !data.telephone) {
    alert('Mets nom et téléphone');
    return;
  }

  const msg = document.getElementById('msg');
  msg.textContent = 'Traitement...';

  try {
    const res = await fetch('/api/commander', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    const j = await res.json();

    if (j.payment_url) {
      window.location.href = j.payment_url;
    } else {
      msg.textContent = '✅ Commande reçue ! On t\'appelle bientôt. ID: ' + j.id;
    }
  } catch (e) {
    msg.textContent = 'Erreur réseau, réessaie';
  }
};
