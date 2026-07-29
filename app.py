from flask import Flask, render_template, request
import fitz
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def extraire_pdf(chemin):
    texte = ""

    document = fitz.open(chemin)

    for page in document:
        texte += page.get_text()

    document.close()

    return texte


def resume_simple(texte):
    phrases = texte.split(".")
    
    resume = ". ".join(phrases[:5])

    return resume


@app.route("/", methods=["GET", "POST"])
def accueil():

    texte = ""
    resume = ""

    if request.method == "POST":

        fichier = request.files["pdf"]

        chemin = os.path.join(
            app.config["UPLOAD_FOLDER"],
            fichier.filename
        )

        fichier.save(chemin)

        texte = extraire_pdf(chemin)

        resume = resume_simple(texte)


    return render_template(
        "index.html",
        texte=texte,
        resume=resume
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)