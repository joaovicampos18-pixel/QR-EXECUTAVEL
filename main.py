import customtkinter as ctk
from supabase import create_client
import qrcode
from PIL import Image, ImageDraw, ImageFont
from fpdf import FPDF
import os
import win32print
import win32api
import tkinter.messagebox as messagebox

# CREDENCIAIS DIRETAS DO JOÃO VITOR
URL_DB = "https://vbrpgqpjujedxkughbgp.supabase.co"
KEY_DB = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZicnBncXBqdWplZHhrdWdoYmdwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzIzNjQwMTMsImV4cCI6MjA4Nzk0MDAxM30.6chioJKrO2gs0W8aWp_XxJlXVZoZhJW8libvlKB8giA"

class AppGerador(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gerador LPN Professional - Joao Vitor Silva")
        self.geometry("1100x700")
        
        # Conexão ao Supabase
        try:
            self.db = create_client(URL_DB, KEY_DB)
            self.prox_cod = self.buscar_ultimo() + 1
        except:
            messagebox.showerror("Erro", "Falha ao conectar ao banco de dados!")
            self.prox_cod = 1

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="LOGÍSTICA LPN", font=("Arial", 22, "bold")).pack(pady=20)
        
        # Menu de Impressoras
        ctk.CTkLabel(self.sidebar, text="Impressora Ativa:", font=("Arial", 12)).pack(pady=(10,0))
        try:
            self.lista_printers = [p[2] for p in win32print.EnumPrinters(2)]
            self.combo_printers = ctk.CTkComboBox(self.sidebar, values=self.lista_printers, width=200)
            self.combo_printers.pack(pady=5, padx=20)
            self.combo_printers.set(win32print.GetDefaultPrinter())
        except:
            ctk.CTkLabel(self.sidebar, text="Nenhuma impressora encontrada", text_color="red").pack()

        # Botões
        ctk.CTkButton(self.sidebar, text="Lote Automático", command=self.tela_auto).pack(pady=10, padx=20)
        ctk.CTkButton(self.sidebar, text="Manual / Lista", command=self.tela_manual).pack(pady=10, padx=20)
        ctk.CTkButton(self.sidebar, text="Etiqueta Larga", command=self.tela_larga).pack(pady=10, padx=20)
        
        ctk.CTkLabel(self.sidebar, text="v2.0 | 2026", font=("Arial", 10)).pack(side="bottom", pady=10)
        ctk.CTkLabel(self.sidebar, text="João Vitor C. L. Silva", font=("Arial", 10, "italic")).pack(side="bottom")

        # Container Central
        self.container = ctk.CTkFrame(self, corner_radius=15)
        self.container.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.tela_auto()

    def buscar_ultimo(self):
        try:
            r = self.db.table("registros_etiquetas").select("fim").order("fim", desc=True).limit(1).execute()
            return int(r.data[0]['fim']) if r.data else 0
        except: return 0

    def f_pad(self, t):
        qr = qrcode.QRCode(box_size=12, border=1)
        qr.add_data(str(t)); qr.make(fit=True)
        img = qr.make_image().convert('RGB')
        cv = Image.new('RGB', (img.size[0]+300, img.size[1]+120), 'white')
        d = ImageDraw.Draw(cv)
        try: f=ImageFont.truetype("arialbd.ttf", 60)
        except: f=ImageFont.load_default()
        d.text((150,20), str(t), fill="black", font=f)
        cv.paste(img, (130, 100))
        return cv

    def imprimir_direto(self, caminho):
        try:
            win32print.SetDefaultPrinter(self.combo_printers.get())
            win32api.ShellExecute(0, "print", caminho, None, ".", 0)
        except Exception as e:
            messagebox.showerror("Erro Impressão", str(e))

    def limpar(self):
        for w in self.container.winfo_children(): w.destroy()

    # --- TELA 1: AUTOMÁTICO ---
    def tela_auto(self):
        self.limpar()
        ctk.CTkLabel(self.container, text="Gerar Sequência Automática", font=("Arial", 24, "bold")).pack(pady=20)
        ctk.CTkLabel(self.container, text=f"Código Inicial (Banco): {self.prox_cod:08d}", text_color="#4A90E2").pack()
        
        self.ent_qtd = ctk.CTkEntry(self.container, placeholder_text="Qtd de Etiquetas", width=200)
        self.ent_qtd.pack(pady=20)
        
        ctk.CTkButton(self.container, text="GERAR E IMPRIMIR LOTE", fg_color="#4A90E2", height=40, command=self.acao_auto).pack()

    def acao_auto(self):
        try:
            q = int(self.ent_qtd.get())
            ini, fim = self.prox_cod, self.prox_cod + q - 1
            pdf = FPDF('L','mm',(65,100))
            for i in range(q):
                pdf.add_page(); pdf.image(self.f_pad(f"{(ini+i):08d}"), 5, 5, 90)
            pdf.output("temp.pdf")
            self.db.table("registros_etiquetas").insert({"inicio":ini,"fim":fim,"quantidade":q}).execute()
            if messagebox.askyesno("Imprimir", "Deseja imprimir agora?"): self.imprimir_direto("temp.pdf")
            self.prox_cod = fim + 1
            self.tela_auto()
        except: messagebox.showerror("Erro", "Insira uma quantidade válida")

    # --- TELA 2: MANUAL / LISTA ---
    def tela_manual(self):
        self.limpar()
        ctk.CTkLabel(self.container, text="Lista de Códigos Personalizados", font=("Arial", 24, "bold")).pack(pady=20)
        self.txt_manual = ctk.CTkTextbox(self.container, width=500, height=300)
        self.txt_manual.pack(pady=10)
        ctk.CTkButton(self.container, text="GERAR E IMPRIMIR LISTA", fg_color="#2ECC71", height=40, command=self.acao_manual).pack()

    def acao_manual(self):
        cods = [c.strip() for c in self.txt_manual.get("1.0", "end").split("\n") if c.strip()]
        if not cods: return
        pdf = FPDF('L','mm',(65,100))
        for c in cods:
            pdf.add_page(); pdf.image(self.f_pad(c), 5, 5, 90)
        pdf.output("temp_man.pdf")
        if messagebox.askyesno("Imprimir", "Enviar lista para impressora?"): self.imprimir_direto("temp_man.pdf")

    # --- TELA 3: LARGA ---
    def tela_larga(self):
        self.limpar()
        ctk.CTkLabel(self.container, text="Etiqueta Larga (7 QRs - 31.5cm)", font=("Arial", 24, "bold")).pack(pady=20)
        self.txt_larga = ctk.CTkTextbox(self.container, width=500, height=200)
        self.txt_larga.pack(pady=10)
        ctk.CTkButton(self.container, text="GERAR LARGA", fg_color="#E67E22", height=40, command=lambda: messagebox.showinfo("Aviso", "Ajuste o papel térmico para 315mm")).pack()

if __name__ == "__main__":
    app = AppGerador()
    app.mainloop()
