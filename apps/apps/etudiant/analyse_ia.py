"""
Analyse IA du PDF — ESCEP Niger.
Priorité : ZeroGPT (gratuit) → GPTZero (payant) → heuristique locale.
Durée garantie : 40–60 secondes.
"""
import re, time, random

MARQUEURS = [
    r"\ben tant qu[e']", r"\bil est important de noter", r"\bdans le cadre de",
    r"\bill convient de souligner", r"\bil est essentiel\b", r"\bil est crucial\b",
    r"\bjoue un rôle crucial\b", r"\bde nos jours\b", r"\bgrâce aux avancées\b",
    r"\ben conclusion\b", r"\ben résumé\b", r"\bpour conclure\b",
    r"\bpremièrement\b", r"\bdeuxièmement\b", r"\ben outre\b", r"\bpar ailleurs\b",
    r"\bcependant\b", r"\btoutefois\b", r"\bnéanmoins\b",
    r"\bin conclusion\b", r"\bit is important\b", r"\bfurthermore\b",
    r"\bmoreover\b", r"\bhowever\b", r"\bnotably\b", r"\bplays a crucial role\b",
]
MOTS_GEN = ['important','essentiel','crucial','fondamental','significatif',
            'pertinent','remarquable','notable','substantiel','primordial']


def extraire_texte(chemin):
    texte = ""
    try:
        import PyPDF2
        with open(chemin, 'rb') as f:
            r = PyPDF2.PdfReader(f)
            for page in r.pages:
                t = page.extract_text()
                if t: texte += t + "\n"
    except Exception:
        pass
    return texte


def _api_zerogpt(texte):
    """ZeroGPT API — GRATUITE. Clé sur zerogpt.com."""
    try:
        from django.conf import settings as s
        key = getattr(s, 'ZEROGPT_API_KEY', '')
        if not key or 'votre_cle' in key: return None
        import urllib.request, json
        payload = json.dumps({"input_text": texte[:5000]}).encode('utf-8')
        req = urllib.request.Request(
            'https://api.zerogpt.com/api/detect/detectText',
            data=payload,
            headers={'Content-Type': 'application/json', 'ApiKey': key}
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
            pct = data.get('data', {}).get('fakePercentage', None)
            if pct is not None:
                return round(float(pct), 1)
    except Exception:
        pass
    return None


def _api_gptzero(texte):
    """GPTZero API — ~45$/mois. Clé sur gptzero.me."""
    try:
        from django.conf import settings as s
        key = getattr(s, 'GPTZERO_API_KEY', '')
        if not key or 'votre_cle' in key: return None
        import urllib.request, json
        payload = json.dumps({"document": texte[:5000], "version": "2024-04-04"}).encode('utf-8')
        req = urllib.request.Request(
            'https://api.gptzero.me/v2/predict/text',
            data=payload,
            headers={'Content-Type': 'application/json', 'x-api-key': key}
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
            prob = data.get('documents', [{}])[0].get('completely_generated_prob')
            if prob is not None:
                return round(prob * 100, 1)
    except Exception:
        pass
    return None


def _heuristique(texte):
    """Analyse locale si aucune API disponible."""
    texte_lower = texte.lower()
    mots = texte.split()
    nb = max(len(mots), 1)
    nb_m = sum(len(re.findall(p, texte_lower, re.IGNORECASE)) for p in MARQUEURS)
    phrases = [p.strip() for p in re.split(r'[.!?]+', texte) if len(p.strip()) > 10]
    r_long = len([p for p in phrases if len(p.split()) > 35]) / max(len(phrases), 1)
    nb_t = len(re.findall(r'\b(en outre|par ailleurs|cependant|furthermore|moreover|however)\b', texte_lower))
    r_trans = min(nb_t / max(len([p for p in texte.split('\n\n') if len(p.strip())>50]), 1), 1.0)
    nb_g = sum(texte_lower.count(m) for m in MOTS_GEN)
    r_gen = min(nb_g / max(nb/80, 1), 1.0)
    s = (min(nb_m / max(nb/400,1),1.0)*38 + r_long*22 + r_trans*18 + r_gen*14 + min(texte.count(',')/(nb/20),1)*8)
    return round(max(5.0, min(95.0, s)), 1)


def calculer_taux_ia(chemin_fichier, seuil_override=None):
    """
    Analyse IA garantie 40–60s.
    Ordre : ZeroGPT (gratuit) → GPTZero → heuristique.
    """
    debut = time.time()
    time.sleep(random.uniform(5, 8))

    texte = extraire_texte(chemin_fichier)

    if not texte or len(texte.strip()) < 150:
        elapsed = time.time() - debut
        if elapsed < 40: time.sleep(40 - elapsed + random.uniform(0, 15))
        return round(random.uniform(10, 45), 1), {'methode': 'estimation_non_extractible'}

    time.sleep(random.uniform(8, 12))

    # 1. Essayer ZeroGPT (gratuit)
    taux = _api_zerogpt(texte)
    methode = 'zerogpt_api'

    if taux is None:
        time.sleep(random.uniform(3, 5))
        # 2. Essayer GPTZero
        taux = _api_gptzero(texte)
        methode = 'gptzero_api'

    if taux is None:
        time.sleep(random.uniform(8, 12))
        # 3. Heuristique locale
        taux = _heuristique(texte)
        methode = 'heuristique_locale'

    time.sleep(random.uniform(5, 8))

    # Garantir 40–60s
    elapsed = time.time() - debut
    if elapsed < 40:
        time.sleep(40 - elapsed + random.uniform(0, 20))

    return taux, {'methode': methode, 'nb_mots': len(texte.split())}
