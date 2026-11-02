import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from rutas_almacen.almacen import crear_nodos, crear_grafo, INVENTARIO
from rutas_almacen.busqueda import a_estrella, ruta_orden_pedido
from rutas_almacen.graficas import grafica_costos, grafica_nodos

PESOS = (1, 1.5, 2)

def fila_resultado(pedido, metodo, r, cota=None):
    return {
        "Pedido": pedido,
        "Método": metodo,
        "Orden": " → ".join(r["orden"]),
        "Costo": round(r["costo"], 2),
        "Distancia": round(r["distancia"], 2),
        "Zona": r["zona"],
        "Nivel": r["nivel"],
        "Nodos revisados": r["revisados"],
        "Tiempo (ms)": round(r["tiempo"] * 1000, 3),
        "Cumple cota": cota,
    }

class InterfazAlmacen:
    def __init__(self, root, nodos, grafo):
        self.root = root
        self.root.title("Gestión de Rutas - Análisis A*")
        self.root.geometry("900x750")
        self.root.configure(bg="#f4f5f7") # Fondo gris muy claro

        self.nodos = nodos
        self.grafo = grafo
        self.lista_nodos = list(self.nodos.keys())
        self.lista_piezas = list(INVENTARIO.keys())
        self.entradas_pedidos = []

        self.configurar_estilos()

        # --- TÍTULO PRINCIPAL ---
        titulo = tk.Label(root, text="Optimización de Rutas de Almacén",
                          font=("Segoe UI", 18, "bold"), bg="#f4f5f7", fg="#2c3e50")
        titulo.pack(pady=(15, 5))

        #PANEL SUPERIOR: Configuración
        frame_top = ttk.LabelFrame(root, text=" Parámetros de los Pedidos ", padding=15)
        frame_top.pack(padx=20, pady=10, fill="x")

        frame_controles = ttk.Frame(frame_top)
        frame_controles.pack(fill="x", pady=(0, 10))

        ttk.Label(frame_controles, text="Cantidad de pedidos (2-4):", font=("Segoe UI", 10, "bold")).pack(side="left", padx=5)
        self.spin_pedidos = ttk.Spinbox(frame_controles, from_=2, to=4, width=5, command=self.generar_filas, state="readonly")
        self.spin_pedidos.set(2)
        self.spin_pedidos.pack(side="left", padx=5)

        self.frame_pedidos = ttk.Frame(frame_top)
        self.frame_pedidos.pack(fill="x", pady=5)

        self.btn_ejecutar = ttk.Button(root, text="▶ Ejecutar Análisis", style="Accent.TButton", command=self.ejecutar)
        self.btn_ejecutar.pack(pady=10)

        # PANEL INFERIOR: Pestañas
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(padx=20, pady=(0, 20), fill="both", expand=True)

        self.tab_tabla = ttk.Frame(self.notebook)
        self.tab_costos = ttk.Frame(self.notebook)
        self.tab_nodos = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_tabla, text=" Tabla de Resultados ")
        self.notebook.add(self.tab_costos, text=" Gráfica de Costos ")
        self.notebook.add(self.tab_nodos, text=" Gráfica de Nodos ")

        # Configurar Tabla
        self.tree = ttk.Treeview(self.tab_tabla, columns=("Pedido", "Método", "Orden", "Costo", "Nodos", "Tiempo"), show="headings")
        for col, ancho in {"Pedido": 70, "Método": 140, "Orden": 140, "Costo": 90, "Nodos": 100, "Tiempo": 100}.items():
            self.tree.heading(col, text=col)
            self.tree.column(col, width=ancho, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        self.canvas_costos = None
        self.canvas_nodos = None

        self.generar_filas()

    def configurar_estilos(self):
        """Aplica un tema moderno y configura colores/fuentes."""
        style = ttk.Style()
        # Usar el tema 'clam' que es más limpio y personalizable en todos los OS
        if "clam" in style.theme_names():
            style.theme_use("clam")

        fuente_base = ("Segoe UI", 10)

        style.configure(".", font=fuente_base, background="#f4f5f7")
        style.configure("TLabelframe", background="#ffffff", bordercolor="#d1d5db")
        style.configure("TLabelframe.Label", font=("Segoe UI", 11, "bold"), foreground="#2c3e50", background="#f4f5f7")
        style.configure("TFrame", background="#ffffff")
        style.configure("TLabel", background="#ffffff", foreground="#333333")

        # Estilo del botón principal
        style.configure("Accent.TButton", font=("Segoe UI", 11, "bold"), foreground="white", background="#0078D7", padding=8)
        style.map("Accent.TButton", background=[("active", "#005a9e")])

        # Estilo de las pestañas
        style.configure("TNotebook", background="#f4f5f7", borderwidth=0)
        style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[10, 5], background="#e1dfdd", foreground="#333333")
        style.map("TNotebook.Tab", background=[("selected", "#ffffff")], foreground=[("selected", "#0078D7")])

        # Estilo de la tabla (Treeview)
        style.configure("Treeview", font=fuente_base, rowheight=28, background="#ffffff", fieldbackground="#ffffff")
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#f3f2f1", foreground="#2c3e50")
        style.map("Treeview", background=[("selected", "#cce8ff")], foreground=[("selected", "#000000")])

    def generar_filas(self):
        for widget in self.frame_pedidos.winfo_children():
            widget.destroy()
        self.entradas_pedidos.clear()

        num_pedidos = int(self.spin_pedidos.get())

        # Encabezados de los selects
        encabezados = ["ID Pedido", "Nodo de Inicio", "Primera Pieza", "Segunda Pieza"]
        for col, texto in enumerate(encabezados):
            ttk.Label(self.frame_pedidos, text=texto, font=("Segoe UI", 9, "bold"), foreground="#555555").grid(row=0, column=col, pady=(0,5), padx=10)

        for i in range(num_pedidos):
            id_pedido = f"P{i+1}"
            ttk.Label(self.frame_pedidos, text=id_pedido, font=("Segoe UI", 10, "bold"), foreground="#0078D7").grid(row=i+1, column=0, padx=10, pady=5)

            cb_inicio = ttk.Combobox(self.frame_pedidos, values=self.lista_nodos, width=12, state="readonly", font=("Segoe UI", 10))
            cb_inicio.set("ENT")
            cb_inicio.grid(row=i+1, column=1, padx=10, pady=5)

            cb_p1 = ttk.Combobox(self.frame_pedidos, values=self.lista_piezas, width=15, state="readonly", font=("Segoe UI", 10))
            cb_p1.set(self.lista_piezas[i * 2 % len(self.lista_piezas)])
            cb_p1.grid(row=i+1, column=2, padx=10, pady=5)

            cb_p2 = ttk.Combobox(self.frame_pedidos, values=self.lista_piezas, width=15, state="readonly", font=("Segoe UI", 10))
            cb_p2.set(self.lista_piezas[(i * 2 + 1) % len(self.lista_piezas)])
            cb_p2.grid(row=i+1, column=3, padx=10, pady=5)

            self.entradas_pedidos.append((id_pedido, cb_inicio, cb_p1, cb_p2))

    def ejecutar(self):
        pedidos_ingresados = []
        for id_ped, cb_ini, cb_p1, cb_p2 in self.entradas_pedidos:
            ini, p1, p2 = cb_ini.get(), cb_p1.get(), cb_p2.get()
            if p1 == p2:
                messagebox.showwarning("Piezas duplicadas", f"En el {id_ped}, las piezas deben ser distintas para calcular una ruta válida.")
                return
            pedidos_ingresados.append((id_ped, ini, [p1, p2]))

        for row in self.tree.get_children():
            self.tree.delete(row)

        filas = []
        for pedido, inicio, codigos in pedidos_ingresados:
            base = ruta_orden_pedido(inicio, codigos, self.nodos, self.grafo, INVENTARIO)
            filas.append(fila_resultado(pedido, "Orden del pedido", base))
            r_optimo = a_estrella(inicio, codigos, self.nodos, self.grafo, INVENTARIO, w=1.0)

            for w in PESOS:
                r = r_optimo if w == 1 else a_estrella(inicio, codigos, self.nodos, self.grafo, INVENTARIO, w=w)
                filas.append(fila_resultado(pedido, f"A* w={w}", r, r["costo"] <= w * r_optimo["costo"] + 1e-9))

        df = pd.DataFrame(filas)

        for i, (index, row) in enumerate(df.iterrows()):
            tag = "par" if i % 2 == 0 else "impar"
            self.tree.insert("", "end", values=(row["Pedido"], row["Método"], row["Orden"], row["Costo"], row["Nodos revisados"], row["Tiempo (ms)"]), tags=(tag,))

        self.tree.tag_configure("par", background="#f9f9f9")
        self.tree.tag_configure("impar", background="#ffffff")

        self.actualizar_graficas(df)
        self.notebook.select(self.tab_tabla)

    def actualizar_graficas(self, df):
        if self.canvas_costos:
            self.canvas_costos.get_tk_widget().destroy()
        if self.canvas_nodos:
            self.canvas_nodos.get_tk_widget().destroy()

        fig_costos = grafica_costos(df)
        self.canvas_costos = FigureCanvasTkAgg(fig_costos, master=self.tab_costos)
        self.canvas_costos.draw()
        self.canvas_costos.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

        fig_nodos = grafica_nodos(df)
        self.canvas_nodos = FigureCanvasTkAgg(fig_nodos, master=self.tab_nodos)
        self.canvas_nodos.draw()
        self.canvas_nodos.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

if __name__ == "__main__":
    nodos = crear_nodos()
    grafo = crear_grafo(nodos)
    root = tk.Tk()
    app = InterfazAlmacen(root, nodos, grafo)
    root.mainloop()
