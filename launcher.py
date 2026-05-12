import os, sys, shutil, subprocess, threading
import tkinter as tk
from tkinter import messagebox, filedialog

SERVER_IP   = "194.146.47.49"
SERVER_PORT = 13000
SERVER_NAME = "Callysta2"
SITE_URL    = "http://c2.callysta.com.tr"

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
    import winreg
    paths = [
        r"C:\Gameforge\Metin2",
        r"C:\Program Files\Gameforge\Metin2",
        r"C:\Program Files (x86)\Gameforge\Metin2",
        r"C:\Metin2", r"C:\Games\Metin2",
        os.path.join(os.environ.get("LOCALAPPDATA",""), "Gameforge4d", "Metin2"),
        os.path.join(os.environ.get("PROGRAMFILES",""), "Gameforge", "Metin2"),
        os.path.join(os.environ.get("PROGRAMFILES(X86)",""), "Gameforge", "Metin2"),
    ]
    for hive in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
        for reg_path in [
            r"SOFTWARE\Gameforge4d GmbH\Metin2",
            r"SOFTWARE\WOW6432Node\Gameforge4d GmbH\Metin2"
        ]:
            try:
                key = winreg.OpenKey(hive, reg_path)
                p = winreg.QueryValueEx(key, "InstallPath")[0]
                paths.insert(0, p)
            except: pass
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
        self.geometry("540x440")
        self.resizable(False, False)
        self.configure(bg="#0a0a0f")
        self.metin2_path = tk.StringVar()
        self._build_ui()
        threading.Thread(target=self._auto_detect, daemon=True).start()

    def _build_ui(self):
        tk.Label(self, text="⚔  CALLYSTA2", font=("Georgia",28,"bold"),
                 bg="#0a0a0f", fg="#f0c040").pack(pady=(25,4))
        tk.Label(self, text="Efsane Geri Döndü", font=("Arial",11),
                 bg="#0a0a0f", fg="#8b7355").pack()
        tk.Frame(self, bg="#1a1410", height=1).pack(fill="x", padx=30, pady=12)

        frm = tk.Frame(self, bg="#0a0a0f")
        frm.pack(padx=30, fill="x")
        tk.Label(frm, text="Metin2 Kurulum Klasörü:", bg="#0a0a0f",
                 fg="#a08050", font=("Arial",9)).pack(anchor="w")
        row = tk.Frame(frm, bg="#0a0a0f")
        row.pack(fill="x", pady=4)
        tk.Entry(row, textvariable=self.metin2_path, bg="#0f0f1a",
                 fg="#e0c97f", insertbackground="#e0c97f", relief="flat",
                 font=("Consolas",9), highlightthickness=1,
                 highlightbackground="#2a1f0a",
                 highlightcolor="#8b6914").pack(side="left",fill="x",
                 expand=True,ipady=7,ipadx=6)
        tk.Button(row, text=" ... ", bg="#1a1410", fg="#e0c97f",
                  relief="flat", cursor="hand2", command=self._browse,
                  font=("Arial",9)).pack(side="left", padx=(6,0), ipady=5)

        self.log_box = tk.Text(self, height=9, bg="#080810", fg="#80c080",
                               font=("Consolas",8), relief="flat",
                               state="disabled", highlightthickness=1,
                               highlightbackground="#1a1410")
        self.log_box.pack(padx=30, pady=12, fill="x")

        btn_f = tk.Frame(self, bg="#0a0a0f")
        btn_f.pack(padx=30, fill="x")

        self.patch_btn = tk.Button(btn_f,
            text="⚙  SUNUCUYA BAĞLA  (Patch)",
            bg="#c8860a", fg="#0a0a0f", font=("Arial",11,"bold"),
            relief="flat", cursor="hand2", pady=11,
            command=self._do_patch)
        self.patch_btn.pack(side="left", fill="x", expand=True)

        self.play_btn = tk.Button(btn_f, text="▶ OYNA",
            bg="#1a2a1a", fg="#60c060", font=("Arial",11,"bold"),
            relief="flat", cursor="hand2", pady=11, padx=18,
            command=self._do_play, state="disabled")
        self.play_btn.pack(side="left", padx=(8,0))

        tk.Label(self, text=f"Sunucu: {SERVER_IP}:{SERVER_PORT}   |   {SITE_URL}",
                 bg="#0a0a0f", fg="#2a2010", font=("Arial",8)).pack(pady=(8,0))

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
            self._log("⚙  'SUNUCUYA BAĞLA' butonuna basın.")
        else:
            self._log("⚠  Metin2 bulunamadı.")
            self._log("   Önce Gameforge Launcher ile Metin2'yi kurun.")
            self._log("   Kurulduktan sonra klasörü elle seçin.")

    def _browse(self):
        p = filedialog.askdirectory(title="Metin2 klasörünü seçin")
        if p: self.metin2_path.set(p)

    def _do_patch(self):
        path = self.metin2_path.get().strip()
        if not path or not os.path.isdir(path):
            messagebox.showerror("Hata","Geçerli bir Metin2 klasörü seçin.")
            return
        self.patch_btn.configure(state="disabled", text="⏳ Uygulanıyor...")
        def run():
            try:
                ok = patch_metin2(path, self._log)
                if ok:
                    self._log(f"🎮 {SERVER_NAME} sunucusuna bağlandınız!")
                    self._log("▶ OYNA butonuna basarak oyunu başlatın.")
                    self.play_btn.configure(state="normal", bg="#1a4a1a")
                    self.patch_btn.configure(
                        text="✅ BAĞLANDI — Tekrar patch için tekrar bas",
                        bg="#208b20", fg="#ffffff")
            except Exception as e:
                self._log(f"❌ Hata: {e}")
                self.patch_btn.configure(
                    state="normal",
                    text="⚙  SUNUCUYA BAĞLA  (Patch)",
                    bg="#c8860a", fg="#0a0a0f")
        threading.Thread(target=run, daemon=True).start()

    def _do_play(self):
        path = self.metin2_path.get().strip()
        if not launch_game(path):
            messagebox.showinfo("Bilgi",
                "Oyun başlatılamadı.\n"
                "Metin2 klasörünü kontrol edin\n"
                "veya metin2client.exe'yi elle çalıştırın.")

if __name__ == "__main__":
    App().mainloop()
