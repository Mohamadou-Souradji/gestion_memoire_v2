import os
import re

# Dossier où se trouvent tes fichiers HTML
TEMPLATE_DIR = 'templates'

# Cette expression cherche n'importe quelle suite de </div> (entre 1 et 10) 
# qui se trouve juste avant un {% endblock %}, en ignorant les espaces/sauts de ligne.
pattern = re.compile(r'(</div>\s*){1,10}{%\s*endblock\s*%}')
replacement = '{% endblock %}'

def clean_templates():
    count = 0
    # On parcourt récursivement tous les sous-dossiers
    for root, dirs, files in os.walk(TEMPLATE_DIR):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # On vérifie si le problème existe dans ce fichier
                if pattern.search(content):
                    # On nettoie
                    new_content = pattern.sub(replacement, content)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"✅ Corrigé : {file_path}")
                    count += 1
    
    print(f"\nTerminé ! {count} fichiers ont été nettoyés de leurs balises parasites.")

if __name__ == "__main__":
    clean_templates()