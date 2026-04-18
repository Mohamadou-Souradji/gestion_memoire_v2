import random
import string
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta


class User(AbstractUser):
    """Utilisateur ESCEP avec rôle et authentification 2FA."""

    ROLE_CHOICES = [
        ('etudiant',           'Étudiant'),
        ('chef_departement',   'Chef de département'),
        ('directeur_etudes',   'Directeur des études'),
        ('direction_generale', 'Direction générale'),
        ('jury',               'Membre du jury'),
        ('bibliotheque',       'Bibliothécaire'),
    ]

    role      = models.CharField(max_length=30, choices=ROLE_CHOICES, default='etudiant')
    email     = models.EmailField(unique=True)
    telephone = models.CharField(max_length=20, blank=True)

    USERNAME_FIELD  = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    class Meta:
        verbose_name          = "Utilisateur"
        verbose_name_plural   = "Utilisateurs"

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    def get_dashboard_url(self):
        routes = {
            'etudiant':           '/etudiant/',
            'chef_departement':   '/chef/',
            'directeur_etudes':   '/directeur/',
            'direction_generale': '/dg/',
            'jury':               '/jury/',
            'bibliotheque':       '/bibliotheque/',
        }
        return routes.get(self.role, '/')


class CodeOTP(models.Model):
    """Code à usage unique envoyé par e-mail pour la double authentification."""

    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='codes_otp')
    code       = models.CharField(max_length=6)
    cree_le    = models.DateTimeField(auto_now_add=True)
    utilise    = models.BooleanField(default=False)
    tentatives = models.PositiveSmallIntegerField(default=0)

    MAX_TENTATIVES  = 3
    DUREE_VALIDITE  = 10  # minutes

    class Meta:
        verbose_name = "Code OTP"
        ordering     = ['-cree_le']

    def est_valide(self):
        expiration = self.cree_le + timedelta(minutes=self.DUREE_VALIDITE)
        return (
            not self.utilise
            and self.tentatives < self.MAX_TENTATIVES
            and timezone.now() < expiration
        )

    def verifier(self, code_soumis):
        self.tentatives += 1
        if code_soumis == self.code and self.est_valide():
            self.utilise = True
            self.save()
            return True
        self.save()
        return False

    @classmethod
    def generer_pour(cls, user):
        """Invalide les anciens codes et génère un nouveau."""
        cls.objects.filter(user=user, utilise=False).update(utilise=True)
        code = ''.join(random.choices(string.digits, k=6))
        return cls.objects.create(user=user, code=code)

    def __str__(self):
        return f"OTP {self.code} — {self.user.username}"
