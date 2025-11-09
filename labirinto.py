import tkinter as tk
from tkinter import ttk
from collections import deque

# --- Constantes de Configuração ---
LARGURA_CELULA = 20
ALTURA_CELULA = 20
COLUNAS = 0
LINHAS = 0
TEMPO_MS = 50 

CORES = {
    '#': "#1E3A5F",  
    ' ': "#FFFFFF",  
    'S': "#4CAF50",  
    'E': "#F44336",  
    'Fronteira': "#AED6F1",  
    'Visitado': "#D6EAF8",   
    'Caminho Final': "#FFD700",
}

class MazeEditorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Solucionador de Labirintos Interativo (BFS)")

        # Variáveis de Estado
        self.labirinto = [[' ' for _ in range(COLUNAS)] for _ in range(LINHAS)]
        self.grid_cells = [[None for _ in range(COLUNAS)] for _ in range(LINHAS)]
        self.inicio_pos = None
        self.fim_pos = None
        self.tool_var = tk.StringVar(value='#') 
        self.job_after = None 
        self.simulacao_ativa = False

        
        self.fila = deque()
        self.visitados = set()
        self.predecessores = {} 

        # Configuração da Interface
        self.setup_ui()
        self.limpar_labirinto()

    def setup_ui(self):
        
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        
        canvas_width = COLUNAS * LARGURA_CELULA
        canvas_height = LINHAS * ALTURA_CELULA
        self.canvas = tk.Canvas(main_frame, width=canvas_width, height=canvas_height, bg=CORES[' '], borderwidth=0, highlightthickness=0)
        self.canvas.grid(row=0, column=0, columnspan=2, pady=10)

        
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_click)

        
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=1, column=0, sticky=tk.NW, padx=10)

        
        tool_frame = ttk.LabelFrame(control_frame, text="Ferramenta de Edição", padding="5")
        tool_frame.pack(pady=5, fill=tk.X)

        ferramentas = [
            ("Parede (#)", '#'),
            ("Caminho ( )", ' '),
            ("Início (S)", 'S'),
            ("Fim (E)", 'E')
        ]

        for texto, valor in ferramentas:
            rb = ttk.Radiobutton(tool_frame, text=texto, variable=self.tool_var, value=valor)
            rb.pack(anchor=tk.W)

        
        action_frame = ttk.LabelFrame(control_frame, text="Ações", padding="5")
        action_frame.pack(pady=10, fill=tk.X)

        self.btn_iniciar = ttk.Button(action_frame, text="Iniciar Busca (BFS)", command=self.iniciar_busca)
        self.btn_iniciar.pack(fill=tk.X, pady=2)

        self.btn_resetar = ttk.Button(action_frame, text="Resetar Busca", command=self.resetar_busca, state=tk.DISABLED)
        self.btn_resetar.pack(fill=tk.X, pady=2)

        self.btn_limpar = ttk.Button(action_frame, text="Limpar Labirinto", command=self.limpar_labirinto)
        self.btn_limpar.pack(fill=tk.X, pady=2)

        
        self.status_var = tk.StringVar(value="Modo Edição: Pronto")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, anchor=tk.W)
        self.status_label.grid(row=2, column=0, columnspan=2, sticky=tk.W+tk.E, pady=5)

    # --- Lógica da Grade e Edição ---

    def desenhar_grid_inicial(self):
        """Desenha a grade de células no Canvas e armazena seus IDs."""
        for r in range(LINHAS):
            for c in range(COLUNAS):
                x1 = c * LARGURA_CELULA
                y1 = r * ALTURA_CELULA
                x2 = x1 + LARGURA_CELULA
                y2 = y1 + ALTURA_CELULA
                rect_id = self.canvas.create_rectangle(x1, y1, x2, y2, fill=CORES[' '], outline="#ccc")
                self.grid_cells[r][c] = rect_id
                self.labirinto[r][c] = ' '

    def get_cell_coords(self, event):
        """Converte coordenadas de pixel do mouse para coordenadas de célula (linha, coluna)."""
        c = event.x // LARGURA_CELULA
        r = event.y // ALTURA_CELULA
        if 0 <= r < LINHAS and 0 <= c < COLUNAS:
            return r, c
        return None, None

    def on_canvas_click(self, event):
        """Manipula cliques e arrastos no Canvas para edição."""
        if self.simulacao_ativa:
            return 

        r, c = self.get_cell_coords(event)
        if r is not None and c is not None:
            ferramenta = self.tool_var.get()
            self.editar_celula(r, c, ferramenta)

    def editar_celula(self, r, c, novo_valor):
        """Atualiza o modelo de dados e a representação visual de uma célula."""
        valor_antigo = self.labirinto[r][c]

        if novo_valor == valor_antigo:
            return 

        
        if novo_valor == 'S':
            if self.inicio_pos:
                
                self.labirinto[self.inicio_pos[0]][self.inicio_pos[1]] = ' '
                self.canvas.itemconfig(self.grid_cells[self.inicio_pos[0]][self.inicio_pos[1]], fill=CORES[' '])
            self.inicio_pos = (r, c)
        elif novo_valor == 'E':
            if self.fim_pos:
                
                self.labirinto[self.fim_pos[0]][self.fim_pos[1]] = ' '
                self.canvas.itemconfig(self.grid_cells[self.fim_pos[0]][self.fim_pos[1]], fill=CORES[' '])
            self.fim_pos = (r, c)
        
        
        if valor_antigo == 'S' and novo_valor != 'S':
            self.inicio_pos = None
        elif valor_antigo == 'E' and novo_valor != 'E':
            self.fim_pos = None

        
        self.labirinto[r][c] = novo_valor
        cor = CORES.get(novo_valor, CORES[' '])
        self.canvas.itemconfig(self.grid_cells[r][c], fill=cor)

  

    def limpar_labirinto(self):
        """Limpa toda a grade para o estado inicial de 'Caminho'."""
        self.cancelar_animacao()
        self.simulacao_ativa = False
        self.inicio_pos = None
        self.fim_pos = None
        self.desenhar_grid_inicial() 
        self.status_var.set("Modo Edição: Labirinto limpo.")
        self.habilitar_edicao()
        self.resetar_variaveis_bfs()

    def resetar_busca(self):
        """Limpa apenas os resultados da busca (cores de BFS), mantendo o labirinto."""
        self.cancelar_animacao()
        self.simulacao_ativa = False
        self.resetar_variaveis_bfs()
        
       
        for r in range(LINHAS):
            for c in range(COLUNAS):
                valor = self.labirinto[r][c]
                if valor not in ['#', 'S', 'E']:
                  
                    self.canvas.itemconfig(self.grid_cells[r][c], fill=CORES[' '])
                else:
                  
                    self.canvas.itemconfig(self.grid_cells[r][c], fill=CORES[valor])

        self.status_var.set("Modo Edição: Busca resetada.")
        self.habilitar_edicao()

    def habilitar_edicao(self):
        """Habilita os controles de edição e o botão Iniciar."""
        for child in self.root.winfo_children():
            if isinstance(child, ttk.Frame):
                for sub_child in child.winfo_children():
                    if isinstance(sub_child, ttk.LabelFrame):
                        for widget in sub_child.winfo_children():
                            if isinstance(widget, ttk.Radiobutton):
                                widget.config(state=tk.NORMAL)
        self.btn_iniciar.config(state=tk.NORMAL)
        self.btn_resetar.config(state=tk.DISABLED)

    def desabilitar_edicao(self):
        """Desabilita os controles de edição."""
        for child in self.root.winfo_children():
            if isinstance(child, ttk.Frame):
                for sub_child in child.winfo_children():
                    if isinstance(sub_child, ttk.LabelFrame):
                        for widget in sub_child.winfo_children():
                            if isinstance(widget, ttk.Radiobutton):
                                widget.config(state=tk.DISABLED)
        self.btn_iniciar.config(state=tk.DISABLED)
        self.btn_resetar.config(state=tk.NORMAL)


    def resetar_variaveis_bfs(self):
        """Reinicializa as variáveis internas do BFS."""
        self.fila = deque()
        self.visitados = set()
        self.predecessores = {}

    def iniciar_busca(self):
        """Prepara e inicia a animação do BFS."""
        if not self.inicio_pos or not self.fim_pos:
            self.status_var.set("Erro: Defina os pontos de Início (S) e Fim (E)!")
            return

        self.resetar_busca() 
        self.desabilitar_edicao()
        self.simulacao_ativa = True
        self.status_var.set("Modo Simulação: Iniciando Busca em Largura (BFS)...")

     
        r_s, c_s = self.inicio_pos
        self.fila.append((r_s, c_s))
        self.visitados.add((r_s, c_s))
        self.processar_passo_bfs()

    def processar_passo_bfs(self):
        """Executa um único passo do algoritmo BFS e agenda o próximo."""
        if not self.fila:
            self.status_var.set("Busca Finalizada: Caminho não encontrado.")
            self.simulacao_ativa = False
            self.habilitar_edicao()
            return

        r, c = self.fila.popleft()


        if (r, c) != self.inicio_pos:
            self.canvas.itemconfig(self.grid_cells[r][c], fill=CORES['Visitado'])

        if (r, c) == self.fim_pos:
            self.status_var.set("Busca Finalizada: Caminho encontrado!")
            self.simulacao_ativa = False
            self.reconstruir_caminho()
            self.habilitar_edicao()
            return

        # Encontra vizinhos
        movimentos = [(0, 1), (0, -1), (1, 0), (-1, 0)] 
        
        for dr, dc in movimentos:
            nr, nc = r + dr, c + dc
            vizinho = (nr, nc)

            
            if (0 <= nr < LINHAS and 
                0 <= nc < COLUNAS and 
                self.labirinto[nr][nc] != '#' and 
                vizinho not in self.visitados):
                
                self.visitados.add(vizinho)
                self.predecessores[vizinho] = (r, c)
                self.fila.append(vizinho)

                
                if vizinho != self.fim_pos:
                    self.canvas.itemconfig(self.grid_cells[nr][nc], fill=CORES['Fronteira'])
                
        
        if self.simulacao_ativa:
            self.job_after = self.root.after(TEMPO_MS, self.processar_passo_bfs)

    def cancelar_animacao(self):
        """Cancela a execução agendada do root.after()."""
        if self.job_after:
            self.root.after_cancel(self.job_after)
            self.job_after = None

    def reconstruir_caminho(self):
        """Traça e pinta o caminho mais curto de E até S usando o dicionário de predecessores."""
        caminho = []
        atual = self.fim_pos
        
        
        while atual and atual != self.inicio_pos:
            caminho.append(atual)
            atual = self.predecessores.get(atual)
        
        for r, c in caminho:
            if (r, c) != self.fim_pos:
                self.canvas.itemconfig(self.grid_cells[r][c], fill=CORES['Caminho Final'])

if __name__ == "__main__":
    print("\n----------------------------------------------------configuar o labirinto:----------------------------------------------------\n")
    print("digite o tamanho das colunas:")
    COLUNAS = int(input())
    print("digite o tamanho das linhas:")
    LINHAS = int(input())
    if(COLUNAS == 1 and LINHAS == 1):
        print("o labirinto deve ter no minimo 2 colunas ou 2 linhas")
        exit()

    print("contruindo labirinto...")    
    root = tk.Tk()
    app = MazeEditorGUI(root)
    root.mainloop()
    print("simulaçao finalizada\n")
