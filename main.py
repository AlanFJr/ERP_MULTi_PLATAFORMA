import json
from pathlib import Path

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from datetime import datetime

# Importa os nossos módulos criados nos passos anteriores
import config
import database
from shopee_client import ShopeeClient

LOGIN_WIDTH = 560
LOGIN_HEIGHT = 460
TREE_COLUMNS = ("sku", "nome", "estoque", "shopee_id", "status")


class UserStore:
    """Armazena usuários com acesso limitado em um arquivo JSON local."""

    def __init__(self, file_path="users.json", default_username=None, default_password=None):
        self.path = Path(file_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.default_username = default_username
        self.default_password = default_password
        self._ensure_storage()

    def _ensure_storage(self):
        if self.path.exists():
            return

        initial_users = []
        if self.default_username and self.default_password:
            initial_users.append({
                "username": self.default_username,
                "password": self.default_password,
                "role": "limited"
            })

        self._save_users(initial_users)

    def _load_users(self):
        if not self.path.exists():
            return []

        try:
            raw = self.path.read_text(encoding="utf-8")
            return json.loads(raw) if raw else []
        except json.JSONDecodeError:
            return []

    def _save_users(self, users):
        self.path.write_text(json.dumps(users, indent=2), encoding="utf-8")

    def list_users(self):
        return self._load_users()

    def validate_user(self, username, password):
        username = username.strip().lower()
        for user in self._load_users():
            if user["username"].lower() == username and user["password"] == password:
                return True
        return False

    def add_user(self, username, password):
        username = username.strip()
        if not username or not password:
            return False, "Usuário e senha são obrigatórios."

        users = self._load_users()
        if any(u["username"].lower() == username.lower() for u in users):
            return False, "Usuário já existe."

        users.append({"username": username, "password": password, "role": "limited"})
        self._save_users(users)
        return True, "Usuário criado com sucesso."

    def remove_user(self, username):
        users = self._load_users()
        filtered = [u for u in users if u["username"].lower() != username.lower()]

        if len(filtered) == len(users):
            return False, "Usuário não encontrado."

        self._save_users(filtered)
        return True, "Usuário removido."


class LoginWindow(tk.Tk):
    def __init__(self, user_store):
        super().__init__()
        self.success = False
        self.user_role = "limited"
        self.username = ""
        self.user_store = user_store

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

        hint = "Superusuário: {}".format(config.SUPERUSER_USERNAME)
        tk.Label(container, text=hint, bg="#1e293b", fg="#64748b",
                 font=("Segoe UI", 9)).pack(pady=(0, 15))

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

        if username == config.SUPERUSER_USERNAME and password == config.SUPERUSER_PASSWORD:
            self.success = True
            self.username = username
            self.user_role = "superuser"
            self.destroy()
            return

        if self.user_store.validate_user(username, password):
            self.success = True
            self.username = username
            self.user_role = "limited"
            self.destroy()
            return

        messagebox.showerror("Acesso negado", "Usuário ou senha incorretos.")

    def _handle_close(self):
        self.success = False
        self.destroy()


class ERPApp(tk.Tk):
    def __init__(self, username, role, user_store):
        super().__init__()
        self.current_user = username
        self.user_role = role
        self.user_store = user_store
        self.selected_item_iid = None
        self.search_term = tk.StringVar()

        self.selected_sku = tk.StringVar(value="---")
        self.selected_name = tk.StringVar(value="---")
        self.selected_stock = tk.StringVar(value="---")
        self.selected_shopee_id = tk.StringVar(value="---")

        # 1. Configurações da Janela
        self.title("Sistema ERP Integrado - Shopee & Estoque Local")
        self.geometry("1100x720")
        self.configure(bg="#f0f2f5")

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
        style.theme_use('clam')

        style.configure("Treeview",
                        background="white",
                        fieldbackground="white",
                        foreground="#333",
                        rowheight=28,
                        font=('Segoe UI', 10))

        style.configure("Treeview.Heading",
                        font=('Segoe UI', 10, 'bold'),
                        background="#e1e4e8")

        style.configure("Accent.TButton",
                        background="#2563eb",
                        foreground="white",
                        font=('Segoe UI', 10, 'bold'))
        style.map("Accent.TButton", background=[("active", "#1d4ed8")])

    def create_layout(self):
        left_panel = tk.Frame(self, bg="#1e293b", width=220)
        left_panel.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(left_panel, text="ERP MASTER", bg="#1e293b", fg="white",
                 font=("Arial Black", 16)).pack(pady=(30, 10))

        tk.Label(left_panel, text="Gestão Multi-Canal", bg="#1e293b", fg="#94a3b8",
                 font=("Segoe UI", 10)).pack(pady=(0, 20))

        user_info = f"Usuário: {self.current_user}\nPerfil: {self.user_role.title()}"
        tk.Label(left_panel, text=user_info, bg="#1e293b", fg="#cbd5f5",
                 font=("Segoe UI", 10), justify=tk.LEFT).pack(padx=10, pady=(0, 20), anchor="w")

        tk.Button(left_panel, text="🔄 Recarregar Tabela",
                  bg="#334155", fg="white", bd=0,
                  font=("Segoe UI", 11), pady=10,
                  activebackground="#475569", activeforeground="white",
                  command=self.refresh_data).pack(fill=tk.X, padx=10)

        main_panel = tk.Frame(self, bg="#f0f2f5")
        main_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        header = tk.Frame(main_panel, bg="white", height=60, padx=20)
        header.pack(fill=tk.X)
        tk.Label(header, text="Controle de Estoque Unificado",
                 font=("Segoe UI", 16, "bold"), bg="white", fg="#1e293b").pack(side=tk.LEFT, pady=15)

        content = tk.Frame(main_panel, padx=20, pady=20, bg="#f0f2f5")
        content.pack(fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(content)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.search_tab = tk.Frame(self.notebook, bg="#f0f2f5")
        self.update_tab = tk.Frame(self.notebook, bg="#f0f2f5")
        self.notebook.add(self.search_tab, text="Pesquisa")
        self.notebook.add(self.update_tab, text="Atualização")

        if self.user_role == "superuser":
            self.admin_tab = tk.Frame(self.notebook, bg="#f0f2f5")
            self.notebook.add(self.admin_tab, text="Acessos")
        else:
            self.admin_tab = None

        self.build_search_tab()
        self.build_update_tab()
        if self.admin_tab:
            self.build_admin_tab()

        log_frame = tk.LabelFrame(content, text="Logs do Sistema", bg="#f0f2f5",
                                  font=("Segoe UI", 10, "bold"))
        log_frame.pack(fill=tk.X, pady=(15, 0))
        self.log_widget = scrolledtext.ScrolledText(log_frame, height=6, state='disabled',
                                                    bg="#1e293b", fg="#00ff00", font=("Consolas", 9))
        self.log_widget.pack(fill=tk.X)

    def build_search_tab(self):
        control_frame = tk.Frame(self.search_tab, bg="#f0f2f5")
        control_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(control_frame, text="Buscar por SKU ou Nome:").pack(side=tk.LEFT)
        search_entry = ttk.Entry(control_frame, textvariable=self.search_term, width=35)
        search_entry.pack(side=tk.LEFT, padx=10)
        search_entry.bind("<Return>", lambda _: self.search_products())

        ttk.Button(control_frame, text="Buscar", command=self.search_products).pack(side=tk.LEFT)
        ttk.Button(control_frame, text="Limpar", command=self.clear_search).pack(side=tk.LEFT, padx=(10, 0))

        self.result_var = tk.StringVar(value="0 produtos")
        tk.Label(control_frame, textvariable=self.result_var, bg="#f0f2f5", fg="#475569",
                 font=("Segoe UI", 10)).pack(side=tk.RIGHT)

        tree_frame = tk.Frame(self.search_tab)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(tree_frame, columns=TREE_COLUMNS, show="headings", height=12)
        self.tree.heading("sku", text="SKU (Código)")
        self.tree.heading("nome", text="Produto")
        self.tree.heading("estoque", text="Qtd. Local")
        self.tree.heading("shopee_id", text="ID Shopee")
        self.tree.heading("status", text="Status Sync")

        self.tree.column("sku", width=140)
        self.tree.column("nome", width=320)
        self.tree.column("estoque", width=90, anchor="center")
        self.tree.column("shopee_id", width=140, anchor="center")
        self.tree.column("status", width=150, anchor="center")

        scroller = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroller.set)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroller.pack(side=tk.RIGHT, fill=tk.Y)

    def build_update_tab(self):
        info_box = tk.LabelFrame(self.update_tab, text="Produto Selecionado", bg="#f0f2f5",
                                 font=("Segoe UI", 10, "bold"))
        info_box.pack(fill=tk.X, pady=(0, 15))

        self._add_info_row(info_box, "SKU:", self.selected_sku)
        self._add_info_row(info_box, "Nome:", self.selected_name)
        self._add_info_row(info_box, "Estoque Atual:", self.selected_stock)
        self._add_info_row(info_box, "Shopee ID:", self.selected_shopee_id)

        form_frame = tk.Frame(self.update_tab, bg="white", padx=20, pady=20)
        form_frame.pack(fill=tk.X)

        tk.Label(form_frame, text="Novo Estoque", bg="white", font=("Segoe UI", 12)).pack(anchor="w")
        self.new_stock_entry = ttk.Entry(form_frame, width=15, font=("Segoe UI", 12))
        self.new_stock_entry.pack(anchor="w", pady=(5, 15))

        self.btn_update = ttk.Button(form_frame, text="ATUALIZAR & SINCRONIZAR",
                                     style="Accent.TButton",
                                     command=self.start_update_thread)
        self.btn_update.pack(anchor="w")

    def _add_info_row(self, parent, label_text, var):
        row = tk.Frame(parent, bg="#f0f2f5")
        row.pack(fill=tk.X, pady=2)
        tk.Label(row, text=label_text, width=15, anchor="w", bg="#f0f2f5",
                 font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        tk.Label(row, textvariable=var, bg="#f0f2f5", font=("Segoe UI", 10)).pack(side=tk.LEFT)

    def build_admin_tab(self):
        wrapper = tk.Frame(self.admin_tab, bg="#f0f2f5", padx=10, pady=10)
        wrapper.pack(fill=tk.BOTH, expand=True)

        ttk.Label(wrapper, text="Usuários com acesso limitado", font=("Segoe UI", 11, "bold"))\
            .pack(anchor="w", pady=(0, 10))

        table_frame = tk.Frame(wrapper)
        table_frame.pack(fill=tk.BOTH, expand=True)

        self.user_tree = ttk.Treeview(table_frame, columns=("username", "role"), show="headings", height=6)
        self.user_tree.heading("username", text="Usuário")
        self.user_tree.heading("role", text="Perfil")
        self.user_tree.column("username", width=200)
        self.user_tree.column("role", width=100)
        self.user_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        user_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.user_tree.yview)
        self.user_tree.configure(yscrollcommand=user_scroll.set)
        user_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        form = tk.LabelFrame(wrapper, text="Novo Usuário", bg="#f0f2f5")
        form.pack(fill=tk.X, pady=15)

        self.new_user_var = tk.StringVar()
        self.new_pass_var = tk.StringVar()
        self.user_feedback_var = tk.StringVar()

        ttk.Label(form, text="Usuário:").pack(anchor="w")
        ttk.Entry(form, textvariable=self.new_user_var).pack(fill=tk.X, pady=(0, 10))
        ttk.Label(form, text="Senha:").pack(anchor="w")
        ttk.Entry(form, textvariable=self.new_pass_var, show="*").pack(fill=tk.X, pady=(0, 10))

        ttk.Button(form, text="Adicionar", command=self.add_limited_user).pack(side=tk.LEFT)
        ttk.Button(form, text="Remover selecionado", command=self.remove_selected_user).pack(side=tk.LEFT, padx=(10, 0))

        tk.Label(wrapper, textvariable=self.user_feedback_var, bg="#f0f2f5", fg="#475569",
                 font=("Segoe UI", 10)).pack(fill=tk.X, pady=(10, 0))

        self.load_users_table()

    # ---------------------------- FUNCIONALIDADES ---------------------------- #
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_widget.config(state='normal')
        self.log_widget.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_widget.see(tk.END)
        self.log_widget.config(state='disabled')

    def populate_tree(self, produtos):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for p in produtos:
            shopee_id = p['shopee_id'] if p['shopee_id'] else "---"
            self.tree.insert("", "end", values=(
                p['sku'],
                p['nome'],
                p['estoque_real'],
                shopee_id,
                "Aguardando"
            ))

        self.result_var.set(f"{len(produtos)} produtos")
        self.clear_selection()

    def refresh_data(self):
        self.log("Buscando dados atualizados do banco...")
        produtos = database.get_all_products()
        self.populate_tree(produtos)
        self.log(f"Tabela atualizada. {len(produtos)} produtos carregados.")

    def search_products(self):
        term = self.search_term.get().strip()
        if not term:
            self.refresh_data()
            return

        self.log(f"Buscando por '{term}'...")
        produtos = database.search_products(term)
        self.populate_tree(produtos)
        self.log(f"{len(produtos)} produtos encontrados para '{term}'.")

    def clear_search(self):
        self.search_term.set("")
        self.refresh_data()

    def on_tree_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            self.clear_selection()
            return

        iid = selected[0]
        values = self.tree.item(iid)['values']
        if not values:
            return

        self.selected_item_iid = iid
        self.selected_sku.set(values[0])
        self.selected_name.set(values[1])
        self.selected_stock.set(values[2])
        self.selected_shopee_id.set(values[3])

    def clear_selection(self):
        self.selected_item_iid = None
        self.selected_sku.set("---")
        self.selected_name.set("---")
        self.selected_stock.set("---")
        self.selected_shopee_id.set("---")
        self.new_stock_entry.delete(0, tk.END)

    def start_update_thread(self):
        if not self.selected_item_iid:
            messagebox.showwarning("Seleção necessária", "Selecione um produto na aba de pesquisa.")
            return

        qty_str = self.new_stock_entry.get().strip()
        if not qty_str.isdigit():
            messagebox.showerror("Erro", "Digite um número inteiro válido para o estoque.")
            return

        self.btn_update.config(state="disabled")
        threading.Thread(target=self.process_update,
                         args=(self.selected_item_iid, int(qty_str)),
                         daemon=True).start()

    def process_update(self, item_iid, new_qty):
        try:
            if not self.tree.exists(item_iid):
                self.log("❌ Item selecionado não existe mais na lista.")
                return

            current_values = self.tree.item(item_iid)['values']
            if not current_values:
                self.log("❌ Não foi possível recuperar os dados do item selecionado.")
                return

            sku = current_values[0]
            shopee_id = str(current_values[3])

            self.log(f"--- INICIANDO PROCESSO PARA {sku} ---")
            self.log(f"Atualizando banco local para {new_qty} un...")

            if database.update_stock(sku, new_qty):
                self.after(0, lambda: self.tree.set(item_iid, "estoque", new_qty))
                self.after(0, lambda: self.selected_stock.set(str(new_qty)))
            else:
                self.log("❌ Erro ao atualizar banco local. Abortando.")
                return

            if shopee_id not in ("---", "None"):
                self.log(f"Conectando à API Shopee (Item ID: {shopee_id})...")
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

        except Exception as exc:
            self.log(f"❌ ERRO CRÍTICO NA THREAD: {exc}")

        finally:
            self.after(0, lambda: self.btn_update.config(state="normal"))
            self.after(0, lambda: self.new_stock_entry.delete(0, tk.END))
            self.log("--- PROCESSO FINALIZADO ---")

    # ---------------------------- ADMIN TAB ---------------------------- #
    def load_users_table(self):
        if not self.admin_tab:
            return
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)

        for user in self.user_store.list_users():
            self.user_tree.insert("", "end", values=(user["username"], user.get("role", "limited")))

    def add_limited_user(self):
        username = self.new_user_var.get().strip()
        password = self.new_pass_var.get().strip()
        ok, msg = self.user_store.add_user(username, password)
        self.user_feedback_var.set(msg)
        if ok:
            self.new_user_var.set("")
            self.new_pass_var.set("")
            self.load_users_table()

    def remove_selected_user(self):
        selection = self.user_tree.selection()
        if not selection:
            self.user_feedback_var.set("Selecione um usuário para remover.")
            return

        username = self.user_tree.item(selection[0])["values"][0]
        ok, msg = self.user_store.remove_user(username)
        self.user_feedback_var.set(msg)
        if ok:
            self.load_users_table()


if __name__ == "__main__":
    user_store = UserStore(
        default_username=config.DEFAULT_LIMITED_USERNAME,
        default_password=config.DEFAULT_LIMITED_PASSWORD
    )

    login_window = LoginWindow(user_store)
    login_window.mainloop()

    if getattr(login_window, "success", False):
        app = ERPApp(
            username=login_window.username,
            role=login_window.user_role,
            user_store=user_store
        )
        app.mainloop()
    else:
        print("Execução encerrada: login não realizado.")