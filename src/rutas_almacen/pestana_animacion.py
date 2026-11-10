"""Pestaña "Animación" de la interfaz tkinter.

Se agrega al notebook de main.py y reutiliza el pedido y el peso w que el
usuario elija entre los pedidos de la última ejecución del análisis.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from rutas_almacen.busqueda import a_estrella
from rutas_almacen.animacion import animar_busqueda, animar_ruta, exportar

MODO_BUSQUEDA = "Exploración de A*"
MODO_RUTA = "Ruta final"
PESOS = ("1", "1.5", "2")


class PestanaAnimacion(ttk.Frame):
    def __init__(self, parent, nodos, grafo, inventario):
        super().__init__(parent)
        self.nodos = nodos
        self.grafo = grafo
        self.inventario = inventario
        self.pedidos = {}      # id_pedido -> (inicio, [codigos]) de la última ejecución
        self.anim = None
        self._clave_anim = None
        self.velocidad = 1.0

        # ---- barra de controles (arriba) ----
        barra = ttk.Frame(self)
        barra.pack(fill="x", padx=10, pady=(10, 4))

        ttk.Label(barra, text="Pedido:").pack(side="left", padx=(0, 4))
        self.cb_pedido = ttk.Combobox(barra, values=[], width=6, state="readonly")
        self.cb_pedido.pack(side="left", padx=(0, 10))

        ttk.Label(barra, text="Animar:").pack(side="left", padx=(0, 4))
        self.cb_modo = ttk.Combobox(barra, values=[MODO_BUSQUEDA, MODO_RUTA], width=18, state="readonly")
        self.cb_modo.set(MODO_BUSQUEDA)
        self.cb_modo.pack(side="left", padx=(0, 10))

        ttk.Label(barra, text="Peso w:").pack(side="left", padx=(0, 4))
        self.cb_w = ttk.Combobox(barra, values=PESOS, width=5, state="readonly")
        self.cb_w.set("1")
        self.cb_w.pack(side="left")

        # ---- botones de reproducción ----
        botones = ttk.Frame(self)
        botones.pack(fill="x", padx=10, pady=(0, 4))
        ttk.Button(botones, text="▶ Reproducir", command=self.reproducir).pack(side="left", padx=(0, 6))
        ttk.Button(botones, text="⏸ Pausar", command=self.pausar).pack(side="left", padx=(0, 6))
        ttk.Button(botones, text="↺ Reiniciar", command=self.reiniciar).pack(side="left", padx=(0, 14))

        ttk.Label(botones, text="Velocidad:").pack(side="left", padx=(0, 4))
        self.escala = ttk.Scale(botones, from_=0.25, to=4.0, value=1.0, length=140, command=self._cambiar_velocidad)
        self.escala.pack(side="left")
        self.lbl_vel = ttk.Label(botones, text="1.0x", width=6)
        self.lbl_vel.pack(side="left", padx=(4, 14))

        ttk.Button(botones, text="Exportar video…", command=self.exportar_video).pack(side="right")

        # ---- lienzo ----
        self.fig = Figure(figsize=(9, 6.4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.lbl_aviso = ttk.Label(self, text="Ejecuta el análisis para habilitar la animación.",
                                   foreground="#666666")
        self.lbl_aviso.pack(pady=(0, 8))

    # ------------------------------------------------------------------ datos
    def actualizar_pedidos(self, pedidos):
        """Recibe los pedidos de la última ejecución: [(id, inicio, [codigos]), ...]."""
        self._detener()
        self.pedidos = {pid: (ini, list(cods)) for pid, ini, cods in pedidos}
        ids = list(self.pedidos)
        self.cb_pedido["values"] = ids
        if ids and self.cb_pedido.get() not in ids:
            self.cb_pedido.set(ids[0])
        self.lbl_aviso.config(text=f"Listo: elige pedido, modo y peso, y pulsa Reproducir ({len(ids)} pedidos disponibles).")
        self.fig.clf()
        self.canvas.draw_idle()
        self.anim = None

    def _seleccion(self):
        """Devuelve (inicio, codigos, w) o None si no hay análisis previo."""
        if not self.pedidos or not self.cb_pedido.get():
            messagebox.showwarning("Sin análisis",
                                   "Primero pulsa «Ejecutar Análisis» para tener pedidos que animar.")
            return None
        inicio, codigos = self.pedidos[self.cb_pedido.get()]
        return inicio, codigos, float(self.cb_w.get())

    def _clave_seleccion(self):
        return (self.cb_pedido.get(), self.cb_modo.get(), self.cb_w.get())

    def _crear_animacion(self, fig):
        """Corre A* con traza para la selección actual y construye la animación."""
        sel = self._seleccion()
        if sel is None:
            return None
        inicio, codigos, w = sel
        traza = []
        resultado = a_estrella(inicio, codigos, self.nodos, self.grafo, self.inventario, w=w, traza=traza)
        if self.cb_modo.get() == MODO_RUTA:
            return animar_ruta(self.nodos, self.grafo, resultado, inicio, self.inventario, codigos, fig=fig)
        return animar_busqueda(self.nodos, self.grafo, traza, self.inventario, codigos, inicio,
                               resultado=resultado, fig=fig)

    # ----------------------------------------------------------- reproducción
    def _detener(self):
        if self.anim is not None and self.anim.event_source is not None:
            self.anim.event_source.stop()

    def reproducir(self):
        # Si hay una animación a medias con la misma selección, solo se reanuda;
        # si terminó, no existe o cambió el pedido/modo/peso, se crea de nuevo.
        if (self.anim is not None and self.anim.event_source is not None
                and self._clave_seleccion() == self._clave_anim):
            try:
                self.anim.resume()
                return
            except Exception:
                pass
        self.reiniciar()

    def pausar(self):
        if self.anim is not None and self.anim.event_source is not None:
            self.anim.pause()

    def reiniciar(self):
        self._detener()
        self.anim = self._crear_animacion(self.fig)
        if self.anim is None:
            return
        self._clave_anim = self._clave_seleccion()
        self._aplicar_velocidad()
        self.canvas.draw()

    def _cambiar_velocidad(self, valor):
        self.velocidad = float(valor)
        self.lbl_vel.config(text=f"{self.velocidad:.2f}x")
        self._aplicar_velocidad()

    def _aplicar_velocidad(self):
        if self.anim is not None and self.anim.event_source is not None:
            self.anim.event_source.interval = max(15, int(self.anim.intervalo_ms / self.velocidad))

    # ----------------------------------------------------------------- export
    def exportar_video(self):
        if self._seleccion() is None:
            return
        archivo = filedialog.asksaveasfilename(
            title="Exportar animación", defaultextension=".mp4",
            initialfile=f"{self.cb_pedido.get()}_{'ruta' if self.cb_modo.get() == MODO_RUTA else 'busqueda'}.mp4",
            filetypes=[("Video MP4", "*.mp4"), ("GIF animado", "*.gif")])
        if not archivo:
            return
        # Se usa una figura aparte para no interrumpir la reproducción en pantalla.
        fig_export = Figure(figsize=(9, 6.4), dpi=110)
        self.lbl_aviso.config(text="Exportando video, espera un momento…")
        self.config(cursor="watch")
        self.update_idletasks()
        try:
            anim = self._crear_animacion(fig_export)
            exportar(anim, archivo, fps=max(1, round(self.velocidad * 1000 / anim.intervalo_ms)))
            messagebox.showinfo("Exportación lista", f"Se guardó:\n{archivo}")
        except Exception as e:  # falta ffmpeg/Pillow, ruta sin permisos, etc.
            messagebox.showerror("No se pudo exportar", str(e))
        finally:
            self.config(cursor="")
            self.lbl_aviso.config(text="Listo.")
