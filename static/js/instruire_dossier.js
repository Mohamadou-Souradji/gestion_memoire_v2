// Modal Validation
function afficherModalValider() {
  document.getElementById('modalValider').classList.add('show');
}

function fermerModalValider() {
  document.getElementById('modalValider').classList.remove('show');
}

// Modal Rejet
function afficherModalRejeter() {
  document.getElementById('modalRejeter').classList.add('show');
}

function fermerModalRejeter() {
  document.getElementById('modalRejeter').classList.remove('show');
}

// Afficher image en grand
function afficherImageGrande(imageSrc, titre) {
  const modal = document.getElementById('modalImage');
  const imgLarge = document.getElementById('imageLarge');
  const imgTitre = document.getElementById('imageTitre');
  
  imgLarge.src = imageSrc;
  imgTitre.textContent = titre;
  modal.classList.add('show');
}

// Fermer image en grand
function fermerImageGrande() {
  document.getElementById('modalImage').classList.remove('show');
}

// Fermer la modal en appuyant sur Échap
document.addEventListener('keydown', function(event) {
  if (event.key === 'Escape') {
    fermerImageGrande();
  }
});
