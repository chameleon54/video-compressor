import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import os
import re
import threading
from PIL import Image, ImageTk
import cv2
from tkinterdnd2 import TkinterDnD, DND_FILES

video_files = []

def show_video_thumbnail(video_path):
    try:
        cap = cv2.VideoCapture(video_path)
        success, frame = cap.read()
        cap.release()

        if success:
            frame = cv2.resize(frame, (320, 180))
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img_tk = ImageTk.PhotoImage(img)
            thumbnail_image_label.configure(image=img_tk)
            thumbnail_image_label.image = img_tk
        else:
            thumbnail_image_label.configure(image='', text="Preview not available")
    except Exception:
        thumbnail_image_label.configure(image='', text="Error loading preview")

def update_estimated_size(file_path=None):
    if not file_path:
        file_path = video_files[-1] if video_files else None
    crf = crf_slider.get()
    if file_path and os.path.isfile(file_path):
        try:
            estimated_mb = estimate_output_size(file_path, crf)
            estimated_label.config(text=f"Estimated size (latest): ~{estimated_mb} MB")
        except Exception:
            estimated_label.config(text="Estimated size: -")
    else:
        estimated_label.config(text="Estimated size: -")

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
    if not video_files:
        messagebox.showerror("Error", "No videos selected.")
        return

    crf_value = crf_slider.get()

    def compress_all():
        total = len(video_files)
        for i, input_path in enumerate(video_files):
            progress_label.config(text=f"Compressing ({i+1}/{total}): {os.path.basename(input_path)}")
            duration = get_video_duration(input_path)
            if not duration:
                continue

            base, ext = os.path.splitext(input_path)
            output_path = base + f"_compressed_crf{crf_value}" + ext

            command = [
                'ffmpeg', '-i', input_path,
                '-vcodec', 'libx264', '-crf', str(crf_value),
                '-y', output_path
            ]

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
                        progress_label.config(text=f"{os.path.basename(input_path)}: {int(progress)}%")

            process.wait()
            progress_bar["value"] = 0

        progress_label.config(text="All videos compressed.")
        messagebox.showinfo("Success", f"Compressed {total} video(s).")

    threading.Thread(target=compress_all).start()

def browse_file():
    file_paths = filedialog.askopenfilenames(
        filetypes=[("Video Files", "*.mp4 *.mov *.avi *.mkv"), ("All files", "*.*")]
    )
    add_files(file_paths)

def on_drop(event):
    file_paths = root.tk.splitlist(event.data)
    add_files(file_paths)

def add_files(file_paths):
    for path in file_paths:
        if path not in video_files:
            video_files.append(path)
            file_listbox.insert(tk.END, os.path.basename(path))
    if video_files:
        show_video_thumbnail(video_files[-1])
        update_estimated_size(video_files[-1])
        file_count_label.config(text=f"{len(video_files)} video(s) selected")
def remove_selected():
    selected_indices = list(file_listbox.curselection())
    for i in reversed(selected_indices):
        del video_files[i]
        file_listbox.delete(i)
    file_count_label.config(text=f"{len(video_files)} video(s) selected")
    if video_files:
        show_video_thumbnail(video_files[-1])
        update_estimated_size(video_files[-1])
    else:
        thumbnail_image_label.configure(image='', text='')
        estimated_label.config(text="Estimated size: -")

def remove_all():
    video_files.clear()
    file_listbox.delete(0, tk.END)
    file_count_label.config(text="0 video(s) selected")
    thumbnail_image_label.configure(image='', text='')
    estimated_label.config(text="Estimated size: -")


# GUI
root = TkinterDnD.Tk()
root.title("Batch Video Compressor")

tk.Label(root, text="Drop or Select Video Files").pack(pady=5)
tk.Button(root, text="Browse", command=browse_file).pack()

root.drop_target_register(DND_FILES)
root.dnd_bind('<<Drop>>', on_drop)

file_listbox = tk.Listbox(root, width=50, height=6)
file_listbox.pack(pady=5)
# Buttons to remove selected or all files
btn_frame = tk.Frame(root)
btn_frame.pack(pady=(0, 10))

tk.Button(btn_frame, text="Remove Selected", command=lambda: remove_selected()).pack(side=tk.LEFT, padx=5)
tk.Button(btn_frame, text="Remove All", command=lambda: remove_all()).pack(side=tk.LEFT, padx=5)


file_count_label = tk.Label(root, text="0 video(s) selected")
file_count_label.pack()

preview_label = tk.Label(root, text="Preview (last selected):")
preview_label.pack()
thumbnail_image_label = tk.Label(root)
thumbnail_image_label.pack()

tk.Label(root, text="Compression Quality (CRF):").pack(pady=5)
crf_slider = tk.Scale(root, from_=18, to=35, orient="horizontal", command=lambda v: update_estimated_size())
crf_slider.set(28)
crf_slider.pack()

estimated_label = tk.Label(root, text="Estimated size: -")
estimated_label.pack()

tk.Button(root, text="Compress All Videos", command=compress_video, bg="green", fg="white").pack(pady=10)

progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress_bar.pack(pady=10)

progress_label = tk.Label(root, text="")
progress_label.pack()

root.mainloop()
