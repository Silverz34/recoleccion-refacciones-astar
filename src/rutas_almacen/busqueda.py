import math
import heapq
import time
from dataclasses import dataclass
from rutas_almacen.almacen import Pieza, costo_paso, penalizacion_nivel, PENALIZACION_ZONA
from typing import Any


@dataclass(frozen=True)
class Estado:
    nodo: str # donde esta el recolectpr
    pendientes: frozenset #codigos de las piezas que faltan

def es_meta(estado):
    return not estado.pendientes #ambas piezas recogidas en cualquier nodo

def sucesores(estado, nodos, grafo, inventario):
    """Genera (acción, nuevo_estado, (distancia, zona, nivel))"""
    for vecino, dist in grafo[estado.nodo].items():
        zona = round(costo_paso(nodos, grafo, estado.nodo, vecino)- dist, 6)
        yield (f"ir a{vecino}", Estado(vecino, estado.pendientes), (dist, zona, 0))


    for codigo in estado.pendientes:
        pieza = inventario[codigo]
        if pieza.nodo == estado.nodo:
            nuevo = Estado(estado.nodo, estado.pendientes - {codigo})
            yield (f"recoger {codigo}", nuevo, (0,0, penalizacion_nivel(pieza)))

def heuristica (estado, nodos, inventario,incluir_zona = True):
    if not estado.pendientes:
        return 0
    actual = nodos [estado.nodo]
    distancia_max = 0
    penalizaciones = 0
    zonas_pendientes = set()
    for codigo in estado.pendientes:
        pieza = inventario[codigo]
        destino = nodos[pieza.nodo]
        distancia = math. hypot(actual.x - destino.x, actual.y - destino.y)
        distancia_max = max(distancia_max, distancia)
        penalizaciones += penalizacion_nivel(pieza)
        zonas_pendientes.add(destino.zona)
    h = distancia_max + penalizaciones
    if incluir_zona:
     h += PENALIZACION_ZONA * len(zonas_pendientes - {actual.zona})
    return h


def reconstruir(estado, padre):
    pasos = []
    while padre[estado] is not None:
        previo, accion, desglose = padre[estado]
        pasos.append((accion, estado.nodo, desglose))
        estado = previo
    pasos.reverse()
    return pasos

def a_estrella(nodo_inicio, codigos, nodos, grafo, inventario, w = 1.0, incluir_zona=True):
    """A* ponderado: f(n) = g(n) + w * h(n)"""
    t0 = time.perf_counter()
    inicio = Estado(nodo_inicio, frozenset(codigos))
    g : dict [Estado, float] ={inicio: 0.0}  # mejor costo conocido para llegar
    padre : dict[Estado, tuple | None]={inicio: None} # estado : (estado previo,accion, desglose)
    contador = 0
    h0 = heuristica(inicio,nodos,inventario, incluir_zona)
    frontera = [(w * h0, contador, 0.0, inicio)]
    revisados = 0

    while frontera:
        _, _, g_actual, actual = heapq.heappop(frontera)
        if g_actual > g[actual]:
            continue
        revisados += 1


        if es_meta(actual):
            pasos = reconstruir(actual, padre)
            return {
                "pasos" : pasos,
                "orden" : [p[0].split()[1] for p in pasos if p[0]. startswith("recoger")],
                "costo" : g_actual,
                "distancia" : sum(p[2][0] for p in pasos),
                "zona" : sum(p[2][1] for p in pasos),
                "nivel" : sum(p[2][2] for p in pasos),
               "revisados" : revisados,
               "tiempo" : time.perf_counter() - t0,
            }

        for accion, nuevo, desglose, in sucesores(actual, nodos, grafo, inventario):
            g_nuevo = g_actual + sum(desglose)
            if g_nuevo < g.get(nuevo, float("inf")):
                g[nuevo] = g_nuevo
                padre[nuevo] = (actual, accion, desglose)
                contador += 1
                f_nuevo = g_nuevo + w * heuristica(nuevo, nodos, inventario, incluir_zona)
                heapq.heappush(frontera, (f_nuevo, contador, g_nuevo, nuevo))

    raise ValueError("No existe una ruta que recoja todas las piezas del pedido")



# metodo de comparacion, no se si sea necesario pero aja
def ruta_orden_pedido(nodo_inicio, codigos, nodos, grafo, inventario):
    """Línea base: ir primero a la primera pieza listada, luego a la segunda.
    Cada tramo usa la mejor ruta (w=1); solo el ORDEN queda fijo por el pedido."""
    claves = ("costo", "distancia", "zona", "nivel", "revisados", "tiempo")
    total : dict[str, Any] = {k: 0 for k in claves}
    actual = nodo_inicio
    for codigo in codigos:
        r = a_estrella(actual, [codigo], nodos, grafo, inventario, w=1.0)
        for k in claves:
            total[k] += r[k]
        actual = inventario[codigo].nodo
    total["orden"] = list(codigos)
    return total
