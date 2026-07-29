from flask import Flask, render_template, request
import fitz
import os
from gtts import gTTS

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
AUDIO_FOLDER = "static"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# Extraction du texte du PDF
def extraire_pdf(chemin):
    texte = ""

    document = fitz.open(chemin)

    for page in document:
        texte += page.get_text()

    document.close()

    return texte


# Résumé simple (temporaire avant l'IA)
def resume_simple(texte):
    phrases = texte.split(".")

    resume = ". ".join(phrases[:5])

    return resume


# Génération audio
def generer_audio(texte):

    if not texte.strip():
        return None

    fichier_audio = "static/resume.mp3"

    tts = gTTS(
        text=texte[:3000],
        lang="fr"
    )

    tts.save(fichier_audio)

    return fichier_audio



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


        audio = generer_audio(resume)



    return render_template(
        "index.html",
        texte=texte,
        resume=resume,
        audio=audio
    )



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)