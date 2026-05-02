#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import vlc
import os
import subprocess
from pathlib import Path

class MediaPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Media Player")
        self.root.geometry("800x600")
        
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        
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
        
        self.video_frame = tk.Frame(self.root, bg='black')
        self.video_frame.pack(fill=tk.BOTH, expand=True)
        
        control_frame = tk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(control_frame, text="Play", command=self.play).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Pause", command=self.pause).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Stop", command=self.stop).pack(side=tk.LEFT, padx=2)
        
        self.volume = tk.Scale(control_frame, from_=0, to=100, orient=tk.HORIZONTAL, label="Volume")
        self.volume.set(70)
        self.volume.pack(side=tk.RIGHT, padx=5)
        self.volume.bind("<Motion>", self.set_volume)
        
        self.root.update()
        self.set_window_handle()
        
    def set_window_handle(self):
        if os.name == "nt":
            self.player.set_hwnd(self.video_frame.winfo_id())
        else:
            self.player.set_xwindow(self.video_frame.winfo_id())
            
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
            media = self.instance.media_new(filename)
            self.player.set_media(media)
            self.play()
            
    def open_cd(self):
        cdrom_path = self.find_cdrom()
        if cdrom_path:
            try:
                media = self.instance.media_new_location(f"cdda://{cdrom_path}")
                self.player.set_media(media)
                self.play()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open CD: {str(e)}")
        else:
            messagebox.showinfo("No CD", "No CD/DVD drive found or no disc inserted")
            
    def open_dvd(self):
        cdrom_path = self.find_cdrom()
        if cdrom_path:
            try:
                media = self.instance.media_new_location(f"dvd://{cdrom_path}")
                self.player.set_media(media)
                self.play()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open DVD: {str(e)}")
        else:
            messagebox.showinfo("No DVD", "No DVD drive found or no disc inserted")
            
    def find_cdrom(self):
        for path in ["/dev/cdrom", "/dev/dvd", "/dev/sr0"]:
            if os.path.exists(path):
                return path
        return None
        
    def play(self):
        self.player.play()
        
    def pause(self):
        self.player.pause()
        
    def stop(self):
        self.player.stop()
        
    def set_volume(self, event=None):
        self.player.audio_set_volume(self.volume.get())

if __name__ == "__main__":
    root = tk.Tk()
    app = MediaPlayer(root)
    root.mainloop()
