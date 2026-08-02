from __future__ import annotations

import asyncio
import os
import re
import uuid
from pathlib import Path

import edge_tts
import fitz  # PyMuPDF
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
AUDIO_FOLDER = BASE_DIR / "static" / "audio"
ALLOWED_EXTENSIONS = {"pdf"}
MAX_PDF_SIZE = 25 * 1024 * 1024  # 25 Mo

# Voix française naturelle. Autre choix possible : fr-FR-HenriNeural
VOICE = "fr-FR-DeniseNeural"
VOICE_RATE = "-8%"       # Lecture légèrement ralentie
VOICE_VOLUME = "+10%"    # Volume un peu renforcé
VOICE_PITCH = "+0Hz"

UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
AUDIO_FOLDER.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.config.update(
    UPLOAD_FOLDER=str(UPLOAD_FOLDER),
    MAX_CONTENT_LENGTH=MAX_PDF_SIZE,
)


def extension_autorisee(nom_fichier: str) -> bool:
    """Vérifie que le fichier possède bien l'extension PDF."""
    return "." in nom_fichier and nom_fichier.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def nettoyer_texte(texte: str) -> str:
    """Nettoie le texte extrait afin d'améliorer la prononciation."""
    if not texte:
        return ""

    # Répare les mots coupés en fin de ligne : "infor-\nmatique" -> "informatique"
    texte = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", texte)

    # Transforme les retours à la ligne simples en espaces.
    texte = re.sub(r"(?<!\n)\n(?!\n)", " ", texte)

    # Marque une pause entre les paragraphes.
    texte = re.sub(r"\n{2,}", ". ", texte)

    # Supprime les espaces inutiles.
    texte = re.sub(r"[ \t]+", " ", texte)
    texte = re.sub(r"\s+([,.;:!?])", r"\1", texte)
    texte = re.sub(r"([.!?])(?=[A-ZÀ-ÖØ-Ý])", r"\1 ", texte)

    return texte.strip()


def extraire_pdf(chemin: Path) -> str:
    """Extrait le texte d'un PDF et ferme toujours le document."""
    try:
        with fitz.open(chemin) as document:
            pages = [page.get_text("text", sort=True) for page in document]
        return nettoyer_texte("\n\n".join(pages))
    except (fitz.FileDataError, fitz.EmptyFileError) as exc:
        app.logger.exception("PDF invalide ou illisible : %s", exc)
        return ""
    except Exception as exc:
        app.logger.exception("Erreur pendant l'extraction du PDF : %s", exc)
        return ""


def resume_simple(texte: str, nombre_phrases: int = 5) -> str:
    """Produit un résumé extractif simple à partir des premières phrases utiles."""
    if not texte:
        return ""

    phrases = re.split(r"(?<=[.!?])\s+", texte)
    phrases_utiles = [phrase.strip() for phrase in phrases if len(phrase.strip()) >= 20]
    return " ".join(phrases_utiles[:nombre_phrases])


async def _creer_audio_edge(texte: str, chemin_sortie: Path) -> None:
    communication = edge_tts.Communicate(
        text=texte,
        voice=VOICE,
        rate=VOICE_RATE,
        volume=VOICE_VOLUME,
        pitch=VOICE_PITCH,
    )
    await communication.save(str(chemin_sortie))


def generer_audio(texte: str, mode: str) -> str | None:
    """Génère un MP3 unique et renvoie son chemin relatif dans static/."""
    contenu = resume_simple(texte) if mode == "resume" else texte
    contenu = nettoyer_texte(contenu)

    if not contenu:
        return None

    nom_audio = f"lecture_{uuid.uuid4().hex}.mp3"
    chemin_audio = AUDIO_FOLDER / nom_audio

    try:
        asyncio.run(_creer_audio_edge(contenu, chemin_audio))
    except Exception as exc:
        app.logger.exception("Erreur pendant la génération audio : %s", exc)
        chemin_audio.unlink(missing_ok=True)
        return None

    if not chemin_audio.exists() or chemin_audio.stat().st_size == 0:
        chemin_audio.unlink(missing_ok=True)
        return None

    # Chemin relatif utilisable avec url_for('static', filename=audio)
    return f"audio/{nom_audio}"


@app.errorhandler(413)
def fichier_trop_volumineux(_erreur):
    return render_template(
        "index.html",
        texte="",
        resume="",
        audio=None,
        erreur="Le fichier PDF dépasse la limite autorisée de 25 Mo.",
    ), 413


@app.route("/", methods=["GET", "POST"])
def accueil():
    texte = ""
    resume = ""
    audio = None
    erreur = None
    chemin_pdf: Path | None = None

    if request.method == "POST":
        fichier = request.files.get("pdf")
        mode = request.form.get("mode", "resume")

        if mode not in {"resume", "livre"}:
            mode = "resume"

        if fichier is None or not fichier.filename:
            erreur = "Sélectionne un fichier PDF."
        elif not extension_autorisee(fichier.filename):
            erreur = "Le fichier sélectionné doit être au format PDF."
        else:
            nom_securise = secure_filename(fichier.filename)
            nom_unique = f"{uuid.uuid4().hex}_{nom_securise}"
            chemin_pdf = UPLOAD_FOLDER / nom_unique

            try:
                fichier.save(chemin_pdf)
                texte = extraire_pdf(chemin_pdf)

                if not texte:
                    erreur = (
                        "Aucun texte exploitable n'a été trouvé. "
                        "Le PDF est peut-être scanné sous forme d'images."
                    )
                else:
                    resume = resume_simple(texte)
                    audio = generer_audio(texte, mode)
                    if audio is None:
                        erreur = "La génération de la voix a échoué. Réessaie dans un instant."
            except OSError as exc:
                app.logger.exception("Erreur d'enregistrement du PDF : %s", exc)
                erreur = "Impossible d'enregistrer ou de traiter le fichier PDF."
            finally:
                if chemin_pdf is not None:
                    chemin_pdf.unlink(missing_ok=True)

    return render_template(
        "index.html",
        texte=texte,
        resume=resume,
        audio=audio,
        erreur=erreur,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
