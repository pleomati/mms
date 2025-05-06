import subprocess
import time
import re
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import datetime
import configparser
import os
import threading
import platform
from PIL import Image, ImageTk
import webbrowser

def set_icon(root, icon_path):
        try:
            # Dla Windows
            if os.name == 'nt':
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('ModernMusicScheduler')
                
            # Standardowe ładowanie ikony
            img = Image.open(icon_path)
            icon_photo = ImageTk.PhotoImage(img)
            root.iconphoto(False, icon_photo)
            # Przechowuj referencję
            root.icon_photo = icon_photo
            return True
        except Exception as e:
            print(f"Error setting icon: {e}")
            return False

class ModernMusicPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Modern Music Scheduler")
        self.root.geometry("800x630")
        self.root.minsize(700, 580)
        self.root.configure(bg='#2d2d2d')
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()
        
        self.countdown_var = tk.StringVar()
        self.countdown_var.set("")
        self.setup_ui()
        self.load_config()

        # Inicjalizacja zmiennych
        self.play_button_pressed = False
        self.is_playing = False
        self.process = None
        self.scheduled_time = None
        self.os_type = platform.system()
        self.vlc_path = self.detect_vlc_path()

        # Lista plików muzycznych
        self.music_files = []
        self.current_track_index = 0
        self.playlist_mode = False

    def configure_styles(self):
        """Konfiguruje nowoczesne style dla widgetów"""
        bg_color = '#2d2d2d'
        fg_color = '#ffffff'
        self.style.configure('TFrame', background=bg_color)
        self.style.configure('TLabel', background=bg_color, foreground=fg_color, font=('Segoe UI', 10))
        self.style.configure('TButton', font=('Segoe UI', 10), padding=6)
        self.style.configure('TEntry', fieldbackground='#3d3d3d', foreground=fg_color, insertcolor=fg_color)
        self.style.configure('TLabelFrame', background=bg_color, foreground=fg_color, relief='groove', borderwidth=2)
        self.style.configure('Red.TButton', foreground=fg_color, background='#d9534f')
        self.style.configure('Green.TButton', foreground=fg_color, background='#5cb85c')
        self.style.map('TButton',
                     background=[('active', '#4a4a4a'), ('pressed', '#3a3a3a')],
                     foreground=[('active', fg_color)])
        self.style.map('Red.TButton',
                     background=[('active', '#c9302c'), ('pressed', '#ac2925')])
        self.style.map('Green.TButton',
                     background=[('active', '#449d44'), ('pressed', '#398439')])

    def setup_ui(self):
        # Główny kontener
        self.main_frame = ttk.Frame(self.root, padding="15")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Nagłówek
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        try:
            img = Image.new('RGBA', (48, 48), (45, 45, 45, 0))
            self.logo = ImageTk.PhotoImage(img)
            logo_label = tk.Label(header_frame, image=self.logo, bg='#2d2d2d')
            logo_label.pack(side=tk.LEFT, padx=(0, 10))
        except:
            pass
        title_label = ttk.Label(header_frame, text="Modern Music Scheduler", font=('Segoe UI', 18, 'bold'))
        title_label.pack(side=tk.LEFT)

        # Sekcja pliku - wybór wielu plików
        file_frame = ttk.LabelFrame(self.main_frame, text=" Music Files ", padding=15)
        file_frame.pack(fill=tk.X, pady=10)

        self.file_listbox = tk.Listbox(file_frame, height=4, bg='#3d3d3d', fg='white', selectbackground='#5cb85c')
        self.file_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        btn_frame_files = ttk.Frame(file_frame)
        btn_frame_files.pack(side=tk.LEFT, padx=5)

        add_files_btn = ttk.Button(btn_frame_files, text="Add Files", command=self.add_files)
        add_files_btn.pack(fill=tk.X, pady=2)
        remove_files_btn = ttk.Button(btn_frame_files, text="Remove Selected", command=self.remove_selected_files)
        remove_files_btn.pack(fill=tk.X, pady=2)
        clear_files_btn = ttk.Button(btn_frame_files, text="Clear List", command=self.clear_files)
        clear_files_btn.pack(fill=tk.X, pady=2)

        # Sekcja harmonogramu
        schedule_frame = ttk.LabelFrame(self.main_frame, text=" Schedule ", padding=15)
        schedule_frame.pack(fill=tk.X, pady=10)

        ttk.Label(schedule_frame, text="Date & Time:").pack(side=tk.LEFT)
        self.date_time_entry = ttk.Entry(schedule_frame, width=25)
        self.date_time_entry.pack(side=tk.LEFT, padx=5)

        ttk.Label(schedule_frame, text="or").pack(side=tk.LEFT, padx=10)

        ttk.Label(schedule_frame, text="In minutes:").pack(side=tk.LEFT)
        self.minutes_entry = ttk.Entry(schedule_frame, width=5)
        self.minutes_entry.pack(side=tk.LEFT, padx=5)

        # Sekcja odtwarzania
        control_frame = ttk.Frame(self.main_frame)
        control_frame.pack(fill=tk.X, pady=15)

        self.play_button = ttk.Button(control_frame, text="Schedule Playback", style='Green.TButton', command=self.on_play_button_click)
        self.play_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(control_frame, text="Stop", style='Red.TButton', command=self.stop_playback)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        self.stop_button.config(state=tk.DISABLED)

        # Sekcja statusu
        status_frame = ttk.Frame(self.main_frame)
        status_frame.pack(fill=tk.X, pady=(10, 5))
        self.status_label = ttk.Label(status_frame, text="Ready", font=('Segoe UI', 10, 'italic'))
        self.status_label.pack(side=tk.LEFT)
        self.countdown_label = ttk.Label(status_frame, textvariable=self.countdown_var, font=('Segoe UI', 10, 'bold'))
        self.countdown_label.pack(side=tk.RIGHT)

        # Sekcja ustawień VLC
        settings_frame = ttk.LabelFrame(self.main_frame, text=" Settings ", padding=15)
        settings_frame.pack(fill=tk.X, pady=10)
        ttk.Label(settings_frame, text="VLC Path:").pack(side=tk.LEFT)
        self.vlc_path_entry = ttk.Entry(settings_frame, width=40)
        self.vlc_path_entry.pack(side=tk.LEFT, padx=5)
        vlc_browse_button = ttk.Button(settings_frame, text="Browse", command=self.browse_vlc_path)
        vlc_browse_button.pack(side=tk.LEFT, padx=5)

        # Menu
        self.create_menu()

    def create_menu(self):
        self.menu_bar = tk.Menu(self.root, bg='#3d3d3d', fg='white')
        
        # Menu File
        file_menu = tk.Menu(self.menu_bar, tearoff=0, bg='#3d3d3d', fg='white')
        file_menu.add_command(label="Save Settings", command=self.save_config)
        file_menu.add_command(label="Clear", command=self.clear_fields)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        
        # Menu Help
        help_menu = tk.Menu(self.menu_bar, tearoff=0, bg='#3d3d3d', fg='white')
        help_menu.add_command(label="Download VLC", command=self.download_vlc)
        help_menu.add_command(label="About", command=self.show_about)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=self.menu_bar)

    def download_vlc(self):
        """Otwiera przeglądarkę z linkiem do pobrania VLC"""
        vlc_url = "https://www.videolan.org/vlc/"
        try:
            webbrowser.open_new(vlc_url)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open browser: {str(e)}")

    def detect_vlc_path(self):
        """Automatycznie wykrywa ścieżkę do VLC"""
        if self.os_type == "Windows":
            default_paths = [
                "C:\\Program Files\\VideoLAN\\VLC\\vlc.exe",
                "C:\\Program Files (x86)\\VideoLAN\\VLC\\vlc.exe"
            ]
            for path in default_paths:
                if os.path.exists(path):
                    return path
        else:
            default_paths = [
                "/usr/bin/vlc",
                "/usr/local/bin/vlc"
            ]
            for path in default_paths:
                if os.path.exists(path):
                    return path
        return "vlc"

    def add_files(self):
        files = filedialog.askopenfilenames(
            title="Select Music Files",
            filetypes=[("Audio Files", "*.mp3 *.wav *.ogg *.flac *.aac *.wma"), ("All Files", "*.*")]
        )
        for f in files:
            if f not in self.music_files:
                self.music_files.append(f)
                self.file_listbox.insert(tk.END, os.path.basename(f))
        self.save_config()

    def remove_selected_files(self):
        selected_indices = list(self.file_listbox.curselection())
        for index in reversed(selected_indices):
            del self.music_files[index]
            self.file_listbox.delete(index)
        self.save_config()

    def clear_files(self):
        self.music_files.clear()
        self.file_listbox.delete(0, tk.END)
        self.save_config()

    def browse_vlc_path(self):
        if self.os_type == "Windows":
            filename = filedialog.askopenfilename(title="Locate vlc.exe", filetypes=[("Executable", "*.exe"), ("All Files", "*.*")])
        else:
            filename = filedialog.askopenfilename(title="Locate VLC")
        if filename:
            self.vlc_path_entry.delete(0, tk.END)
            self.vlc_path_entry.insert(0, filename)
            self.vlc_path = filename
            self.save_config()

    def on_play_button_click(self):
        """Obsługa przycisku odtwarzania"""
        self.play_button_pressed = True
        self.save_config()

        # Jeśli użytkownik podał minuty, ustaw czas
        if self.minutes_entry.get():
            try:
                minutes = int(self.minutes_entry.get())
                if minutes <= 0:
                    raise ValueError
                future_time = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
                self.date_time_entry.delete(0, tk.END)
                self.date_time_entry.insert(0, future_time.strftime("%Y-%m-%d %H:%M:%S"))
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number of minutes (greater than 0)")
                return

        # Sprawdź czy są pliki do odtworzenia
        if not self.music_files:
            messagebox.showerror("Error", "No music files added")
            return

        # Ustaw tryb playlisty jeśli jest więcej niż 1 plik
        self.playlist_mode = len(self.music_files) > 1
        self.current_track_index = 0
        self.play_music_at_time()

    def play_music_at_time(self):
        """Rozpoczyna proces odtwarzania"""
        if self.playlist_mode:
            self.schedule_next_track()
        else:
            self.schedule_single_track()

    def schedule_single_track(self):
        """Planowanie odtwarzania pojedynczego pliku"""
        filepath = self.music_files[0]
        date_time_str = self.date_time_entry.get()

        if not self.validate_datetime(date_time_str):
            return

        target_datetime = datetime.datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")
        now = datetime.datetime.now()
        time_difference = target_datetime - now

        if time_difference.total_seconds() < 0:
            messagebox.showerror("Error", "Scheduled time already passed")
            return

        self.scheduled_time = target_datetime
        self.update_countdown()
        self.play_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text=f"Scheduled: {os.path.basename(filepath)} at {target_datetime}")
        threading.Thread(target=self.wait_and_play, daemon=True).start()

    def schedule_next_track(self):
        """Planowanie odtwarzania kolejnego utworu w playliście"""
        if self.current_track_index >= len(self.music_files):
            # Koniec playlisty
            self.status_label.config(text="Playlist finished")
            self.play_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.countdown_var.set("")
            return

        filepath = self.music_files[self.current_track_index]
        date_time_str = self.date_time_entry.get()

        if not os.path.exists(filepath):
            messagebox.showerror("Error", f"File {filepath} does not exist")
            self.current_track_index += 1
            self.schedule_next_track()
            return

        if not self.validate_datetime(date_time_str):
            return

        target_datetime = datetime.datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")
        now = datetime.datetime.now()
        time_difference = target_datetime - now

        if time_difference.total_seconds() < 0:
            # Jeśli czas już minął, odtwarzaj natychmiast
            self.execute_playback(filepath)
        else:
            self.scheduled_time = target_datetime
            self.update_countdown()
            self.status_label.config(text=f"Scheduled: {os.path.basename(filepath)} at {target_datetime}")
            threading.Thread(target=self.wait_and_play_playlist, daemon=True).start()

    def update_countdown(self):
        """Aktualizuje odliczanie czasu do odtwarzania"""
        if hasattr(self, 'scheduled_time') and self.scheduled_time and not self.is_playing:
            remaining = self.scheduled_time - datetime.datetime.now()
            if remaining.total_seconds() > 0:
                total_seconds = int(remaining.total_seconds())
                days = total_seconds // (24 * 3600)
                remaining_seconds = total_seconds % (24 * 3600)
                hours = remaining_seconds // 3600
                remaining_seconds %= 3600
                minutes = remaining_seconds // 60
                seconds = remaining_seconds % 60
                
                if days > 0:
                    self.countdown_var.set(f"Time left: {days}d {hours:02d}:{minutes:02d}:{seconds:02d}")
                else:
                    self.countdown_var.set(f"Time left: {hours:02d}:{minutes:02d}:{seconds:02d}")
                self.root.after(1000, self.update_countdown)
            else:
                self.countdown_var.set("Time to play!")

    def wait_and_play_playlist(self):
        """Czeka na czas odtwarzania dla playlisty"""
        time_to_wait = (self.scheduled_time - datetime.datetime.now()).total_seconds()
        if time_to_wait > 0:
            time.sleep(time_to_wait)
        
        filepath = self.music_files[self.current_track_index]
        self.execute_playback(filepath)
        
        # Przejdź do następnego utworu
        self.current_track_index += 1
        self.schedule_next_track()

    def wait_and_play(self):
        """Czeka na czas i odtwarza pojedynczy plik"""
        time_to_wait = (self.scheduled_time - datetime.datetime.now()).total_seconds()
        if time_to_wait > 0:
            time.sleep(time_to_wait)
        
        filepath = self.music_files[0]
        self.execute_playback(filepath)

    def execute_playback(self, filepath):
        """Wykonuje odtwarzanie pliku"""
        vlc_path = self.vlc_path_entry.get() if self.vlc_path_entry.get() else self.vlc_path
        
        try:
            self.is_playing = True
            self.status_label.config(text=f"Playing: {os.path.basename(filepath)}")
            
            # Upewnij się, że ścieżka do pliku jest poprawnie sformatowana
            # subprocess obsługuje ścieżki z spacjami bez cudzysłowów, jeśli przekazujemy listę
            # Możesz też użyć os.path.abspath, aby mieć pełną ścieżkę
            full_filepath = os.path.abspath(filepath)
            
            # Tworzymy listę argumentów
            command = [vlc_path, "--play-and-exit", full_filepath]
            
            # Uruchamiamy VLC bez shell=True
            self.process = subprocess.Popen(command)
            self.process.wait()
            
            if not self.playlist_mode:
                messagebox.showinfo("Finished", f"Finished playing: {os.path.basename(filepath)}")
            
        except FileNotFoundError:
            messagebox.showerror("Error", f"VLC not found at: {vlc_path}\nPlease check the path.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            self.is_playing = False
            if not self.playlist_mode:
                self.stop_button.config(state=tk.DISABLED)
                self.play_button.config(state=tk.NORMAL)
                self.status_label.config(text="Ready")
                self.countdown_var.set("")
            self.save_config()

    def stop_playback(self):
        """Zatrzymuje odtwarzanie"""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
        
        self.is_playing = False
        self.playlist_mode = False
        self.play_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="Stopped by user")
        self.countdown_var.set("")
        self.save_config()

    def validate_datetime(self, date_time_str):
        """Walidacja formatu daty i czasu"""
        pattern_full = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$"
        pattern_time = r"^\d{2}:\d{2}:\d{2}$"
        
        if re.match(pattern_full, date_time_str):
            try:
                datetime.datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")
                return True
            except ValueError:
                messagebox.showerror("Error", "Invalid date or time format")
                return False
        elif re.match(pattern_time, date_time_str):
            now = datetime.datetime.now()
            full_datetime_str = f"{now.strftime('%Y-%m-%d')} {date_time_str}"
            try:
                datetime.datetime.strptime(full_datetime_str, "%Y-%m-%d %H:%M:%S")
                self.date_time_entry.delete(0, tk.END)
                self.date_time_entry.insert(0, full_datetime_str)
                return True
            except ValueError:
                messagebox.showerror("Error", "Invalid time format")
                return False
        else:
            messagebox.showerror("Error", "Use format YYYY-MM-DD HH:MM:SS or HH:MM:SS")
            return False

    def load_config(self):
        """Wczytuje konfigurację z pliku"""
        config = configparser.ConfigParser()
        config_path = self.get_config_path()
        if os.path.exists(config_path):
            config.read(config_path)
            try:
                # Wczytanie listy plików
                files_str = config['DEFAULT'].get('files', '')
                if files_str:
                    self.music_files = files_str.split(';')
                    # Sprawdź czy pliki istnieją i dodaj do listy
                    self.file_listbox.delete(0, tk.END)
                    valid_files = []
                    for f in self.music_files:
                        abs_path = f
                        if not os.path.isabs(f):
                            abs_path = os.path.join(os.path.dirname(config_path), f)
                        if os.path.exists(abs_path):
                            valid_files.append(abs_path)
                            self.file_listbox.insert(tk.END, os.path.basename(abs_path))
                    self.music_files = valid_files
                # Reszta odczytów
                self.date_time_entry.delete(0, tk.END)
                if 'datetime' in config['DEFAULT']:
                    self.date_time_entry.insert(0, config['DEFAULT']['datetime'])
                # VLC path
                if 'vlc_path' in config['DEFAULT']:
                    self.vlc_path_entry.delete(0, tk.END)
                    self.vlc_path_entry.insert(0, config['DEFAULT']['vlc_path'])
                    self.vlc_path = config['DEFAULT']['vlc_path']
                # Przycisk
                self.play_button_pressed = config.getboolean('DEFAULT', 'play_button_pressed', fallback=False)
                if self.play_button_pressed:
                    self.play_button.config(text="Played")
            except KeyError:
                pass


    def save_config(self):
        """Zapisuje konfigurację do pliku"""
        config = configparser.ConfigParser()
        config['DEFAULT'] = {
            'files': ';'.join(self.music_files),
            'datetime': self.date_time_entry.get(),
            'vlc_path': self.vlc_path_entry.get() if self.vlc_path_entry.get() else self.vlc_path,
            'play_button_pressed': str(self.play_button_pressed)
        }
        config_dir = os.path.dirname(self.get_config_path())
        os.makedirs(config_dir, exist_ok=True)
        with open(self.get_config_path(), 'w') as configfile:
            config.write(configfile)

    def get_config_path(self):
        """Zwraca ścieżkę do pliku konfiguracyjnego"""
        config_dir = os.path.expanduser("~/.modern_music_player")
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        return os.path.join(config_dir, "config.ini")

    def clear_fields(self):
        """Czyści wszystkie pola"""
        self.file_listbox.delete(0, tk.END)
        self.music_files.clear()
        self.date_time_entry.delete(0, tk.END)
        self.minutes_entry.delete(0, tk.END)
        self.play_button.config(text="Schedule Playback", state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="Ready")
        self.countdown_var.set("")
        self.play_button_pressed = False
        self.save_config()

    def show_about(self):
        """Wyświetla informacje o programie"""
        about_text = (
            "Modern Music Scheduler\n"
            "Version 2.0\n\n"
            "Features:\n"
            "- Schedule music playback\n"
            "- Play with delay\n"
            "- Support for multiple formats\n"
            "- Requires VLC media player\n"
            "- Playlist support\n\n"
            "Download VLC from: www.videolan.org\n\n"
            "Author: Adam Pasiak"
        )
        messagebox.showinfo("About", about_text)

if __name__ == "__main__":
    root = tk.Tk()
    icon_path = 'mms.ico'
    if not os.path.exists(icon_path):
        # Spróbuj znaleźć ikonę w różnych lokalizacjach
        icon_path = os.path.join(os.path.dirname(__file__), 'mms.ico')
    
    set_icon(root, icon_path)
    app = ModernMusicPlayer(root)
    root.mainloop()