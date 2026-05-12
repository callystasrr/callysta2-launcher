import os, sys, shutil, threading, urllib.request, zipfile, tempfile, struct
import tkinter as tk
from tkinter import messagebox, filedialog

SERVER_IP   = "194.146.47.49"
SERVER_PORT = 13000
SERVER_NAME = "Callysta2"
SITE_URL    = "http://c2.callysta.com.tr"
INSTALL_DIR = os.path.join(os.environ.get("PROGRAMFILES","C:\\Program Files"), "Callysta2")

BASE_URL = "https://github.com/callystasrr/callysta2-launcher/releases/download/client-v1.0/"
PARTS = [
    "Callysta2Client.zip.part01",
    "Callysta2Client.zip.part02",
    "Callysta2Client.zip.part03",
    "Callysta2Client.zip.part04",
    "Callysta2Client.zip.part05",
]
TOTAL_SIZE = 2202 * 1024 * 1024  # ~2.2GB

SERVERINFO = f"""import os
SERVER_SETTINGS_LIST = [
    {{
        "name": "{SERVER_NAME}",
        "desc": "{SERVER_NAME} - Efsane Geri Dönüyor",
        "connect": [
            {{
                "name": "{SERVER_NAME} CH1",
                "ip": "{SERVER_IP}",
                "port": {SERVER_PORT},
            }},
        ],
    }},
]
"""

def find_installed():
    paths = [
        INSTALL_DIR,
        os.path.join(os.environ.get("PROGRAMFILES",""), "Callysta2"),
        os.path.join(os.environ.get("PROGRAMFILES(X86)",""), "Callysta2"),
        r"C:\Callysta2", r"C:\Games\Callysta2",
    ]
    for p in paths:
        if os.path.isdir(p) and os.path.exists(os.path.join(p, "metin2client.exe")):
            return p
    return None

def patch_serverinfo(path, log):
    for sub in ["", "tr-TR"]:
        t = os.path.join(path, sub, "serverinfo.py") if sub else os.path.join(path, "serverinfo.py")
        if os.path.exists(t):
            shutil.copy2(t, t+".bak")
    target = os.path.join(path, "serverinfo.py")
    with open(target, "w", encoding="utf-8") as f:
        f.write(SERVERINFO)
    log("✅ serverinfo.py Callysta2'ye bağlandı.")

def launch_game(path):
    for sub in ["", "tr-TR"]:
        for exe in ["metin2client.exe","gsl_metin2.exe","metin2.exe"]:
            full = os.path.join(path, sub, exe) if sub else os.path.join(path, exe)
            if os.path.exists(full):
                os.startfile(full)
                return True
    return False

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{SERVER_NAME} Launcher")
        self.geometry("580x540")
        self.resizable(False, False)
        self.configure(bg="#0a0a0f")
        self.install_path = tk.StringVar(value=INSTALL_DIR)
        self._build_ui()
        threading.Thread(target=self._auto_detect, daemon=True).start()

    def _build_ui(self):
        tk.Label(self, text="⚔  CALLYSTA2", font=("Georgia",28,"bold"),
                 bg="#0a0a0f", fg="#f0c040").pack(pady=(20,3))
        tk.Label(self, text="Efsane Geri Döndü", font=("Arial",10),
                 bg="#0a0a0f", fg="#8b7355").pack()
        tk.Frame(self, bg="#1a1410", height=1).pack(fill="x", padx=30, pady=10)

        # Kurulum yolu
        frm = tk.Frame(self, bg="#0a0a0f")
        frm.pack(padx=30, fill="x")
        tk.Label(frm, text="Kurulum Klasörü:", bg="#0a0a0f",
                 fg="#a08050", font=("Arial",9)).pack(anchor="w")
        row = tk.Frame(frm, bg="#0a0a0f")
        row.pack(fill="x", pady=4)
        tk.Entry(row, textvariable=self.install_path, bg="#0f0f1a",
                 fg="#e0c97f", insertbackground="#e0c97f", relief="flat",
                 font=("Consolas",9), highlightthickness=1,
                 highlightbackground="#2a1f0a",
                 highlightcolor="#8b6914").pack(side="left", fill="x",
                 expand=True, ipady=7, ipadx=6)
        tk.Button(row, text=" ... ", bg="#1a1410", fg="#e0c97f",
                  relief="flat", cursor="hand2", command=self._browse,
                  font=("Arial",9)).pack(side="left", padx=(6,0), ipady=5)

        # Genel progress
        pf = tk.Frame(self, bg="#0a0a0f")
        pf.pack(padx=30, fill="x", pady=(10,0))
        tk.Label(pf, text="Genel İlerleme:", bg="#0a0a0f",
                 fg="#a08050", font=("Arial",9)).pack(anchor="w")
        self.prog_bg = tk.Frame(pf, bg="#0f0f1a", height=24,
                                 highlightthickness=1, highlightbackground="#2a1f0a")
        self.prog_bg.pack(fill="x", pady=3)
        self.prog_bar = tk.Frame(self.prog_bg, bg="#c8860a", height=24, width=0)
        self.prog_bar.place(x=0, y=0, height=24)
        self.prog_lbl = tk.Label(self.prog_bg, text="Hazır", bg="#0f0f1a",
                                  fg="#e0c97f", font=("Arial",9,"bold"))
        self.prog_lbl.place(relx=0.5, rely=0.5, anchor="center")

        # Parça progress
        pf2 = tk.Frame(self, bg="#0a0a0f")
        pf2.pack(padx=30, fill="x", pady=(4,0))
        tk.Label(pf2, text="Mevcut Parça:", bg="#0a0a0f",
                 fg="#a08050", font=("Arial",9)).pack(anchor="w")
        self.part_bg = tk.Frame(pf2, bg="#0f0f1a", height=18,
                                 highlightthickness=1, highlightbackground="#1a1410")
        self.part_bg.pack(fill="x", pady=2)
        self.part_bar = tk.Frame(self.part_bg, bg="#3a5a8a", height=18, width=0)
        self.part_bar.place(x=0, y=0, height=18)
        self.part_lbl = tk.Label(self.part_bg, text="", bg="#0f0f1a",
                                  fg="#a0c0e0", font=("Arial",8))
        self.part_lbl.place(relx=0.5, rely=0.5, anchor="center")

        # Log
        self.log_box = tk.Text(self, height=8, bg="#080810", fg="#80c080",
                               font=("Consolas",8), relief="flat",
                               state="disabled", highlightthickness=1,
                               highlightbackground="#1a1410")
        self.log_box.pack(padx=30, pady=8, fill="x")

        # Butonlar
        bf = tk.Frame(self, bg="#0a0a0f")
        bf.pack(padx=30, fill="x")
        self.install_btn = tk.Button(bf,
            text="⬇  CALLYSTA2 İNDİR VE KUR",
            bg="#c8860a", fg="#0a0a0f", font=("Arial",11,"bold"),
            relief="flat", cursor="hand2", pady=11,
            command=self._do_install)
        self.install_btn.pack(side="left", fill="x", expand=True)
        self.play_btn = tk.Button(bf, text="▶ OYNA",
            bg="#1a2a1a", fg="#60c060", font=("Arial",11,"bold"),
            relief="flat", cursor="hand2", pady=11, padx=18,
            command=self._do_play, state="disabled")
        self.play_btn.pack(side="left", padx=(8,0))

        tk.Label(self, text=f"Sunucu: {SERVER_IP}:{SERVER_PORT}   |   {SITE_URL}",
                 bg="#0a0a0f", fg="#2a2010", font=("Arial",8)).pack(pady=(6,0))

    def _log(self, msg):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg+"\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _set_prog(self, pct, text=None):
        self.prog_bg.update_idletasks()
        w = self.prog_bg.winfo_width()
        self.prog_bar.place(width=int(w * pct / 100))
        self.prog_lbl.configure(text=text or f"{pct:.0f}%")
        if pct >= 100:
            self.prog_bar.configure(bg="#208b20")

    def _set_part(self, pct, text=None):
        self.part_bg.update_idletasks()
        w = self.part_bg.winfo_width()
        self.part_bar.place(width=int(w * pct / 100))
        self.part_lbl.configure(text=text or f"{pct:.0f}%")

    def _auto_detect(self):
        self._log("🔍 Callysta2 aranıyor...")
        p = find_installed()
        if p:
            self.install_path.set(p)
            self._log(f"✅ Kurulu: {p}")
            self._log("▶ Doğrudan OYNA'ya basabilirsiniz.")
            self.play_btn.configure(state="normal", bg="#1a4a1a")
            self.install_btn.configure(text="🔄 Güncelle / Yeniden Kur")
            self._set_prog(100, "Kurulu ✅")
        else:
            self._log("⚠  Callysta2 kurulu değil.")
            self._log("   'İNDİR VE KUR' butonuna basın.")

    def _browse(self):
        p = filedialog.askdirectory(title="Kurulum klasörü seçin")
        if p: self.install_path.set(p)

    def _do_install(self):
        install_dir = self.install_path.get().strip()
        if not install_dir:
            messagebox.showerror("Hata", "Kurulum klasörü seçin.")
            return
        self.install_btn.configure(state="disabled", text="⏳ İşleniyor...")

        def run():
            try:
                os.makedirs(install_dir, exist_ok=True)
                tmp = tempfile.gettempdir()
                part_files = []

                # Parçaları indir
                for i, part in enumerate(PARTS):
                    url  = BASE_URL + part
                    dest = os.path.join(tmp, part)
                    part_files.append(dest)

                    # Daha önce indirilmiş mi?
                    if os.path.exists(dest) and os.path.getsize(dest) > 100*1024*1024:
                        self._log(f"⏭ {part} zaten var, atlanıyor.")
                        self._set_prog(
                            (i / len(PARTS)) * 70,
                            f"Parça {i+1}/{len(PARTS)} mevcut")
                        continue

                    self._log(f"⬇ [{i+1}/{len(PARTS)}] {part} indiriliyor...")
                    downloaded = 0

                    def hook(b, bs, total, _i=i, _part=part):
                        nonlocal downloaded
                        downloaded = b * bs
                        part_pct = min(downloaded / max(total,1) * 100, 100)
                        dl_mb = downloaded / (1024**2)
                        tot_mb = total / (1024**2)
                        self._set_part(part_pct,
                            f"{_part}: {dl_mb:.0f} / {tot_mb:.0f} MB")
                        overall = (_i / len(PARTS) + part_pct / 100 / len(PARTS)) * 70
                        self._set_prog(overall,
                            f"İndiriliyor... Parça {_i+1}/{len(PARTS)}")

                    urllib.request.urlretrieve(url, dest, hook)
                    self._log(f"✅ {part} tamamlandı.")

                # Birleştir
                self._log("🔗 Parçalar birleştiriliyor...")
                self._set_prog(72, "Birleştiriliyor...")
                zip_path = os.path.join(tmp, "Callysta2Client.zip")
                with open(zip_path, "wb") as out:
                    for pf in part_files:
                        self._log(f"   + {os.path.basename(pf)}")
                        with open(pf, "rb") as f:
                            shutil.copyfileobj(f, out)
                self._log("✅ Birleştirme tamamlandı!")
                self._set_prog(75, "Birleştirildi ✅")

                # Ayıkla
                self._log(f"📦 Ayıklanıyor → {install_dir}")
                self._set_prog(78, "Ayıklanıyor...")
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    members = zf.namelist()
                    total = len(members)
                    for idx, m in enumerate(members):
                        target = m[len("tr-TR/"):] if m.startswith("tr-TR/") else m
                        if not target: continue
                        dest = os.path.join(install_dir, target)
                        if m.endswith("/"):
                            os.makedirs(dest, exist_ok=True)
                        else:
                            os.makedirs(os.path.dirname(dest), exist_ok=True)
                            with zf.open(m) as src, open(dest,"wb") as dst:
                                shutil.copyfileobj(src, dst)
                        if idx % 100 == 0:
                            pct = 78 + (idx/total)*20
                            self._set_prog(pct, f"Ayıklanıyor... {idx}/{total}")

                self._log("✅ Ayıklama tamamlandı!")

                # Patch
                patch_serverinfo(install_dir, self._log)
                self._set_prog(100, "Kurulum tamamlandı! ✅")
                self._log(f"🎮 {SERVER_NAME} hazır! OYNA butonuna bas.")

                self.play_btn.configure(state="normal", bg="#1a4a1a")
                self.install_btn.configure(
                    text="🔄 Güncelle / Yeniden Kur",
                    bg="#208b20", fg="#ffffff", state="normal")

                # Temp temizle
                try:
                    os.remove(zip_path)
                    for pf in part_files:
                        os.remove(pf)
                except: pass

            except Exception as e:
                self._log(f"❌ Hata: {e}")
                self.install_btn.configure(
                    state="normal",
                    text="⬇  CALLYSTA2 İNDİR VE KUR",
                    bg="#c8860a", fg="#0a0a0f")

        threading.Thread(target=run, daemon=True).start()

    def _do_play(self):
        install_dir = self.install_path.get().strip()
        if not launch_game(install_dir):
            messagebox.showinfo("Bilgi",
                "Oyun başlatılamadı.\n"
                "metin2client.exe'yi elle çalıştırın.")

if __name__ == "__main__":
    App().mainloop()
