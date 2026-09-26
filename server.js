// Backend minimal pour ViralClip
// À déployer sur Railway.app
//
// Ce serveur reçoit un lien vidéo, lance le pipeline
// (téléchargement -> transcription -> sous-titres -> export)
// et renvoie l'URL de la vidéo générée.
//
// NOTE : la génération vidéo (yt-dlp, Whisper, FFmpeg) demande
// un environnement Python. Ici le serveur Node.js appelle un
// script Python en sous-processus, comme validé dans Colab.

const express = require("express");
const cors = require("cors");
const { exec } = require("child_process");
const path = require("path");
const fs = require("fs");

const app = express();
app.use(cors());
app.use(express.json());

// Dossier où seront stockées les vidéos générées
const OUTPUT_DIR = path.join(__dirname, "outputs");
if (!fs.existsSync(OUTPUT_DIR)) fs.mkdirSync(OUTPUT_DIR);
app.use("/outputs", express.static(OUTPUT_DIR));

app.post("/generate", (req, res) => {
  const { url } = req.body;
  if (!url) return res.status(400).json({ error: "Lien manquant" });

  const jobId = Date.now();
  const outputFile = path.join(OUTPUT_DIR, `video_${jobId}.mp4`);

  // Appelle le script Python (pipeline.py) qui fait le travail
  // téléchargement + transcription + sous-titres + export
  const command = `python3 pipeline.py "${url}" "${outputFile}"`;

  exec(command, { timeout: 180000 }, (error, stdout, stderr) => {
    if (error) {
      console.error(stderr);
      return res.status(500).json({ error: "Échec du traitement vidéo" });
    }

    res.json({
      videoUrl: `/outputs/video_${jobId}.mp4`
    });
  });
});

app.get("/", (req, res) => {
  res.send("ViralClip backend actif ✅");
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Serveur lancé sur le port ${PORT}`));
