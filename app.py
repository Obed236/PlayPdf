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

    if mode == "resume":

        fichier = "static/audio/resume.mp3"

        tts = gTTS(
            text=texte[:3000],
            lang="fr"
        )

        tts.save(fichier)

        return fichier



    else:

        dossier = "static/audio"

        morceaux = [
            texte[i:i+3000]
            for i in range(0, len(texte), 3000)
        ]


        fichiers = []


        for index, morceau in enumerate(morceaux):

            fichier = f"{dossier}/livre_{index}.mp3"


            tts = gTTS(
                text=morceau,
                lang="fr"
            )


            tts.save(fichier)


            fichiers.append(fichier)


        # Pour cette première version,
        # on retourne le premier fichier audio

        return fichiers[0]



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


        choix = request.form.get("mode")


        if choix == "resume":

            audio = generer_audio(
                resume,
                "resume"
            )


        elif choix == "livre":

            audio = generer_audio(
                texte,
                "livre"
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