"""
Weather Online Installer - ONEDIR versie
Versie: 1.3.0
Auteur: Rog294super

Kleine installer die de ONEDIR versie (instant startup) downloadt en installeert.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import zipfile
import subprocess
import threading
from pathlib import Path
import shutil

GITHUB_REPO = "Rog294super/Weather-App"
VERSION = "1.3.0"


class InstallerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Weather Installer v{VERSION}")
        self.root.geometry("600x450")
        self.root.resizable(False, False)
        self.root.configure(bg="#2b2b2b")
        
        # Variables
        self.install_path = tk.StringVar()
        self.install_path.set(str(Path.home() / "Weather"))
        self.progress_var = tk.DoubleVar(value=0)
        self.status_text = tk.StringVar(value="Klaar om te installeren")
        
        self.create_ui()
    
    def create_ui(self):
        # Header
        header = tk.Label(self.root, text="🎮 Weather Installer", 
                         font=("Arial", 20, "bold"), bg="#2b2b2b", fg="#4a90e2")
        header.pack(pady=20)
        
        # Info
        info = tk.Label(self.root, 
                       text="Deze installer downloadt en installeert Weather\n"
                            "met instant startup (< 0.5 seconde) 🚀",
                       bg="#2b2b2b", fg="white", font=("Arial", 10), justify=tk.CENTER)
        info.pack(pady=10)
        
        # Feature highlights
        features_frame = tk.Frame(self.root, bg="#3a3a3a", relief=tk.RAISED, bd=2)
        features_frame.pack(padx=20, pady=10, fill=tk.X)
        
        features = [
            "⚡ Instant startup (0.3-0.5s)",
            "🎯 Automatische sneltoets setup",
            "🔄 Auto-update functie",
            "📁 Keuze van installatie locatie"
        ]
        
        for feature in features:
            tk.Label(features_frame, text=feature, bg="#3a3a3a", fg="white",
                    font=("Arial", 9), anchor=tk.W).pack(padx=10, pady=2, anchor=tk.W)
        
        # Install path
        path_frame = tk.LabelFrame(self.root, text="Installatielocatie", 
                                  bg="#2b2b2b", fg="white", font=("Arial", 11, "bold"))
        path_frame.pack(padx=20, pady=10, fill=tk.X)
        
        path_subframe = tk.Frame(path_frame, bg="#2b2b2b")
        path_subframe.pack(padx=10, pady=10, fill=tk.X)
        
        path_entry = tk.Entry(path_subframe, textvariable=self.install_path, 
                             font=("Arial", 10), bg="#3a3a3a", fg="white")
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        tk.Button(path_subframe, text="📁", command=self.browse_path,
                 bg="#4a90e2", fg="white", font=("Arial", 10, "bold"),
                 relief=tk.FLAT, cursor="hand2", width=3).pack(side=tk.RIGHT)
        
        # Progress
        progress_frame = tk.Frame(self.root, bg="#2b2b2b")
        progress_frame.pack(padx=20, pady=10, fill=tk.X)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate',
                                           variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.status_label = tk.Label(progress_frame, textvariable=self.status_text,
                                     bg="#2b2b2b", fg="#aaaaaa", font=("Arial", 9))
        self.status_label.pack()
        
        # Buttons
        btn_frame = tk.Frame(self.root, bg="#2b2b2b")
        btn_frame.pack(pady=20)
        
        self.install_btn = tk.Button(btn_frame, text="⬇️ Installeren", 
                                     command=self.start_install,
                                     bg="#28a745", fg="white", font=("Arial", 12, "bold"),
                                     relief=tk.FLAT, cursor="hand2", padx=30, pady=10)
        self.install_btn.pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="❌ Annuleren", command=self.root.quit,
                 bg="#dc3545", fg="white", font=("Arial", 12, "bold"),
                 relief=tk.FLAT, cursor="hand2", padx=30, pady=10).pack(side=tk.LEFT, padx=5)
    
    def browse_path(self):
        path = filedialog.askdirectory(title="Selecteer installatielocatie")
        if path:
            self.install_path.set(path)
    
    def update_progress(self, value, text):
        self.progress_var.set(value)
        self.status_text.set(text)
        self.root.update()
    
    def start_install(self):
        self.install_btn.config(state=tk.DISABLED)
        threading.Thread(target=self.install_thread, daemon=True).start()
    
    def install_thread(self):
        try:
            install_dir = Path(self.install_path.get())
            
            # Step 1: Create directory
            self.update_progress(5, "Map aanmaken...")
            install_dir.mkdir(parents=True, exist_ok=True)
            
            # Step 2: Get latest release info
            self.update_progress(10, "Laatste versie ophalen...")
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                raise Exception("Kon geen release informatie ophalen")
            
            data = response.json()
            
            # Step 3: Zoek ONEDIR ZIP (geprefereerd) of maak van losse bestanden
            self.update_progress(15, "Bestanden zoeken...")
            
            # Zoek eerst naar ONEDIR ZIP
            onedir_zip = None
            for asset in data.get("assets", []):
                name = asset["name"].lower()
                # Zoek naar "onedir", "fast", of folder structure ZIP
                if name.endswith(".zip") and any(x in name for x in ["onedir", "fast", "folder"]):
                    onedir_zip = asset
                    break
            
            if onedir_zip:
                # Download ONEDIR ZIP
                self.update_progress(20, "Downloaden ONEDIR versie...")
                zip_path = install_dir / "Weather_onedir.zip"
                self.download_file(onedir_zip["browser_download_url"], zip_path, 20, 70)
                
                # Extract
                self.update_progress(70, "Uitpakken...")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    # Extract en zoek de Weather folder binnen ZIP
                    members = zip_ref.namelist()
                    
                    # Check of er een Weather/ folder in zit
                    has_Weather_folder = any(m.startswith('Weather/') for m in members)
                    
                    if has_Weather_folder:
                        # Extract alles, dan verplaats Weather folder inhoud naar root
                        temp_extract = install_dir / "_temp_extract"
                        temp_extract.mkdir(exist_ok=True)
                        zip_ref.extractall(temp_extract)
                        
                        # Verplaats Weather folder inhoud
                        Weather_folder = temp_extract / "Weather"
                        if Weather_folder.exists():
                            for item in Weather_folder.iterdir():
                                dest = install_dir / item.name
                                if dest.exists():
                                    if dest.is_dir():
                                        shutil.rmtree(dest)
                                    else:
                                        dest.unlink()
                                shutil.move(str(item), str(dest))
                        
                        # Cleanup
                        shutil.rmtree(temp_extract)
                    else:
                        # Direct extract
                        zip_ref.extractall(install_dir)
                
                zip_path.unlink()
                
            else:
                # Geen ONEDIR ZIP gevonden, gebruik fallback naar EXE download
                self.update_progress(20, "ONEDIR niet beschikbaar, download standalone...")
                
                exe_asset = next((a for a in data["assets"] if a["name"].endswith(".exe") and "Installer" not in a["name"]), None)
                if not exe_asset:
                    raise Exception("Geen installeerbaar bestand gevonden")
                
                # Download .exe
                exe_path = install_dir / "Weather.exe"
                self.download_file(exe_asset["browser_download_url"], exe_path, 20, 80)
                
                # Download updater als beschikbaar
                updater_asset = next((a for a in data["assets"] if "updater" in a["name"].lower() and a["name"].endswith(".exe")), None)
                if updater_asset:
                    self.update_progress(80, "Updater downloaden...")
                    updater_path = install_dir / "updater.exe"
                    self.download_file(updater_asset["browser_download_url"], updater_path, 80, 85)
            
            # Step 4: Create default config
            self.update_progress(85, "Configuratie aanmaken...")
            self.create_default_config(install_dir)
            
            # Step 5: Create shortcut
            self.update_progress(90, "Snelkoppeling aanmaken...")
            self.create_shortcut(install_dir)
            
            # Step 6: Create uninstaller
            self.update_progress(95, "Uninstaller aanmaken...")
            self.create_uninstaller(install_dir)
            
            # Done!
            self.update_progress(100, "Installatie voltooid! 🎉")
            
            self.root.after(100, lambda: self.show_complete_dialog(install_dir))
            
        except Exception as e:
            self.root.after(100, lambda: messagebox.showerror("Fout", f"Installatie mislukt:\n{e}"))
            self.install_btn.config(state=tk.NORMAL)
            self.update_progress(0, "Installatie mislukt")
    
    def download_file(self, url, dest_path, progress_start, progress_end):
        """Download bestand met progress indicator"""
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size)
                        progress = progress_start + (progress_end - progress_start) * percent
                        size_mb = downloaded / (1024 * 1024)
                        total_mb = total_size / (1024 * 1024)
                        self.update_progress(progress, f"Downloaden... {size_mb:.1f} MB / {total_mb:.1f} MB")
    
    def create_default_config(self, install_dir):
        """Maak standaard config.json"""
        config = {
            "toetsen": {
                "positie_1": "ctrl+shift+1",
                "positie_2": "ctrl+shift+2",
                "positie_3": "ctrl+shift+3",
                "positie_4": "ctrl+shift+4",
                "positie_5": "ctrl+shift+5",
                "stadsfeest": "ctrl+shift+l",
                "zegetocht": "ctrl+shift+b",
                "stadsfeest_zegetocht": "ctrl+shift+x",
                "boerendorp": "ctrl+shift+u",
                "start": "ctrl+shift+f",
                "stop": "ctrl+shift+v"
            },
            "snelheid": 0.3,
            "boerendorpen": {
                "aantal": 6,
                "locaties": [],
                "loyaliteit_onderzocht": False,
                "wachttijd": "10m"
            }
        }
        
        import json
        config_path = install_dir / "config.json"
        if not config_path.exists():
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
    
    def create_shortcut(self, install_dir):
        """Maak desktop shortcut"""
        try:
            desktop = Path.home() / "Desktop"
            shortcut_path = desktop / "Weather.lnk"
            
            # Zoek Weather.exe (kan in subdirectory zitten bij ONEDIR)
            exe_path = install_dir / "Weather.exe"
            
            if not exe_path.exists():
                # Zoek in Weather subfolder
                alt_path = install_dir / "Weather" / "Weather.exe"
                if alt_path.exists():
                    exe_path = alt_path
            
            if exe_path.exists():
                # Windows shortcut via PowerShell
                ps_script = f"""
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{exe_path}"
$Shortcut.WorkingDirectory = "{exe_path.parent}"
$Shortcut.Save()
"""
                subprocess.run(["powershell", "-Command", ps_script], 
                             capture_output=True, timeout=5)
        except:
            pass  # Niet kritisch
    
    def create_uninstaller(self, install_dir):
        """Maak eenvoudige uninstaller batch script"""
        try:
            uninstall_script = f"""@echo off
