from flask import Flask, request, send_file, jsonify
import os
import subprocess
import tempfile
import requests

app = Flask(__name__)

@app.route('/render', methods=['POST'])
def render_video():
    data = request.json
    ruta_imagen = data.get("ruta_imagen")
    ruta_audio = data.get("ruta_audio")
    ruta_salida = data.get("ruta_salida", "output.mp4")

    if not ruta_imagen or not ruta_audio:
        return jsonify({"error": "Se necesitan las URLs de imagen y audio"}), 400

    with tempfile.TemporaryDirectory() as tmpdir:
        image_path = os.path.join(tmpdir, "image.png")
        audio_path = os.path.join(tmpdir, "audio.mp3")
        output_path = os.path.join(tmpdir, ruta_salida)

        # Descargar imagen
        try:
            r_img = requests.get(ruta_imagen)
            with open(image_path, "wb") as f:
                f.write(r_img.content)
        except Exception as e:
            return jsonify({"error": "No se pudo descargar la imagen", "details": str(e)}), 500

        # Descargar audio
        try:
            r_audio = requests.get(ruta_audio)
            with open(audio_path, "wb") as f:
                f.write(r_audio.content)
        except Exception as e:
            return jsonify({"error": "No se pudo descargar el audio", "details": str(e)}), 500

        try:
            # Generar video a partir de imagen + audio
            subprocess.run([
                'ffmpeg', '-y',
                '-loop', '1', '-i', image_path,
                '-i', audio_path,
                '-c:v', 'libx264', '-tune', 'stillimage',
                '-c:a', 'aac', '-b:a', '192k',
                '-pix_fmt', 'yuv420p', '-shortest',
                output_path
            ], check=True)
        except subprocess.CalledProcessError as e:
            return jsonify({"error": "Error al ejecutar FFmpeg", "details": str(e)}), 500

        if not os.path.exists(output_path):
            return jsonify({"error": "No se generó el video"}), 500

        return send_file(output_path, as_attachment=True, download_name=ruta_salida, mimetype='video/mp4')

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
