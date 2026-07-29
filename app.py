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



# ==========================
# Extraction du PDF
# ==========================

def extraire_pdf(chemin):

    texte = ""

    try:

        document = fitz.open(chemin)

        for page in document:

            texte += page.get_text()


        document.close()

    except Exception as e:

        print("Erreur extraction PDF :", e)


    return texte




# ==========================
# Résumé simple
# ==========================

def resume_simple(texte):

    phrases = texte.split(".")

    resume = ". ".join(phrases[:5])

    return resume





# ==========================
# Génération audio
# ==========================

def generer_audio(texte, mode):


    if not texte or not texte.strip():

        return None



    dossier = AUDIO_FOLDER


    # Nettoyage ancien audio

    for fichier in os.listdir(dossier):

        chemin = os.path.join(
            dossier,
            fichier
        )

        try:

            os.remove(chemin)

        except:

            pass



    fichiers_audio = []



    if mode == "resume":


        contenu = resume_simple(texte)


        morceaux = [
            contenu
        ]


    else:


        # Découpe du livre complet
        # évite le crash Render

        taille = 1500


        morceaux = [

            texte[i:i + taille]

            for i in range(
                0,
                len(texte),
                taille
            )

        ]



    for index, morceau in enumerate(morceaux):


        if not morceau.strip():

            continue


        try:


            nom = f"livre_{index}.mp3"


            chemin = os.path.join(
                dossier,
                nom
            )


            tts = gTTS(
                text=morceau,
                lang="fr"
            )


            tts.save(chemin)


            fichiers_audio.append(
                chemin
            )



        except Exception as e:


            print(
                "Erreur génération audio :",
                e
            )


            return None




    if fichiers_audio:


        # On retourne le premier fichier
        # pour lecture navigateur

        return fichiers_audio[0]



    return None






# ==========================
# Page principale
# ==========================

@app.route("/", methods=["GET", "POST"])

def accueil():


    texte = ""

    resume = ""

    audio = None



    if request.method == "POST":



        fichier = request.files.get("pdf")



        if fichier:


            chemin = os.path.join(

                app.config["UPLOAD_FOLDER"],

                fichier.filename

            )


            fichier.save(chemin)



            texte = extraire_pdf(
                chemin
            )



            resume = resume_simple(
                texte
            )



            mode = request.form.get(

                "mode",

                "resume"

            )



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





# ==========================
# Lancement serveur
# ==========================

if __name__ == "__main__":


    app.run(

        host="0.0.0.0",

        port=5000

    )