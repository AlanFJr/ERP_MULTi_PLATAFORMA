import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from datetime import datetime

# Importa os nossos módulos criados nos passos anteriores
import config
import database
from shopee_client import ShopeeClient

VALID_USERNAME=config.VALID_USERNAME
VALID_PASSWORD=config.VALID_PASSWORD    
LOGIN_WIDTH = 560
LOGIN_HEIGHT = 460


class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.success = False
        self.title("Login - ERP Shopee")
        self.geometry(f"{LOGIN_WIDTH}x{LOGIN_HEIGHT}")
        self.minsize(LOGIN_WIDTH, LOGIN_HEIGHT)
        self.resizable(False, False)
        self.configure(bg="#0f172a")
        self.protocol("WM_DELETE_WINDOW", self._handle_close)
        self._build_ui()
        self._center()

    def _build_ui(self):
        container = tk.Frame(self, bg="#1e293b", padx=30, pady=30)
        container.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        tk.Label(container, text="Bem-vindo", bg="#1e293b", fg="#f8fafc",
                 font=("Segoe UI", 14, "bold")).pack(pady=(0, 10))
        tk.Label(container, text="Informe suas credenciais", bg="#1e293b",
                 fg="#94a3b8", font=("Segoe UI", 10)).pack(pady=(0, 15))

        tk.Label(container, text="Usuário", bg="#1e293b", fg="#cbd5f5").pack(anchor="w")
        self.ent_user = ttk.Entry(container)
        self.ent_user.pack(fill=tk.X, pady=(0, 10))

        tk.Label(container, text="Senha", bg="#1e293b", fg="#cbd5f5").pack(anchor="w")
        self.ent_pass = ttk.Entry(container, show="*")
        self.ent_pass.pack(fill=tk.X, pady=(0, 15))
        self.ent_pass.bind("<Return>", lambda _: self._attempt_login())

        ttk.Button(container, text="Entrar", command=self._attempt_login).pack(fill=tk.X)
        self.ent_user.focus_set()

    def _center(self):
        self.update_idletasks()
        width = self.winfo_width() or LOGIN_WIDTH
        height = self.winfo_height() or LOGIN_HEIGHT
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _attempt_login(self):
        username = self.ent_user.get().strip()
        password = self.ent_pass.get().strip()

        if username == VALID_USERNAME and password == VALID_PASSWORD:
            self.success = True
            self.destroy()
        else:
            messagebox.showerror("Acesso negado", "Usuário ou senha incorretos.")

    def _handle_close(self):
        self.success = False
        self.destroy()

class ERPApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # 1. Configurações da Janela
        self.title("Sistema ERP Integrado - Shopee & Estoque Local")
        self.geometry("1000x700")
        self.configure(bg="#f0f2f5") # Fundo cinza claro moderno
        
        # 2. Inicializa o Cliente Shopee
        self.shopee = ShopeeClient()
        
        # 3. Constroi a Interface
        self.setup_styles()
        self.create_layout()
        
        # 4. Carrega os dados iniciais assim que abre
        self.after(100, self.refresh_data)

    def setup_styles(self):
        """Define cores e fontes para ficar com cara de software profissional."""
        style = ttk.Style()
        style.theme_use('clam') # Tema mais limpo que o padrão do Windows
        
        # Estilo da Tabela
        style.configure("Treeview", 
                        background="white",
                        fieldbackground="white", 
                        foreground="#333",
                        rowheight=30,
                        font=('Segoe UI', 10))
        
        style.configure("Treeview.Heading", 
                        font=('Segoe UI', 10, 'bold'), 
                        background="#e1e4e8")
        
        # Estilo do Botão Principal
        style.configure("Accent.TButton", 
                        background="#2563eb", 
                        foreground="white", 
                        font=('Segoe UI', 10, 'bold'))
        style.map("Accent.TButton", background=[("active", "#1d4ed8")])

    def create_layout(self):
        # --- PAINEL ESQUERDO (MENU) ---
        left_panel = tk.Frame(self, bg="#1e293b", width=220)
        left_panel.pack(side=tk.LEFT, fill=tk.Y)
        
        # Logo / Título
        tk.Label(left_panel, text="ERP MASTER", bg="#1e293b", fg="white", 
                 font=("Arial Black", 16)).pack(pady=(30, 10))
        
        tk.Label(left_panel, text="Gestão Multi-Canal", bg="#1e293b", fg="#94a3b8", 
                 font=("Segoe UI", 10)).pack(pady=(0, 30))
        
        # Botão Recarregar
        btn_refresh = tk.Button(left_panel, text="🔄 Recarregar Tabela", 
                                bg="#334155", fg="white", bd=0, 
                                font=("Segoe UI", 11), pady=10,
                                activebackground="#475569", activeforeground="white",
                                command=self.refresh_data)
        btn_refresh.pack(fill=tk.X, padx=10)

        # --- PAINEL DIREITO (CONTEÚDO) ---
        main_panel = tk.Frame(self, bg="#f0f2f5")
        main_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Cabeçalho
        header = tk.Frame(main_panel, bg="white", height=60, padx=20)
        header.pack(fill=tk.X)
        tk.Label(header, text="Controle de Estoque Unificado", 
                 font=("Segoe UI", 16, "bold"), bg="white", fg="#1e293b").pack(side=tk.LEFT, pady=15)

        # Área Central
        content = tk.Frame(main_panel, padx=20, pady=20, bg="#f0f2f5")
        content.pack(fill=tk.BOTH, expand=True)

        # 1. Tabela de Produtos (Treeview)
        cols = ("sku", "nome", "estoque", "shopee_id", "status")
        self.tree = ttk.Treeview(content, columns=cols, show="headings", height=12)
        
        # Cabeçalhos
        self.tree.heading("sku", text="SKU (Código)")
        self.tree.heading("nome", text="Produto")
        self.tree.heading("estoque", text="Qtd. Local")
        self.tree.heading("shopee_id", text="ID Shopee")
        self.tree.heading("status", text="Status Sync")
        
        # Larguras
        self.tree.column("sku", width=120)
        self.tree.column("nome", width=300)
        self.tree.column("estoque", width=80, anchor="center")
        self.tree.column("shopee_id", width=120, anchor="center")
        self.tree.column("status", width=150, anchor="center")
        
        # Scrollbar
        scroller = ttk.Scrollbar(content, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroller.set)
        
        self.tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        scroller.place(relx=0.985, rely=0.0, relheight=1.0, anchor="ne")

        # 2. Área de Ação (Input e Botão)
        action_frame = tk.Frame(content, bg="white", padx=15, pady=10)
        action_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(action_frame, text="Novo Estoque:", bg="white", font=("Segoe UI", 11)).pack(side=tk.LEFT)
        
        self.ent_qty = ttk.Entry(action_frame, width=10, font=("Segoe UI", 11))
        self.ent_qty.pack(side=tk.LEFT, padx=10)
        
        # Botão de Ação
        self.btn_update = ttk.Button(action_frame, text="ATUALIZAR & SINCRONIZAR", 
                                     style="Accent.TButton", 
                                     command=self.start_update_thread)
        self.btn_update.pack(side=tk.LEFT)

        # 3. Console de Logs
        log_frame = tk.LabelFrame(content, text="Logs do Sistema", bg="#f0f2f5", font=("Segoe UI", 10, "bold"))
        log_frame.pack(fill=tk.X)
        
        self.log_widget = scrolledtext.ScrolledText(log_frame, height=6, state='disabled', 
                                                    bg="#1e293b", fg="#00ff00", font=("Consolas", 9))
        self.log_widget.pack(fill=tk.X)

    def log(self, message):
        """Escreve uma mensagem no console preto da aplicação."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_widget.config(state='normal')
        self.log_widget.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_widget.see(tk.END) # Rola para o final
        self.log_widget.config(state='disabled')

    def refresh_data(self):
        """Busca dados frescos do MySQL e preenche a tabela."""
        self.log("Buscando dados atualizados do banco...")
        
        # Limpa tabela atual
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Busca do database.py
        produtos = database.get_all_products()
        
        for p in produtos:
            shopee_id = p['shopee_id'] if p['shopee_id'] else "---"
            
            self.tree.insert("", "end", values=(
                p['sku'],
                p['nome'],
                p['estoque_real'],
                shopee_id,
                "Aguardando"
            ))
            
        self.log(f"Tabela atualizada. {len(produtos)} produtos carregados.")

    def start_update_thread(self):
        """
        Inicia a atualização numa thread separada.
        Isso impede que a janela congele enquanto fala com a Shopee.
        """
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Atenção", "Selecione um produto na tabela para atualizar.")
            return
            
        qty_str = self.ent_qty.get()
        if not qty_str.isdigit():
            messagebox.showerror("Erro", "Digite um número inteiro válido para o estoque.")
            return
            
        # Bloqueia botão para evitar duplo clique
        self.btn_update.config(state="disabled")
        
        # INICIA A THREAD
        t = threading.Thread(target=self.process_update, args=(selected[0], int(qty_str)))
        t.start()

    def process_update(self, item_iid, new_qty):
        """
        Lógica pesada: Atualiza MySQL -> Atualiza Shopee -> Atualiza Interface.
        Executada em segundo plano.
        """
        try:
            # Pega dados da linha selecionada
            current_values = self.tree.item(item_iid)['values']
            sku = current_values[0]
            shopee_id = str(current_values[3]) # Converte para string para comparar
            
            self.log(f"--- INICIANDO PROCESSO PARA {sku} ---")
            
            # 1. ATUALIZAÇÃO LOCAL (MySQL)
            self.log(f"Atualizando banco local para {new_qty} un...")
            if database.update_stock(sku, new_qty):
                # Usa 'after' para tocar na GUI de forma segura
                self.after(0, lambda: self.tree.set(item_iid, "estoque", new_qty))
            else:
                self.log("❌ Erro ao atualizar banco local. Abortando.")
                return

            # 2. ATUALIZAÇÃO REMOTA (Shopee)
            if shopee_id != "---" and shopee_id != "None":
                self.log(f"Conectando à API Shopee (Item ID: {shopee_id})...")
                
                # Chama nosso shopee_client.py
                resultado = self.shopee.update_stock(shopee_id, new_qty)
                
                if not resultado.get("error"):
                    self.log(f"✅ SHOPEE ATUALIZADA! Msg: {resultado['msg']}")
                    self.after(0, lambda: self.tree.set(item_iid, "status", "Sincronizado"))
                else:
                    self.log(f"❌ Erro Shopee: {resultado['error']}")
                    self.after(0, lambda: self.tree.set(item_iid, "status", "Erro API"))
            else:
                self.log("ℹ️ Produto não vinculado à Shopee. Apenas local atualizado.")
                self.after(0, lambda: self.tree.set(item_iid, "status", "Local Only"))
                
        except Exception as e:
            self.log(f"❌ ERRO CRÍTICO NA THREAD: {e}")
            
        finally:
            # Reabilita o botão e limpa o campo
            self.after(0, lambda: self.btn_update.config(state="normal"))
            self.after(0, lambda: self.ent_qty.delete(0, tk.END))
            self.log("--- PROCESSO FINALIZADO ---")

if __name__ == "__main__":
    login_window = LoginWindow()
    login_window.mainloop()

    if getattr(login_window, "success", False):
        app = ERPApp()
        app.mainloop()
    else:
        print("Execução encerrada: login não realizado.")