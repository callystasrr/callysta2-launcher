# Bu script Windows'ta çalışacak launcher kodunu üretir
# Sunucuda sadece PyInstaller ile exe yapacağız

launcher_code = '''
import os, sys, shutil, winreg, subprocess, tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading, urllib.request, json

SERVER_IP   = "194.146.47.49"
SERVER_PORT = 13000
SERVER_NAME = "Callysta2"
SITE_URL    = "http://c2.callysta.com.tr"

SERVERINFO = """import os
SERVER_SETTINGS_LIST = [
    {{
        "name": "{name}",
        "desc": "{name} - Efsane Geri Dönüyor",
        "connect": [
            {{
                "name": "{name} CH1",
                "ip": "{ip}",
                "port": {port},
            }},
        ],
    }},
]
""".format(name=SERVER_NAME, ip=SERVER_IP, port=SERVER_PORT)

def find_metin2():
    """Metin2 kurulum yolunu bul"""
    paths = [
        r"C:\\\\Gameforge\\\\Metin2",
        r"C:\\\\Program Files\\\\Gameforge\\\\Metin2",
        r"C:\\\\Program Files (x86)\\\\Gameforge\\\\Metin2",
        r"C:\\\\Metin2",
        r"C:\\\\Games\\\\Metin2",
        os.path.join(os.environ.get("LOCALAPPDATA",""), "Gameforge4d", "Metin2"),
        os.path.join(os.environ.get("PROGRAMFILES",""), "Gameforge", "Metin2"),
        os.path.join(os.environ.get("PROGRAMFILES(X86)",""), "Gameforge", "Metin2"),
    ]
    # Registry\'den bul
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\\\Gameforge4d GmbH\\\\Metin2")
        path = winreg.QueryValueEx(key, "InstallPath")[0]
        paths.insert(0, path)
    except: pass
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\\\WOW6432Node\\\\Gameforge4d GmbH\\\\Metin2")
        path = winreg.QueryValueEx(key, "InstallPath")[0]
        paths.insert(0, path)
    except: pass
    
    for p in paths:
        if os.path.exists(p) and (
            os.path.exists(os.path.join(p, "metin2client.exe")) or
            os.path.exists(os.path.join(p, "metin2.exe")) or
            os.path.exists(os.path.join(p, "serverinfo.py"))
        ):
            return p
    return None

def patch_metin2(path, log_fn):
    """serverinfo.py\'yi yaz"""
    targets = [
        os.path.join(path, "serverinfo.py"),
        os.path.join(path, "pack", "serverinfo.py"),
        os.path.join(path, "data", "serverinfo.py"),
    ]
    patched = 0
    for t in targets:
        if os.path.exists(t):
            # Yedek al
            shutil.copy2(t, t + ".bak_original")
            with open(t, "w", encoding="utf-8") as f:
                f.write(SERVERINFO)
            log_fn(f"✅ Güncellendi: {t}")
            patched += 1
    if patched == 0:
        # Yoksa ana dizine yaz
        target = os.path.join(path, "serverinfo.py")
        with open(target, "w", encoding="utf-8") as f:
            f.write(SERVERINFO)
        log_fn(f"✅ Oluşturuldu: {target}")
        patched += 1
    return patched > 0

def launch_game(path):
    exes = ["metin2client.exe", "metin2.exe", "game.exe", "Metin2.exe"]
    for exe in exes:
        full = os.path.join(path, exe)
        if os.path.exists(full):
            os.startfile(full)
            return True
    return False

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{SERVER_NAME} Launcher")
        self.geometry("520x420")
        self.resizable(False, False)
        self.configure(bg="#0a0a0f")
        self.metin2_path = tk.StringVar()
        self._build_ui()
        threading.Thread(target=self._auto_detect, daemon=True).start()

    def _build_ui(self):
        # Başlık
        tk.Label(self, text="⚔ CALLYSTA2", font=("Georgia", 28, "bold"),
                 bg="#0a0a0f", fg="#f0c040").pack(pady=(25,5))
        tk.Label(self, text="Efsane Geri Döndü", font=("Arial", 11),
                 bg="#0a0a0f", fg="#8b7355").pack()
        tk.Label(self, text="─" * 60, bg="#0a0a0f", fg="#1a1410").pack(pady=10)

        # Yol
        frm = tk.Frame(self, bg="#0a0a0f")
        frm.pack(padx=30, fill="x")
        tk.Label(frm, text="Metin2 Kurulum Klasörü:", bg="#0a0a0f",
                 fg="#a08050", font=("Arial", 9)).pack(anchor="w")
        row = tk.Frame(frm, bg="#0a0a0f")
        row.pack(fill="x", pady=4)
        tk.Entry(row, textvariable=self.metin2_path, bg="#0f0f1a",
                 fg="#e0c97f", insertbackground="#e0c97f",
                 relief="flat", font=("Consolas", 9), bd=0,
                 highlightthickness=1, highlightbackground="#2a1f0a",
                 highlightcolor="#8b6914").pack(side="left", fill="x", expand=True, ipady=6, ipadx=6)
        tk.Button(row, text="...", bg="#1a1410", fg="#e0c97f",
                  relief="flat", cursor="hand2", command=self._browse,
                  font=("Arial", 9), padx=8).pack(side="left", padx=(5,0))

        # Log kutusu
        self.log = tk.Text(self, height=8, bg="#080810", fg="#80c080",
                           font=("Consolas", 8), relief="flat",
                           state="disabled", bd=0,
                           highlightthickness=1, highlightbackground="#1a1410")
        self.log.pack(padx=30, pady=15, fill="x")

        # Butonlar
        btn_frame = tk.Frame(self, bg="#0a0a0f")
        btn_frame.pack(padx=30, pady=5, fill="x")

        self.patch_btn = tk.Button(btn_frame, text="⚙ SUNUCUYA BAĞLA",
            bg="#c8860a", fg="#0a0a0f", font=("Arial", 11, "bold"),
            relief="flat", cursor="hand2", padx=20, pady=10,
            command=self._do_patch)
        self.patch_btn.pack(side="left", fill="x", expand=True)

        self.play_btn = tk.Button(btn_frame, text="▶ OYNA",
            bg="#1a1410", fg="#e0c97f", font=("Arial", 11, "bold"),
            relief="flat", cursor="hand2", padx=20, pady=10,
            command=self._do_play, state="disabled")
        self.play_btn.pack(side="left", padx=(10,0))

        # Alt bilgi
        tk.Label(self, text=f"Sunucu: {SERVER_IP}:{SERVER_PORT}  |  {SITE_URL}",
                 bg="#0a0a0f", fg="#3a3020", font=("Arial", 8)).pack(pady=(10,0))

    def _log(self, msg):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _auto_detect(self):
        self._log("🔍 Metin2 aranıyor...")
        path = find_metin2()
        if path:
            self.metin2_path.set(path)
            self._log(f"✅ Metin2 bulundu: {path}")
        else:
            self._log("⚠️  Metin2 bulunamadı. Klasörü elle seçin.")
            self._log("   Gameforge launcher ile önce Metin2\'yi kurun.")

    def _browse(self):
        path = filedialog.askdirectory(title="Metin2 klasörünü seçin")
        if path:
            self.metin2_path.set(path)

    def _do_patch(self):
        path = self.metin2_path.get().strip()
        if not path or not os.path.isdir(path):
            messagebox.showerror("Hata", "Geçerli bir Metin2 klasörü seçin.")
            return
        self.patch_btn.configure(state="disabled", text="⏳ İşleniyor...")
        self._log(f"⚙ Patch uygulanıyor: {path}")
        def run():
            ok = patch_metin2(path, self._log)
            if ok:
                self._log(f"🎮 {SERVER_NAME} sunucusuna bağlandınız!")
                self._log("▶ Şimdi OYNA butonuna basabilirsiniz.")
                self.play_btn.configure(state="normal", bg="#20803a")
                self.patch_btn.configure(text="✅ BAĞLANDI", bg="#208b20")
            else:
                self._log("❌ Hata oluştu. Klasörü kontrol edin.")
                self.patch_btn.configure(state="normal", text="⚙ SUNUCUYA BAĞLA")
        threading.Thread(target=run, daemon=True).start()

    def _do_play(self):
        path = self.metin2_path.get().strip()
        if not launch_game(path):
            messagebox.showinfo("Bilgi", "Oyun başlatılamadı.\\nMetin2 klasörünü kontrol edin veya oyunu elle başlatın.")

if __name__ == "__main__":
    App().mainloop()
'''

with open("/home/metin2/launcher/callysta2_launcher.py", "w") as f:
    f.write(launcher_code)

print("Launcher kodu yazıldı.")
