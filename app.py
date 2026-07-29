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
def generer_audio(texte, mode):

    dossier = "static/audio"
    os.makedirs(dossier, exist_ok=True)

    if mode == "resume":

        chemin = os.path.join(dossier, "resume.mp3")

        contenu = resume_simple(texte)[:5000]

    else:

        chemin = os.path.join(dossier, "livre_complet.mp3")

        contenu = texte[:5000]

    tts = gTTS(
        text=contenu,
        lang="fr"
    )

    tts.save(chemin)

    return chemin



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

        audio = generer_audio(
            texte,
            mode
        )

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