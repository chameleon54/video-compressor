import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import os
import re
import threading
from PIL import Image, ImageTk
import cv2

def show_video_thumbnail(video_path):
    try:
        cap = cv2.VideoCapture(video_path)
        success, frame = cap.read()
        cap.release()

        if success:
            # Resize frame to fit window (keep aspect ratio)
            frame = cv2.resize(frame, (320, 180))
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img_tk = ImageTk.PhotoImage(img)
            thumbnail_image_label.configure(image=img_tk)
            thumbnail_image_label.image = img_tk  # Keep reference!
        else:
            thumbnail_image_label.configure(image='', text="Preview not available")

    except Exception as e:
        thumbnail_image_label.configure(image='', text="Error loading preview")


def update_estimated_size():
    file_path = input_file_var.get()
    crf = crf_slider.get()
    if os.path.isfile(file_path):
        try:
            estimated_mb = estimate_output_size(file_path, crf)
            estimated_label.config(text=f"Estimated output size: ~{estimated_mb} MB")
        except Exception:
            estimated_label.config(text="Estimated output size: -")
    else:
        estimated_label.config(text="Estimated output size: -")

def estimate_output_size(input_path, crf):
    size_bytes = os.path.getsize(input_path)
    size_mb = size_bytes / (1024 * 1024)

    
    if crf <= 20:
        ratio = 0.75
    elif crf <= 23:
        ratio = 0.65
    elif crf <= 26:
        ratio = 0.5
    elif crf <= 30:
        ratio = 0.4
    elif crf <= 33:
        ratio = 0.3
    else:
        ratio = 0.2

    estimated_mb = size_mb * ratio
    return round(estimated_mb, 2)


def get_video_duration(filename):
    
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries',
             'format=duration', '-of',
             'default=noprint_wrappers=1:nokey=1', filename],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return float(result.stdout.strip())
    except Exception:
        return None

def parse_time(time_str):
    
    h, m, s = re.split('[:.]', time_str)[:3]
    return int(h) * 3600 + int(m) * 60 + int(s)

def compress_video():
    input_path = input_file_var.get()
    crf_value = crf_slider.get()

    if not input_path:
        messagebox.showerror("Error", "Please select a video file.")
        return

    duration = get_video_duration(input_path)
    if not duration:
        messagebox.showerror("Error", "Could not get video duration.")
        return

    progress_bar["value"] = 0
    progress_label.config(text="Starting compression...")

    base, ext = os.path.splitext(input_path)
    output_path = base + f"_compressed_crf{crf_value}" + ext
    
    command = [
        'ffmpeg', '-i', input_path,
        '-vcodec', 'libx264', '-crf', str(crf_value),
        '-y', output_path  #Overwrite without asking
    ]
    
    def run_ffmpeg():
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            for line in process.stderr:
                if "time=" in line:
                    match = re.search(r'time=(\d+:\d+:\d+\.\d+)', line)
                    if match:
                        current_time = parse_time(match.group(1))
                        progress = (current_time / duration) * 100
                        progress_bar["value"] = progress
                        progress_label.config(text=f"Compressing... {int(progress)}%")

            process.wait()
            if process.returncode == 0:
                progress_bar["value"] = 100
                progress_label.config(text="Compression complete!")
                messagebox.showinfo("Success", f"Video compressed!\nSaved as:\n{output_path}")
            else:
                raise subprocess.CalledProcessError(process.returncode, command)

        except Exception as e:
            progress_label.config(text="Compression failed.")
            messagebox.showerror("Error", f"Compression failed:\n{e}")

    
    threading.Thread(target=run_ffmpeg).start()

def browse_file():
    file_path = filedialog.askopenfilename(
        filetypes=[("Video Files", "*.mp4 *.mov *.avi *.mkv"), ("All files", "*.*")]
    )
    input_file_var.set(file_path)
    update_estimated_size()
    show_video_thumbnail(file_path)
#gui
#Todo:make it more beautiful
root = tk.Tk()
root.title("Video Compressor with Progress Bar")

input_file_var = tk.StringVar()

tk.Label(root, text="Select Video File:").pack(pady=5)
tk.Entry(root, textvariable=input_file_var, width=50).pack(padx=10)
tk.Button(root, text="Browse", command=browse_file).pack(pady=5)

preview_label = tk.Label(root, text="Video Preview")
preview_label.pack(pady=10)

thumbnail_image_label = tk.Label(root)  
thumbnail_image_label.pack()

tk.Label(root, text="Compression Quality (CRF):").pack(pady=5)
crf_slider = tk.Scale(root, from_=18, to=35, orient="horizontal", command=lambda value: update_estimated_size())
crf_slider.set(28)
crf_slider.pack()

estimated_label = tk.Label(root, text="Estimated output size: -")
estimated_label.pack()

tk.Button(root, text="Compress Video", command=compress_video, bg="green", fg="white").pack(pady=10)

progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress_bar.pack(pady=10)

progress_label = tk.Label(root, text="")
progress_label.pack()

root.mainloop()
