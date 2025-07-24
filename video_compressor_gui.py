import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os

def compress_video():
    input_path = input_file_var.get()
    crf_value = crf_slider.get()
    
    if not input_path:
        messagebox.showerror("Error", "Please select a video file.")
        return

    
    base, ext = os.path.splitext(input_path)
    output_path = base + f"_compressed_crf{crf_value}" + ext

   
    command = [
        'ffmpeg', '-i', input_path,
        '-vcodec', 'libx264',
        '-crf', str(crf_value),
        output_path
    ]

    try:
        subprocess.run(command, check=True)
        messagebox.showinfo("Success", f"Video compressed successfully!\nSaved as:\n{output_path}")
    except subprocess.CalledProcessError:
        messagebox.showerror("Error", "Compression failed. Make sure ffmpeg is installed.")

def browse_file():
    file_path = filedialog.askopenfilename(
        filetypes=[("Video Files", "*.mp4 *.mov *.avi *.mkv"), ("All files", "*.*")]
    )
    input_file_var.set(file_path)

#GUI
root = tk.Tk()
root.title("Video Compressor")


input_file_var = tk.StringVar()
tk.Label(root, text="Select Video File:").pack(pady=5)
tk.Entry(root, textvariable=input_file_var, width=50).pack(padx=10)
tk.Button(root, text="Browse", command=browse_file).pack(pady=5)


tk.Label(root, text="Compression Quality (CRF):").pack(pady=5)
crf_slider = tk.Scale(root, from_=18, to=35, orient="horizontal")  
crf_slider.set(28)
crf_slider.pack()


tk.Button(root, text="Compress Video", command=compress_video, bg="green", fg="white").pack(pady=15)

root.mainloop()