echo Weather Uninstaller
echo.
echo Dit verwijdert Weather van je computer.
echo.
pause
echo.
echo Verwijderen...
cd ..
rmdir /s /q "{install_dir.name}"
del "%USERPROFILE%\\Desktop\\Weather.lnk" 2>nul
echo.
echo Weather is verwijderd.
pause
"""
            uninstall_path = install_dir / "Uninstall.bat"
            with open(uninstall_path, 'w') as f:
                f.write(uninstall_script)
        except:
            pass
    
    def show_complete_dialog(self, install_dir):
        """Toon voltooiings dialog"""
        # Zoek exe locatie
        exe_path = install_dir / "Weather.exe"
        if not exe_path.exists():
            alt_path = install_dir / "Weather" / "Weather.exe"
            if alt_path.exists():
                exe_path = alt_path
        
        result = messagebox.askyesno(
            "Installatie Voltooid! 🎉",
            f"Weather is geïnstalleerd in:\n{install_dir}\n\n"
            f"✨ Instant startup actief! (< 0.5s)\n\n"
            f"Wil je Weather nu starten?"
        )
        
        if result and exe_path.exists():
            subprocess.Popen([str(exe_path)], cwd=str(exe_path.parent))
        
        self.root.quit()


def main():
    root = tk.Tk()
    app = InstallerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
