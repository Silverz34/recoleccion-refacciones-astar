from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize, to_rgba

COLOR_ZONA = {
    "A": "#cfe3f7",
    "B": "#d4efc8",
    "C": "#fde3b8",
    "D": "#efd0ec",
    "Pasillo": "#e4e4e4",
}
COLOR_PIEZA_PENDIENTE = "#f5b700"
COLOR_PIEZA_RECOGIDA = "#2e9e5b"
COLOR_RUTA = "#d62839"
COLOR_ARBOL = "#e8890c"


# --------------------------------------------------------------------------
# Dibujo base del almacén
# --------------------------------------------------------------------------
def _preparar_ejes(fig, nodos):
    fig.clf()
    fig.subplots_adjust(bottom=0.2, top=0.93)  # espacio abajo para el recuadro de texto
    ax = fig.add_subplot(111)
    xs = [n.x for n in nodos.values()]
    ys = [n.y for n in nodos.values()]
    ax.set_xlim(min(xs) - 3, max(xs) + 3)
    ax.set_ylim(max(ys) + 3, min(ys) - 3)  # eje y invertido: la zona A queda arriba
    ax.set_aspect("equal", adjustable="box")
    ax.set_xticks([])
    ax.set_yticks([])
    for lado in ax.spines.values():
        lado.set_visible(False)
    return ax


def dibujar_almacen(ax, nodos, grafo, inventario=None, codigos=None):
    """Dibuja aristas, nodos (coloreados por zona) y las piezas del pedido.

    Devuelve un diccionario con los artistas que las animaciones actualizan:
    "ids" (lista de ids en el orden del scatter), "scatter", "piezas" (scatter
    de estrellas o None) y "codigos_piezas" (códigos en el orden del scatter).
    """
    ids = list(nodos)
    segmentos = []
    vistos = set()
    for a, vecinos in grafo.items():
        for b in vecinos:
            if (b, a) in vistos:
                continue
            vistos.add((a, b))
            segmentos.append([(nodos[a].x, nodos[a].y), (nodos[b].x, nodos[b].y)])
    ax.add_collection(LineCollection(segmentos, colors="#b9b9b9", linewidths=1.2, zorder=1))

    scatter = ax.scatter(
        [nodos[i].x for i in ids], [nodos[i].y for i in ids],
        s=330, c=[COLOR_ZONA[nodos[i].zona] for i in ids],
        edgecolors="#6b6b6b", linewidths=0.8, zorder=3,
    )
    for i in ids:
        ax.text(nodos[i].x, nodos[i].y, i.replace("-ACC", "\nACC"), ha="center",
                va="center", fontsize=6.5, zorder=5, color="#222222")

    piezas = None
    codigos_piezas = []
    if inventario and codigos:
        codigos_piezas = list(codigos)
        px = [nodos[inventario[c].nodo].x for c in codigos_piezas]
        py = [nodos[inventario[c].nodo].y - 1.35 for c in codigos_piezas]
        piezas = ax.scatter(px, py, s=170, marker="*", c=COLOR_PIEZA_PENDIENTE,
                            edgecolors="#7a5c00", linewidths=0.7, zorder=6)
        for c, x, y in zip(codigos_piezas, px, py):
            ax.text(x, y - 1.0, f"{c} (niv {inventario[c].nivel})", ha="center",
                    va="bottom", fontsize=7, zorder=6, color="#7a5c00", fontweight="bold")
    return {"ids": ids, "scatter": scatter, "piezas": piezas, "codigos_piezas": codigos_piezas}


def _colores_piezas(codigos_piezas, pendientes):
    return [COLOR_PIEZA_PENDIENTE if c in pendientes else COLOR_PIEZA_RECOGIDA for c in codigos_piezas]


def _camino_de_pasos(inicio, resultado):
    """Nodos recorridos en la ruta final, a partir de resultado['pasos']."""
    return [inicio] + [nodo for accion, nodo, _ in resultado["pasos"] if accion.startswith("ir a")]


