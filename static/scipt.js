let synthese = window.speechSynthesis;

let texte = document.querySelector(".texte").innerText;

let lecture = new SpeechSynthesisUtterance(texte);

lecture.lang = "fr-FR";

lecture.rate = 1;


function lire() {

    synthese.cancel();

    synthese.speak(lecture);

}


function pause() {

    synthese.pause();

}


function reprendre() {

    synthese.resume();

}