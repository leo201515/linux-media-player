#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import os
import sys
import time
import threading
import shutil

# Suppress OpenCV warnings
os.environ['OPENCV_VIDEOIO_DEBUG'] = '0'
os.environ['OPENCV_LOG_LEVEL'] = 'SILENT'

class MediaPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Media Player")
        self.root.geometry("800x600")
        self.current_media = None
        self.playing = False
        self.video_thread = None
        self.external_player = None
        
        # Detect available players FIRST (before setup_ui needs it)
        self.available_players = self.find_system_players()
        
        self.setup_ui()
        
    def find_system_players(self):
        """Find available video players on the system"""
        players = {}
        for cmd, name in [
            ('ffplay', 'FFplay'),
            ('mpv', 'MPV'),
            ('mplayer', 'MPlayer'),
            ('vlc', 'VLC'),
            ('totem', 'Totem'),
            ('parole', 'Parole'),
        ]:
            if shutil.which(cmd):
                players[cmd] = name
        return players
        
    def setup_ui(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open File", command=self.open_file)
        file_menu.add_command(label="Open CD/DVD", command=self.open_disc)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Video display area
        self.video_frame = tk.Frame(self.root, bg='black', width=640, height=480)
        self.video_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.video_label = tk.Label(self.video_frame, bg='black', text="No video loaded")
        self.video_label.pack(expand=True)
        
        # Controls
        ctrl_frame = tk.Frame(self.root)
        ctrl_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.play_btn = ttk.Button(ctrl_frame, text="Play", command=self.play)
        self.play_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(ctrl_frame, text="Stop", command=self.stop)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Status
        self.status_label = tk.Label(self.root, text="Ready - No disc", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Check for disc on startup
        self.check_disc_status()
        
    def check_disc_status(self):
        """Update status based on whether disc is present"""
        cdrom = self.find_cdrom()
        if cdrom and self.disc_has_media(cdrom):
            player_info = ""
            if self.available_players:
                player_info = f" ({', '.join(self.available_players.values())} available)"
            self.status_label.config(text=f"Ready - Disc detected{player_info}")
        else:
            self.status_label.config(text="Ready - No disc in drive")
        
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
            self.current_media = filename
            self.status_label.config(text=f"Loaded: {os.path.basename(filename)}")
            self.play()
            
    def open_disc(self):
        self.status_label.config(text="Checking disc...")
        self.root.update()
        
        cdrom = self.find_cdrom()
        if not cdrom:
            messagebox.showinfo("No Disc Drive", "No CD/DVD drive found on this system.", parent=self.root)
            self.status_label.config(text="Ready - No disc drive")
            return
        
        self.status_label.config(text="Checking for disc media...")
        self.root.update()
        
        if not self.disc_has_media(cdrom):
            messagebox.showinfo("No Disc", "No disc detected in the drive.\nPlease insert a CD/DVD and try again.", parent=self.root)
            self.status_label.config(text="Ready - No disc in drive")
            return
            
        self.status_label.config(text="Disc found! Looking for mount point...")
        self.root.update()
        
        mount_point = self.find_disc_mount(cdrom)
        
        if not mount_point:
            self.status_label.config(text="Mounting disc...")
            self.root.update()
            mount_point = self.try_mount(cdrom)
            
        if mount_point:
            self.status_label.config(text=f"Disc mounted at: {mount_point}")
            self.root.update()
            self.play_dvd(mount_point)
        else:
            self.status_label.config(text="Could not mount disc")
            messagebox.showinfo(
                "Cannot Access Disc", 
                f"Disc detected but could not be mounted automatically.\n\n"
                f"Try opening your file manager manually to browse the disc.",
                parent=self.root
            )
    
    def play_dvd(self, mount_point):
        """Play DVD using available system players"""
        cdrom_device = self.find_cdrom()
        
        if not self.available_players:
            # No players available
            result = messagebox.askyesno(
                "No Video Player Found",
                "No video player is installed on this system.\n\n"
                "To watch DVDs, you need to install a video player.\n\n"
                "Would you like to install MPV (lightweight player)?\n"
                "Command: sudo apt install mpv",
                parent=self.root
            )
            if result:
                # Try to install mpv
                self.status_label.config(text="Installing MPV...")
                self.root.update()
                try:
                    result = subprocess.run(
                        ["pkexec", "apt", "install", "-y", "mpv"],
                        capture_output=True, text=True, timeout=120
                    )
                    if result.returncode == 0:
                        self.available_players = self.find_system_players()
                        self.status_label.config(text="MPV installed! Playing DVD...")
                        self.play_dvd(mount_point)
                        return
                except Exception as e:
                    messagebox.showerror("Install Failed", f"Could not install MPV:\n{str(e)}", parent=self.root)
            
            # Fall back to file manager
            self.open_file_manager(mount_point)
            return
        
        # Find best player for DVD
        # Priority: mpv (best DVD support), mplayer, vlc, ffplay
        preferred_order = ['mpv', 'mplayer', 'vlc', 'ffplay', 'totem', 'parole']
        selected_player = None
        
        for player in preferred_order:
            if player in self.available_players:
                selected_player = player
                break
        
        if not selected_player:
            selected_player = list(self.available_players.keys())[0]
        
        self.status_label.config(text=f"Playing DVD with {self.available_players[selected_player]}...")
        
        # Play with selected player using raw DVD device
        try:
            if selected_player == 'mpv':
                # MPV has excellent DVD support
                self.external_player = subprocess.Popen(
                    ["mpv", f"dvd://", f"--dvd-device={cdrom_device}", "--fs"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
            elif selected_player == 'mplayer':
                self.external_player = subprocess.Popen(
                    ["mplayer", "dvd://", f"-dvd-device", cdrom_device, "-fs"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
            elif selected_player == 'vlc':
                self.external_player = subprocess.Popen(
                    ["vlc", f"dvd://{cdrom_device}", "-f"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
            elif selected_player == 'ffplay':
                # ffplay doesn't do DVD menus well, try to play VOBs
                video_ts = os.path.join(mount_point, 'VIDEO_TS')
                if os.path.exists(video_ts):
                    vobs = sorted([f for f in os.listdir(video_ts) if f.upper().endswith('.VOB') and not f.upper().startswith('VIDEO_TS')])
                    if vobs:
                        self.external_player = subprocess.Popen(
                            ["ffplay", "-fs", "-autoexit", os.path.join(video_ts, vobs[0])],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            start_new_session=True
                        )
                    else:
                        raise Exception("No VOB files found")
                else:
                    raise Exception("No VIDEO_TS folder found")
            else:
                # Generic fallback - just open the mount point
                self.external_player = subprocess.Popen(
                    [selected_player, mount_point],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
            
            self.status_label.config(text=f"Playing DVD with {self.available_players[selected_player]} (close player window when done)")
            
            # Monitor player
            def monitor_player():
                if self.external_player:
                    return_code = self.external_player.wait()
                    if return_code != 0:
                        self.root.after(0, lambda: self.status_label.config(text="DVD playback failed - check console for errors"))
                    else:
                        self.root.after(0, lambda: self.status_label.config(text="DVD playback finished"))
            
            threading.Thread(target=monitor_player, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Playback Error", f"Could not play DVD:\n{str(e)}", parent=self.root)
            self.open_file_manager(mount_point)
    
    def handle_dvd_error(self, error_msg):
        """Handle DVD playback errors"""
        self.status_label.config(text="DVD playback failed")
        
        if "libdvdcss" in error_msg.lower() or "css" in error_msg.lower():
            messagebox.showinfo(
                "DVD Encrypted",
                "This DVD is encrypted and cannot be played.\n\n"
                "To play encrypted DVDs, you need libdvdcss:\n"
                "sudo apt install libdvd-pkg\n"
                "sudo dpkg-reconfigure libdvd-pkg\n\n"
                "Or install VLC which includes DVD support:\n"
                "sudo apt install vlc",
                parent=self.root
            )
        elif "no input" in error_msg.lower() or "could not open" in error_msg.lower():
            messagebox.showinfo(
                "Cannot Read DVD",
                "Cannot read the DVD.\n\n"
                "The disc may be:\n"
                "- Damaged or dirty\n"
                "- In an unsupported format\n"
                "- Not a video DVD\n\n"
                "Try cleaning the disc or using 'Open File' to browse its contents.",
                parent=self.root
            )
        else:
            # Just show the raw error for debugging
            print(f"DVD Error: {error_msg}")
            messagebox.showinfo(
                "Playback Failed",
                "Could not play the DVD.\n\n"
                "The player closed unexpectedly.\n"
                "Try using 'Open File' to browse the disc contents.",
                parent=self.root
            )
    
    def play(self):
        if not self.current_media:
            self.status_label.config(text="No media loaded")
            return
            
        self.stop()
        
        self.status_label.config(text=f"Loading: {os.path.basename(self.current_media)}...")
        self.root.update()
        
        if self.is_audio_file(self.current_media):
            self.play_audio(self.current_media)
        elif self.is_video_file(self.current_media):
            self.play_video(self.current_media)
        else:
            self.status_label.config(text="Unknown file type")
            result = messagebox.askyesno(
                "Unknown File Type",
                f"Cannot play: {os.path.basename(self.current_media)}\n\n"
                "Open in file manager instead?",
                parent=self.root
            )
            if result:
                self.open_file_manager(self.current_media)
    
    def stop(self):
        self.playing = False
        try:
            import pygame
            pygame.mixer.music.stop()
        except:
            pass
        
        # Kill external player if running
        if self.external_player and self.external_player.poll() is None:
            self.external_player.terminate()
            try:
                self.external_player.wait(timeout=2)
            except:
                self.external_player.kill()
            self.external_player = None
        
        self.status_label.config(text="Stopped")
    
    def play_audio(self, filepath):
        """Play audio file using pygame"""
        try:
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
            self.playing = True
            self.status_label.config(text=f"Playing: {os.path.basename(filepath)}")
            
            def check_done():
                while self.playing and pygame.mixer.music.get_busy():
                    time.sleep(0.5)
                if self.playing:
                    self.playing = False
                    self.status_label.config(text="Finished")
            
            threading.Thread(target=check_done, daemon=True).start()
            
        except Exception as e:
            self.status_label.config(text="Audio playback failed")
            messagebox.showerror("Playback Error", f"Cannot play audio file:\n{str(e)}", parent=self.root)
    
    def play_video(self, filepath):
        """Play video file using OpenCV"""
        try:
            import cv2
            from PIL import Image, ImageTk
            
            # Suppress all OpenCV errors completely
            devnull = open(os.devnull, 'w')
            old_stderr = sys.stderr
            sys.stderr = devnull
            
            cap = cv2.VideoCapture(filepath)
            
            sys.stderr = old_stderr
            devnull.close()
            
            if not cap.isOpened():
                self.status_label.config(text="Cannot open video")
                messagebox.showerror("Error", "Cannot open video file\nThe file format may not be supported.", parent=self.root)
                return
            
            self.playing = True
            self.status_label.config(text=f"Playing: {os.path.basename(filepath)}")
            
            def video_loop():
                errors = 0
                while self.playing:
                    try:
                        ret, frame = cap.read()
                        if not ret:
                            break
                        
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        display_width = max(self.video_frame.winfo_width(), 320)
                        display_height = max(self.video_frame.winfo_height(), 240)
                        frame = cv2.resize(frame, (display_width, display_height))
                        
                        img = Image.fromarray(frame)
                        imgtk = ImageTk.PhotoImage(image=img)
                        
                        self.root.after(0, lambda i=imgtk: self.update_video_frame(i))
                        
                        time.sleep(0.033)
                        errors = 0
                    except Exception:
                        errors += 1
                        if errors > 10:
                            break
                        time.sleep(0.1)
                
                cap.release()
                if self.playing:
                    self.playing = False
                    self.root.after(0, lambda: self.status_label.config(text="Finished"))
            
            self.video_thread = threading.Thread(target=video_loop, daemon=True)
            self.video_thread.start()
            
        except Exception as e:
            self.status_label.config(text="Video playback failed")
            messagebox.showerror("Playback Error", f"Cannot play video file:\n{str(e)}\n\nMake sure opencv-python is installed.", parent=self.root)
    
    def update_video_frame(self, imgtk):
        self.video_label.imgtk = imgtk
        self.video_label.configure(image=imgtk)
    
    def is_audio_file(self, filepath):
        return filepath.lower().endswith(('.mp3', '.wav', '.flac', '.ogg', '.m4a'))
    
    def is_video_file(self, filepath):
        return filepath.lower().endswith(('.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv'))
    
    def open_file_manager(self, path):
        file_managers = [
            ["nautilus", path],
            ["dolphin", path],
            ["thunar", path],
            ["pcmanfm", path],
            ["caja", path],
            ["nemo", path],
            ["xdg-open", path],
        ]
        for fm in file_managers:
            try:
                subprocess.Popen(fm, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            except FileNotFoundError:
                continue
        return False
    
    def disc_has_media(self, device):
        try:
            block_device = os.path.basename(os.path.realpath(device))
            size_file = f'/sys/block/{block_device}/size'
            if os.path.exists(size_file):
                with open(size_file, 'r') as f:
                    size = int(f.read().strip())
                    if size > 1000:
                        return True
        except:
            pass
        return False
    
    def try_mount(self, device):
        # Method 1: udisksctl
        try:
            result = subprocess.run(
                ["udisksctl", "mount", "-b", device],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                output = result.stdout.strip()
                if " at " in output:
                    mount_point = output.split(" at ")[-1].rstrip(".")
                    if os.path.exists(mount_point) and os.access(mount_point, os.R_OK):
                        return mount_point
        except:
            pass
        
        # Method 2: Check common mount points
        time.sleep(1)
        import getpass
        user = getpass.getuser()
        user_paths = [
            f'/media/{user}',
            f'/run/media/{user}',
            '/media',
            '/mnt',
            '/run/media',
        ]
        
        for common_path in user_paths:
            if os.path.exists(common_path) and os.access(common_path, os.R_OK):
                try:
                    for item in os.listdir(common_path):
                        full_path = os.path.join(common_path, item)
                        if os.path.isdir(full_path):
                            try:
                                files = os.listdir(full_path)
                                if files:
                                    return full_path
                            except:
                                pass
                except (PermissionError, OSError):
                    continue
        
        mount_point = self.find_disc_mount(device)
        if mount_point and os.path.exists(mount_point) and os.access(mount_point, os.R_OK):
            return mount_point
            
        return None
    
    def find_disc_mount(self, device):
        try:
            with open('/proc/mounts', 'r') as f:
                for line in f:
                    parts = line.split()
                    if parts[0] == device or parts[0].startswith(device):
                        return parts[1]
        except:
            pass
        return None
            
    def find_cdrom(self):
        for path in ["/dev/cdrom", "/dev/dvd", "/dev/sr0"]:
            if os.path.exists(path):
                return path
        return None

if __name__ == "__main__":
    root = tk.Tk()
    app = MediaPlayer(root)
    root.mainloop()