# --------------------------------------------------------------------------
# Animación 1: exploración de A*
# --------------------------------------------------------------------------
def animar_busqueda(nodos, grafo, traza, inventario=None, codigos=None, inicio=None,
                    resultado=None, intervalo=450, fig=None, repetir=False):
    """Anima los estados que A* va expandiendo, en orden.

    Cada nodo se colorea cuando se expande y se oscurece cuantas más veces se
    visita (un mismo nodo se puede expandir varias veces porque el estado
    incluye las piezas pendientes). Las líneas naranjas son los movimientos
    por los que A* llegó a cada estado. Si se pasa `resultado`, se agrega un
    cuadro final con la ruta óptima resaltada.

    Cuadros = len(traza) (+1 si hay resultado). Devuelve un FuncAnimation.
    """
    if not traza:
        raise ValueError("La traza está vacía: ejecuta a_estrella con traza=[]")
    fig = fig or plt.figure(figsize=(9, 6.4))
    ax = _preparar_ejes(fig, nodos)
    artistas = dibujar_almacen(ax, nodos, grafo, inventario, codigos)
    ids, scatter = artistas["ids"], artistas["scatter"]
    indice = {n: k for k, n in enumerate(ids)}

    # visitas acumuladas por nodo después de cada paso
    visitas = np.zeros((len(traza) + 1, len(ids)), dtype=int)
    for k, t in enumerate(traza, start=1):
        visitas[k] = visitas[k - 1]
        visitas[k, indice[t["nodo"]]] += 1
    maximo = max(2, int(visitas.max()))
    norma = Normalize(vmin=0, vmax=maximo)
    mapa = plt.get_cmap("YlOrRd")
    base = [to_rgba(COLOR_ZONA[nodos[i].zona]) for i in ids]

    arbol = LineCollection([], colors=COLOR_ARBOL, linewidths=2.0, alpha=0.8, zorder=2)
    ax.add_collection(arbol)
    ruta, = ax.plot([], [], color=COLOR_RUTA, linewidth=4.5, zorder=2.6, solid_capstyle="round")
    actual, = ax.plot([], [], marker="o", markersize=22, markerfacecolor="none",
                      markeredgecolor="#1b4fd8", markeredgewidth=3, linestyle="none", zorder=7)

    titulo = ax.set_title("", fontsize=11, loc="left")
    info = ax.text(0.0, -0.02, "", transform=ax.transAxes, fontsize=9, va="top",
                   family="monospace", bbox=dict(boxstyle="round", fc="white", ec="#bbbbbb", alpha=0.95), zorder=10)
    barra = fig.colorbar(plt.cm.ScalarMappable(norm=norma, cmap=mapa), ax=ax, fraction=0.03, pad=0.01)
    barra.set_label("veces que se expandió el nodo", fontsize=8)
    barra.ax.tick_params(labelsize=7)

    transiciones = []  # segmentos (previo -> nodo) acumulados
    for t in traza:
        if t["previo"] is not None and t["previo"] != t["nodo"]:
            transiciones.append([(nodos[t["previo"]].x, nodos[t["previo"]].y), (nodos[t["nodo"]].x, nodos[t["nodo"]].y)])
        else:
            transiciones.append(None)

    camino = _camino_de_pasos(inicio, resultado) if (resultado is not None and inicio) else None
    n_cuadros = len(traza) + (1 if camino else 0)

    def actualizar(k):
        if k < len(traza):
            t = traza[k]
            cuentas = visitas[k + 1]
            colores = [to_rgba(mapa(norma(c))) if c > 0 else b for c, b in zip(cuentas, base)]
            scatter.set_facecolor(colores)
            arbol.set_segments([s for s in transiciones[: k + 1] if s])
            actual.set_data([nodos[t["nodo"]].x], [nodos[t["nodo"]].y])
            ruta.set_data([], [])
            if artistas["piezas"] is not None:
                artistas["piezas"].set_facecolor(_colores_piezas(artistas["codigos_piezas"], t["pendientes"]))
            titulo.set_text(f"Exploración de A*  ·  paso {t['paso']} de {len(traza)}")
            pend = ", ".join(t["pendientes"]) or "ninguna"
            llegada = t["accion"].replace("ir a", "ir a ")
            info.set_text(
                f"expande: {t['nodo']}   (llegó por: {llegada})\n"
                f"pendientes: {pend}\n"
                f"g = {t['g']:.2f}   f = {t['f']:.2f}   frontera = {t['frontera']}"
                + ("\n¡META!: todas las piezas recogidas" if t["meta"] else "")
            )
        else:  # cuadro final con la ruta óptima
            ruta.set_data([nodos[n].x for n in camino], [nodos[n].y for n in camino])
            actual.set_data([], [])
            if artistas["piezas"] is not None:
                artistas["piezas"].set_facecolor(_colores_piezas(artistas["codigos_piezas"], []))
            titulo.set_text("Exploración de A*  ·  ruta óptima encontrada")
            info.set_text(
                f"orden de recolección: {' → '.join(resultado['orden'])}\n"
                f"costo total = {resultado['costo']:.2f}   nodos revisados = {resultado['revisados']}"
            )
        return ()

    anim = animation.FuncAnimation(fig, actualizar, frames=n_cuadros, interval=intervalo,
                                   repeat=repetir, blit=False)
    anim.n_cuadros = n_cuadros
    anim.intervalo_ms = intervalo
    return anim


