from flask import Flask, render_template, request
import fitz
import os
from gtts import gTTS

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
AUDIO_FOLDER = "static/audio"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Extraction PDF
def extraire_pdf(chemin):

    texte = ""

    document = fitz.open(chemin)

    for page in document:
        texte += page.get_text()

    document.close()

    return texte

# Résumé simple
def resume_simple(texte):

    phrases = texte.split(".")

    return ". ".join(phrases[:5])

# Génération audio
# Génération audio
def generer_audio(texte, mode):

    dossier = "static/audio"
    os.makedirs(dossier, exist_ok=True)

    if not texte or not texte.strip():
        return None

    fichiers = []

    if mode == "resume":

        morceaux = [
            resume_simple(texte)
        ]

    else:

        # Découpage du document complet
        taille = 3000

        morceaux = [
            texte[i:i + taille]
            for i in range(0, len(texte), taille)
        ]


    for index, morceau in enumerate(morceaux):

        chemin = os.path.join(
            dossier,
            f"livre_{index}.mp3"
        )

        try:

            tts = gTTS(
                text=morceau,
                lang="fr"
            )

            tts.save(chemin)

            fichiers.append(chemin)

        except Exception as e:

            print("Erreur audio :", e)
            return None


    if fichiers:

        return fichiers[0]

    return None
    try:
        tts = gTTS(text=contenu, lang="fr")
        tts.save(chemin)
        return chemin

    except Exception as e:
        print("Erreur gTTS :", e)
        return None

@app.route("/", methods=["GET", "POST"])
def accueil():

    texte = ""
    resume = ""
    audio = None

    if request.method == "POST":

        fichier = request.files["pdf"]

        chemin = os.path.join(
            app.config["UPLOAD_FOLDER"],
            fichier.filename
        )

        fichier.save(chemin)

        texte = extraire_pdf(chemin)

        resume = resume_simple(texte)

        mode = request.form.get("mode", "resume")

        audio = generer_audio(texte, mode)

    return render_template(
        "index.html",
        texte=texte,
        resume=resume,
        audio=audio
    )

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )