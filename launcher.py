import os, sys, shutil, threading, urllib.request, zipfile, tempfile
import tkinter as tk
from tkinter import messagebox, filedialog

SERVER_IP     = "194.146.47.49"
SERVER_PORT   = 13000
SERVER_NAME   = "Callysta2"
SITE_URL      = "http://c2.callysta.com.tr"
CLIENT_URL    = "http://c2.callysta.com.tr/downloads/Callysta2Client.zip"
INSTALL_DIR   = os.path.join(os.environ.get("PROGRAMFILES","C:\\Program Files"), "Callysta2")

SERVERINFO = f"""import os
SERVER_SETTINGS_LIST = [
    {{
        "name": "{SERVER_NAME}",
        "desc": "{SERVER_NAME} - Efsane Geri Dönuyor",
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
        r"C:\Callysta2",
        r"C:\Games\Callysta2",
    ]
    for p in paths:
        if os.path.isdir(p) and os.path.exists(os.path.join(p, "metin2client.exe")):
            return p
    return None

def patch_serverinfo(path, log):
    for sub in ["", "tr-TR"]:
        t = os.path.join(path, sub, "serverinfo.py") if sub else os.path.join(path, "serverinfo.py")
        if os.path.exists(t):
            shutil.copy2(t, t + ".bak")
            with open(t, "w", encoding="utf-8") as f:
                f.write(SERVERINFO)
            log(f"✅ serverinfo.py güncellendi.")
            return True
    # Yoksa oluştur
    t = os.path.join(path, "serverinfo.py")
    with open(t, "w", encoding="utf-8") as f:
        f.write(SERVERINFO)
    log(f"✅ serverinfo.py oluşturuldu.")
    return True

def launch_game(path):
    for sub in ["", "tr-TR"]:
        for exe in ["metin2client.exe", "metin2.exe", "gsl_metin2.exe"]:
            full = os.path.join(path, sub, exe) if sub else os.path.join(path, exe)
            if os.path.exists(full):
                os.startfile(full)
                return True
    return False

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{SERVER_NAME} Launcher")
        self.geometry("560x520")
        self.resizable(False, False)
        self.configure(bg="#0a0a0f")
        self.install_path = tk.StringVar(value=INSTALL_DIR)
        self.cancel_flag = False
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

        # Progress bar
        self.progress_frame = tk.Frame(self, bg="#0a0a0f")
        self.progress_frame.pack(padx=30, fill="x", pady=(8,0))
        tk.Label(self.progress_frame, text="İndirme İlerlemesi:",
                 bg="#0a0a0f", fg="#a08050", font=("Arial",9)).pack(anchor="w")
        self.progress_bg = tk.Frame(self.progress_frame, bg="#0f0f1a",
                                     height=22, highlightthickness=1,
                                     highlightbackground="#2a1f0a")
        self.progress_bg.pack(fill="x", pady=3)
        self.progress_bar = tk.Frame(self.progress_bg, bg="#c8860a", height=22, width=0)
        self.progress_bar.place(x=0, y=0, height=22)
        self.progress_label = tk.Label(self.progress_bg, text="0%",
                                        bg="#0f0f1a", fg="#e0c97f",
                                        font=("Arial",8))
        self.progress_label.place(relx=0.5, rely=0.5, anchor="center")

        # Log kutusu
        self.log_box = tk.Text(self, height=9, bg="#080810", fg="#80c080",
                               font=("Consolas",8), relief="flat",
                               state="disabled", highlightthickness=1,
                               highlightbackground="#1a1410")
        self.log_box.pack(padx=30, pady=10, fill="x")

        # Butonlar
        btn_f = tk.Frame(self, bg="#0a0a0f")
        btn_f.pack(padx=30, fill="x")

        self.install_btn = tk.Button(btn_f,
            text="⬇  CALLYSTA2 İNDİR VE KUR",
            bg="#c8860a", fg="#0a0a0f", font=("Arial",11,"bold"),
            relief="flat", cursor="hand2", pady=11,
            command=self._do_install)
        self.install_btn.pack(side="left", fill="x", expand=True)

        self.play_btn = tk.Button(btn_f, text="▶ OYNA",
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

    def _set_progress(self, pct, text=None):
        total_w = self.progress_bg.winfo_width()
        bar_w = int(total_w * pct / 100)
        self.progress_bar.place(x=0, y=0, height=22, width=bar_w)
        lbl = text or f"{pct:.1f}%"
        self.progress_label.configure(text=lbl)
        if pct >= 100:
            self.progress_bar.configure(bg="#208b20")

    def _auto_detect(self):
        self._log("🔍 Callysta2 aranıyor...")
        p = find_installed()
        if p:
            self.install_path.set(p)
            self._log(f"✅ Kurulu bulundu: {p}")
            self._log("▶ OYNA butonuna basabilirsiniz.")
            self.play_btn.configure(state="normal", bg="#1a4a1a")
            self.install_btn.configure(text="🔄 Güncelle / Yeniden Kur")
        else:
            self._log("⚠  Callysta2 kurulu değil.")
            self._log(f"   Kurulum klasörü: {INSTALL_DIR}")
            self._log("   'İNDİR VE KUR' butonuna basın.")

    def _browse(self):
        p = filedialog.askdirectory(title="Kurulum klasörü seçin")
        if p:
            self.install_path.set(p)

    def _do_install(self):
        install_dir = self.install_path.get().strip()
        if not install_dir:
            messagebox.showerror("Hata", "Kurulum klasörü seçin.")
            return
        self.install_btn.configure(state="disabled", text="⏳ İndiriliyor...")
        self.cancel_flag = False

        def run():
            try:
                os.makedirs(install_dir, exist_ok=True)
                zip_path = os.path.join(tempfile.gettempdir(), "Callysta2Client.zip")

                # İndir
                self._log(f"⬇ İndiriliyor: {CLIENT_URL}")
                self._log(f"   Boyut: ~2.2 GB — lütfen bekleyin...")

                def progress(block, block_size, total):
                    if total > 0:
                        pct = min(block * block_size / total * 100, 100)
                        dl  = block * block_size / (1024**3)
                        tot = total / (1024**3)
                        self._set_progress(pct, f"{dl:.2f} / {tot:.2f} GB  ({pct:.0f}%)")

                urllib.request.urlretrieve(CLIENT_URL, zip_path, progress)
                self._log("✅ İndirme tamamlandı!")
                self._set_progress(100, "İndirme tamamlandı!")

                # Aç
                self._log(f"📦 Ayıklanıyor → {install_dir}")
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    members = zf.namelist()
                    total = len(members)
                    for i, m in enumerate(members):
                        # tr-TR/ prefix'ini kaldır, direkt install_dir'e aç
                        target = m
                        if m.startswith("tr-TR/"):
                            target = m[len("tr-TR/"):]
                        if not target:
                            continue
                        dest = os.path.join(install_dir, target)
                        if m.endswith("/"):
                            os.makedirs(dest, exist_ok=True)
                        else:
                            os.makedirs(os.path.dirname(dest), exist_ok=True)
                            with zf.open(m) as src, open(dest, "wb") as dst:
                                shutil.copyfileobj(src, dst)
                        pct = (i+1) / total * 100
                        if i % 50 == 0:
                            self._set_progress(pct, f"Ayıklanıyor... {pct:.0f}%")

                self._log("✅ Ayıklama tamamlandı!")

                # Patch
                patch_serverinfo(install_dir, self._log)
                self._log(f"🎮 {SERVER_NAME} kurulumu tamamlandı!")
                self._log("▶ OYNA butonuna basarak başlatın!")
                self._set_progress(100, "Kurulum tamamlandı! ✅")

                self.play_btn.configure(state="normal", bg="#1a4a1a")
                self.install_btn.configure(
                    text="🔄 Güncelle / Yeniden Kur",
                    bg="#208b20", fg="#ffffff", state="normal")

                # Temp zip sil
                try: os.remove(zip_path)
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
                "Kurulum klasörünü kontrol edin\n"
                "veya metin2client.exe'yi elle çalıştırın.")

if __name__ == "__main__":
    App().mainloop()