# --------------------------------------------------------------------------
# Animación 2: recorrido final del recolector
# --------------------------------------------------------------------------
def animar_ruta(nodos, grafo, resultado, inicio, inventario=None, codigos=None,
                subpasos=6, pausa_recoger=5, intervalo=90, fig=None, repetir=False):
    """Anima al recolector siguiendo resultado['pasos'] ("ir a X" y "recoger R-xxx").

    Cada movimiento se interpola en `subpasos` cuadros para que se vea fluido;
    al recoger una pieza se queda `pausa_recoger` cuadros y la estrella pasa a
    verde. Muestra el costo acumulado.

    Cuadros = 1 + subpasos * (movimientos) + pausa_recoger * (recogidas).
    Devuelve un FuncAnimation.
    """
    pasos = resultado["pasos"]
    fig = fig or plt.figure(figsize=(9, 6.4))
    ax = _preparar_ejes(fig, nodos)
    if codigos is None and inventario is not None:
        codigos = resultado.get("orden")
    artistas = dibujar_almacen(ax, nodos, grafo, inventario, codigos)

    # línea de tiempo: (x, y, costo acumulado, texto, pendientes, indice_ruta)
    x0, y0 = nodos[inicio].x, nodos[inicio].y
    pendientes = set(codigos or [])
    costo = 0.0
    lineas = [(x0, y0, 0.0, f"inicio en {inicio}", set(pendientes), 1)]
    px, py = x0, y0
    nodo_actual = inicio
    for accion, nodo, desglose in pasos:
        costo_paso = sum(desglose)
        if accion.startswith("ir a"):
            qx, qy = nodos[nodo].x, nodos[nodo].y
            for s in range(1, subpasos + 1):
                f = s / subpasos
                lineas.append((px + (qx - px) * f, py + (qy - py) * f, costo + costo_paso * f,
                               f"{nodo_actual} → {nodo}", set(pendientes), 1))
            px, py, nodo_actual = qx, qy, nodo
            costo += costo_paso
        else:  # recoger
            codigo = accion.split()[1]
            pendientes.discard(codigo)
            costo += costo_paso
            for _ in range(pausa_recoger):
                lineas.append((px, py, costo, f"recoge {codigo} en {nodo}  (+{costo_paso:g})", set(pendientes), 0))

    n_cuadros = len(lineas)
    estela, = ax.plot([], [], color=COLOR_RUTA, linewidth=3.5, zorder=2.6, solid_capstyle="round")
    recolector, = ax.plot([], [], marker="s", markersize=15, markerfacecolor="#1b4fd8",
                          markeredgecolor="white", markeredgewidth=1.5, linestyle="none", zorder=8)
    titulo = ax.set_title("", fontsize=11, loc="left")
    info = ax.text(0.0, -0.02, "", transform=ax.transAxes, fontsize=9, va="top",
                   family="monospace", bbox=dict(boxstyle="round", fc="white", ec="#bbbbbb", alpha=0.95), zorder=10)

    def actualizar(k):
        x, y, c, texto, pend, _ = lineas[k]
        estela.set_data([l[0] for l in lineas[: k + 1]], [l[1] for l in lineas[: k + 1]])
        recolector.set_data([x], [y])
        if artistas["piezas"] is not None:
            artistas["piezas"].set_facecolor(_colores_piezas(artistas["codigos_piezas"], pend))
        titulo.set_text(f"Ruta del recolector  ·  cuadro {k + 1} de {n_cuadros}")
        info.set_text(f"{texto}\ncosto acumulado = {c:.2f} de {resultado['costo']:.2f}\n"
                      f"pendientes: {', '.join(sorted(pend)) or 'ninguna'}")
        return ()

    anim = animation.FuncAnimation(fig, actualizar, frames=n_cuadros, interval=intervalo,
                                   repeat=repetir, blit=False)
    anim.n_cuadros = n_cuadros
    anim.intervalo_ms = intervalo
    return anim


# --------------------------------------------------------------------------
# Exportar
# --------------------------------------------------------------------------
def exportar(anim, archivo, fps=None, dpi=110):
    """Guarda la animación en .mp4 (requiere ffmpeg) o .gif (requiere Pillow).

    fps=None usa la velocidad de la animación. Devuelve la ruta del archivo.
    Lanza RuntimeError con un mensaje claro si falta ffmpeg o Pillow.
    """
    ruta = Path(archivo)
    ext = ruta.suffix.lower()
    fps = fps or max(1, round(1000 / getattr(anim, "intervalo_ms", 200)))
    if ext == ".mp4":
        if not animation.writers.is_available("ffmpeg"):
            raise RuntimeError("Para exportar MP4 se necesita ffmpeg instalado y en el PATH. "
                               "Instálalo o exporta como .gif.")
        escritor = animation.FFMpegWriter(fps=fps, codec="libx264",
                                          extra_args=["-pix_fmt", "yuv420p"])
    elif ext == ".gif":
        try:
            import PIL  # noqa: F401
        except ImportError as e:
            raise RuntimeError("Para exportar GIF se necesita Pillow (pip install pillow).") from e
        escritor = animation.PillowWriter(fps=fps)
    else:
        raise ValueError("Extensión no soportada: usa .mp4 o .gif")
    anim.save(str(ruta), writer=escritor, dpi=dpi)
    return ruta
