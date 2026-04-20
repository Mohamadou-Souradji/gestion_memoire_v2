// FONCTIONS MODALS PROPOSITIONS

function afficherModalValider(id, theme, etudiant) {
  document.getElementById('proposition-theme-valider').textContent = theme;
  document.getElementById('formValider').action = '/chef/proposition/' + id + '/';
  const modal = document.getElementById('modalValider');
  modal.style.display = 'flex';
}

function fermerModalValider() {
  document.getElementById('modalValider').style.display = 'none';
}

function afficherModalRejeter(id, theme, etudiant) {
  document.getElementById('proposition-theme-rejeter').textContent = theme;
  document.getElementById('proposition-etudiant-rejeter').textContent = etudiant;
  document.getElementById('formRejeter').action = '/chef/proposition/' + id + '/';
  const modal = document.getElementById('modalRejeter');
  modal.style.display = 'flex';
}

function fermerModalRejeter() {
  document.getElementById('modalRejeter').style.display = 'none';
}

// Fermer les modals au clic en dehors
document.getElementById('modalValider')?.addEventListener('click', function(e) {
  if (e.target === this) fermerModalValider();
});

document.getElementById('modalRejeter')?.addEventListener('click', function(e) {
  if (e.target === this) fermerModalRejeter();
});

// Fermer les modals avec Échap
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    fermerModalValider();
    fermerModalRejeter();
  }
});
