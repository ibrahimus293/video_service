from flask import Flask, request, send_file, jsonify
import os, subprocess, tempfile, requests

app = Flask(__name__)

@app.route("/video", methods=["POST"])
def generar_video():
    data = request.json
    imagen_url = data.get("imagen")
    audio_url = data.get("audio")
    nombre = data.get("nombre", "video.mp4")

    if not imagen_url or not audio_url:
        return jsonify({"error": "Faltan imagen o audio"}), 400

    with tempfile.TemporaryDirectory() as tmp:
        img = os.path.join(tmp, "img.jpg")
        audio = os.path.join(tmp, "audio.mp3")
        video = os.path.join(tmp, nombre)

        with open(img, "wb") as f:
            f.write(requests.get(imagen_url).content)
        with open(audio, "wb") as f:
            f.write(requests.get(audio_url).content)

        dur = float(subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", audio
        ]).decode().strip())

        subprocess.run([
            "ffmpeg", "-y", "-loop", "1", "-i", img, "-i", audio,
            "-c:v", "libx264", "-t", str(dur), "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k", "-shortest", video
        ], check=True)

        return send_file(video, as_attachment=True, download_name=nombre, mimetype="video/mp4")

@app.route("/health")
def health(): return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
