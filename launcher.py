import os, sys, shutil, threading, webbrowser
import tkinter as tk
from tkinter import messagebox, filedialog

SERVER_IP   = "194.146.47.49"
SERVER_PORT = 13000
SERVER_NAME = "Callysta2"
SITE_URL    = "http://c2.callysta.com.tr"
GAMEFORGE_URL = "https://www.gameforge.com/tr-TR/download/metin2"

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

def find_metin2():
    try:
        import winreg
        for hive in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
            for reg_path in [
                r"SOFTWARE\Gameforge4d GmbH\Metin2",
                r"SOFTWARE\WOW6432Node\Gameforge4d GmbH\Metin2"
            ]:
                try:
                    key = winreg.OpenKey(hive, reg_path)
                    p = winreg.QueryValueEx(key, "InstallPath")[0]
                    if os.path.isdir(p): return p
                except: pass
    except: pass

    paths = [
        r"C:\Gameforge\Metin2",
        r"C:\Program Files\Gameforge\Metin2",
        r"C:\Program Files (x86)\Gameforge\Metin2",
        r"C:\Metin2", r"C:\Games\Metin2",
        os.path.join(os.environ.get("LOCALAPPDATA",""), "Gameforge4d", "Metin2"),
        os.path.join(os.environ.get("PROGRAMFILES",""), "Gameforge", "Metin2"),
        os.path.join(os.environ.get("PROGRAMFILES(X86)",""), "Gameforge", "Metin2"),
    ]
    for p in paths:
        if os.path.isdir(p) and any(
            os.path.exists(os.path.join(p, x))
            for x in ["metin2client.exe","metin2.exe","serverinfo.py"]
        ):
            return p
    return None

def patch_metin2(path, log):
    candidates = [
        os.path.join(path, "serverinfo.py"),
        os.path.join(path, "pack", "serverinfo.py"),
        os.path.join(path, "data", "serverinfo.py"),
    ]
    patched = False
    for t in candidates:
        if os.path.exists(t):
            shutil.copy2(t, t + ".bak")
            with open(t, "w", encoding="utf-8") as f:
                f.write(SERVERINFO)
            log(f"✅ Güncellendi: {t}")
            patched = True
    if not patched:
        t = os.path.join(path, "serverinfo.py")
        with open(t, "w", encoding="utf-8") as f:
            f.write(SERVERINFO)
        log(f"✅ Oluşturuldu: {t}")
        patched = True
    return patched

