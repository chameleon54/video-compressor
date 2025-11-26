from flask import Flask, request, jsonify, send_file, Response
import os
import subprocess
import uuid
import threading

UPLOAD = "uploads"
OUTPUT = "outputs"

os.makedirs(UPLOAD, exist_ok=True)
os.makedirs(OUTPUT, exist_ok=True)

app = Flask(__name__)


def compress_video(input_path, output_path, crf, threads, progress_id):
    command = [
        "ffmpeg", "-i", input_path,
        "-vcodec", "libx264",
        "-crf", str(crf),
        "-threads", str(threads),
        "-progress", f"{progress_id}.txt", "-y",
        output_path
    ]

    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


@app.route("/compress", methods=["POST"])
def compress():
    videos = request.files.getlist("videos")
    crf = int(request.form.get("crf", 28))
    threads = int(request.form.get("threads", 2))

    results = []

    for video in videos:
        uid = str(uuid.uuid4())
        progress_id = f"progress_{uid}"
        input_path = os.path.join(UPLOAD, f"{uid}_{video.filename}")
        output_path = os.path.join(OUTPUT, f"{uid}_compressed.mp4")

        video.save(input_path)

        threading.Thread(target=compress_video,
                         args=(input_path, output_path, crf, threads, progress_id)).start()

        results.append({"id": uid, "name": video.filename})

    return jsonify(results)


@app.route("/progress/<task_id>")
def progress(task_id):
    path = f"progress_{task_id}.txt"
    if not os.path.exists(path):
        return jsonify({"progress": 0})

    with open(path, "r") as f:
        data = f.read()

    # Extract out_time from ffmpeg progress
    lines = data.splitlines()
    time_line = next((x for x in lines if x.startswith("out_time_ms=")), None)

    if not time_line:
        return jsonify({"progress": 0})

    ms = int(time_line.replace("out_time_ms=", ""))
    seconds = ms / 1000000

    return jsonify({"progress": seconds})


@app.route("/download/<task_id>")
def download(task_id):
    file_name = f"{task_id}_compressed.mp4"
    path = os.path.join(OUTPUT, file_name)

    if not os.path.exists(path):
        return jsonify({"error": "Not ready"}), 404

    return send_file(path, as_attachment=True)


@app.route("/")
def home():
    return "Video Compressor Backend Running"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
