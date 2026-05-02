#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import os

class MediaPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Media Player")
        self.root.geometry("600x400")
        self.setup_ui()
        
    def setup_ui(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open File", command=self.open_file)
        file_menu.add_command(label="Open CD", command=self.open_cd)
        file_menu.add_command(label="Open DVD", command=self.open_dvd)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        main_frame = tk.Frame(self.root, bg='black')
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        label = tk.Label(main_frame, text="Media Player\nSelect a file or disc to play", 
                        fg='white', bg='black', font=('Arial', 16))
        label.pack(expand=True)
        
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Open File", command=self.open_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Play CD", command=self.open_cd).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Play DVD", command=self.open_dvd).pack(side=tk.LEFT, padx=5)
        
    def open_file(self):
        filename = filedialog.askopenfilename(
            title="Select Media File",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mkv *.mov *.wmv *.flv"),
                ("Audio files", "*.mp3 *.wav *.flac *.ogg *.m4a"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.play_media(filename)
            
    def open_cd(self):
        cdrom = self.find_cdrom()
        if cdrom:
            self.play_media(cdrom)
        else:
            messagebox.showinfo("No CD", "No CD/DVD drive found")
            
    def open_dvd(self):
        cdrom = self.find_cdrom()
        if cdrom:
            self.play_media(cdrom)
        else:
            messagebox.showinfo("No DVD", "No DVD drive found")
            
    def find_cdrom(self):
        for path in ["/dev/cdrom", "/dev/dvd", "/dev/sr0"]:
            if os.path.exists(path):
                return path
        return None
        
    def play_media(self, path):
        try:
            subprocess.Popen(["xdg-open", path])
        except:
            try:
                subprocess.Popen(["vlc", path])
            except:
                messagebox.showerror("Error", "No media player found. Install vlc or another player.")

if __name__ == "__main__":
    root = tk.Tk()
    app = MediaPlayer(root)
    root.mainloop()