def launch_game(path):
    for exe in ["metin2client.exe","metin2.exe","Metin2.exe","game.exe"]:
        full = os.path.join(path, exe)
        if os.path.exists(full):
            os.startfile(full)
            return True
    return False

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{SERVER_NAME} Launcher")
        self.geometry("560x580")
        self.resizable(False, False)
        self.configure(bg="#0a0a0f")
        self.metin2_path = tk.StringVar()
        self.step = tk.IntVar(value=0)
        self._build_ui()
        threading.Thread(target=self._auto_detect, daemon=True).start()

    def _build_ui(self):
        # Başlık
        tk.Label(self, text="⚔  CALLYSTA2", font=("Georgia",28,"bold"),
                 bg="#0a0a0f", fg="#f0c040").pack(pady=(20,3))
        tk.Label(self, text="Efsane Geri Döndü", font=("Arial",10),
                 bg="#0a0a0f", fg="#8b7355").pack()
        tk.Frame(self, bg="#1a1410", height=1).pack(fill="x", padx=30, pady=12)

        # Adımlar
        steps_frame = tk.Frame(self, bg="#0a0a0f")
        steps_frame.pack(padx=30, fill="x", pady=(0,10))

        self.step_labels = []
        steps = [
            ("1", "Metin2'yi İndir ve Kur"),
            ("2", "Kurulum Klasörünü Seç"),
            ("3", "Sunucuya Bağlan"),
            ("4", "Oyna!"),
        ]
        for i, (num, text) in enumerate(steps):
            row = tk.Frame(steps_frame, bg="#0a0a0f")
            row.pack(fill="x", pady=2)
            circle = tk.Label(row, text=num, width=2,
                font=("Arial",9,"bold"), bg="#1a1410", fg="#8b7355",
                relief="flat", padx=6, pady=3)
            circle.pack(side="left")
            lbl = tk.Label(row, text=text, font=("Arial",10),
                bg="#0a0a0f", fg="#6a5a3a", anchor="w")
            lbl.pack(side="left", padx=10)
            self.step_labels.append((circle, lbl))

        self._update_steps(0)

        tk.Frame(self, bg="#1a1410", height=1).pack(fill="x", padx=30, pady=8)

        # ADIM 1 — Gameforge indir butonu
        self.gf_frame = tk.Frame(self, bg="#0a0a0f")
        self.gf_frame.pack(padx=30, fill="x", pady=4)
        tk.Label(self.gf_frame, text="Adım 1 — Metin2'yi Resmi Siteden İndir:",
                 bg="#0a0a0f", fg="#a08050", font=("Arial",9)).pack(anchor="w", pady=(0,5))
        self.gf_btn = tk.Button(self.gf_frame,
            text="🌐  Gameforge'dan İndir  (Ücretsiz)",
            bg="#1a2a3a", fg="#60a0e0", font=("Arial",10,"bold"),
            relief="flat", cursor="hand2", pady=9,
            command=lambda: webbrowser.open(GAMEFORGE_URL))
        self.gf_btn.pack(fill="x")
        tk.Label(self.gf_frame,
            text="↑ Tıkla → Gameforge Launcher'ı kur → Metin2'yi indir → Kur → Geri dön",
            bg="#0a0a0f", fg="#3a3020", font=("Arial",8)).pack(pady=(3,0))

        tk.Frame(self, bg="#1a1410", height=1).pack(fill="x", padx=30, pady=8)

        # ADIM 2 — Klasör seç
        frm = tk.Frame(self, bg="#0a0a0f")
        frm.pack(padx=30, fill="x")
        tk.Label(frm, text="Adım 2 — Metin2 Kurulum Klasörü:",
                 bg="#0a0a0f", fg="#a08050", font=("Arial",9)).pack(anchor="w", pady=(0,5))
        row = tk.Frame(frm, bg="#0a0a0f")
        row.pack(fill="x")
        tk.Entry(row, textvariable=self.metin2_path, bg="#0f0f1a",
                 fg="#e0c97f", insertbackground="#e0c97f", relief="flat",
                 font=("Consolas",9), highlightthickness=1,
                 highlightbackground="#2a1f0a",
                 highlightcolor="#8b6914").pack(side="left", fill="x",
                 expand=True, ipady=7, ipadx=6)
        tk.Button(row, text=" ... ", bg="#1a1410", fg="#e0c97f",
                  relief="flat", cursor="hand2", command=self._browse,
                  font=("Arial",9)).pack(side="left", padx=(6,0), ipady=5)

        # Log kutusu
        self.log_box = tk.Text(self, height=6, bg="#080810", fg="#80c080",
                               font=("Consolas",8), relief="flat",
                               state="disabled", highlightthickness=1,
                               highlightbackground="#1a1410")
        self.log_box.pack(padx=30, pady=10, fill="x")

        # ADIM 3+4 — Patch ve Oyna butonları
        btn_f = tk.Frame(self, bg="#0a0a0f")
        btn_f.pack(padx=30, fill="x")

        self.patch_btn = tk.Button(btn_f,
            text="⚙  Adım 3 — SUNUCUYA BAĞLA",
            bg="#c8860a", fg="#0a0a0f", font=("Arial",11,"bold"),
            relief="flat", cursor="hand2", pady=11,
            command=self._do_patch)
        self.patch_btn.pack(side="left", fill="x", expand=True)

        self.play_btn = tk.Button(btn_f,
            text="▶ OYNA",
            bg="#1a2a1a", fg="#60c060", font=("Arial",11,"bold"),
            relief="flat", cursor="hand2", pady=11, padx=18,
            command=self._do_play, state="disabled")
        self.play_btn.pack(side="left", padx=(8,0))

        tk.Label(self,
            text=f"Sunucu: {SERVER_IP}:{SERVER_PORT}   |   {SITE_URL}",
            bg="#0a0a0f", fg="#2a2010", font=("Arial",8)).pack(pady=(8,0))

    def _update_steps(self, current):
        colors = {
            "done":   ("#208b20", "#40c040"),
            "active": ("#c8860a", "#f0c040"),
            "wait":   ("#1a1410", "#4a3a20"),
        }
        for i, (circle, lbl) in enumerate(self.step_labels):
            if i < current:
                c, t = colors["done"]
                circle.configure(text="✓", bg=c, fg="#ffffff")
            elif i == current:
                c, t = colors["active"]
                circle.configure(text=str(i+1), bg=c, fg="#0a0a0f")
            else:
                c, t = colors["wait"]
                circle.configure(text=str(i+1), bg=c, fg="#4a3a20")
            lbl.configure(fg=t)

    def _log(self, msg):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg+"\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _auto_detect(self):
        self._log("🔍 Metin2 aranıyor...")
        p = find_metin2()
        if p:
            self.metin2_path.set(p)
            self._log(f"✅ Metin2 bulundu: {p}")
            self._update_steps(2)
        else:
            self._log("⚠  Metin2 bulunamadı.")
            self._log("   Adım 1'deki butona tıklayarak Metin2'yi indirin ve kurun.")
            self._log("   Kurulum bittikten sonra klasörü elle seçebilirsiniz.")
            self._update_steps(0)

    def _browse(self):
        p = filedialog.askdirectory(title="Metin2 klasörünü seçin")
        if p:
            self.metin2_path.set(p)
            self._update_steps(2)

    def _do_patch(self):
        path = self.metin2_path.get().strip()
        if not path or not os.path.isdir(path):
            messagebox.showerror("Hata", "Geçerli bir Metin2 klasörü seçin.\n"
                "Önce Adım 1'den Metin2'yi indirip kurun.")
            return
        self.patch_btn.configure(state="disabled", text="⏳ Uygulanıyor...")
        self._update_steps(2)
        def run():
            try:
                ok = patch_metin2(path, self._log)
                if ok:
                    self._log(f"🎮 {SERVER_NAME} sunucusuna bağlandınız!")
                    self._log("▶ OYNA butonuna basarak oyunu başlatın.")
                    self._update_steps(3)
                    self.play_btn.configure(state="normal", bg="#1a4a1a")
                    self.patch_btn.configure(
                        text="✅ BAĞLANDI",
                        bg="#208b20", fg="#ffffff")
            except Exception as e:
                self._log(f"❌ Hata: {e}")
                self.patch_btn.configure(
                    state="normal",
                    text="⚙  Adım 3 — SUNUCUYA BAĞLA",
                    bg="#c8860a", fg="#0a0a0f")
        threading.Thread(target=run, daemon=True).start()

    def _do_play(self):
        path = self.metin2_path.get().strip()
        self._update_steps(4)
        if not launch_game(path):
            messagebox.showinfo("Bilgi",
                "Oyun başlatılamadı.\n"
                "Metin2 klasörünü kontrol edin\n"
                "veya metin2client.exe'yi elle çalıştırın.")

if __name__ == "__main__":
    App().mainloop()
