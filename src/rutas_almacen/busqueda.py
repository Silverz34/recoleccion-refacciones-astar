import math
import heapq
import time
from dataclasses import dataclass
from almacen import Pieza, costo_paso, penalizacion_nivel, PENALIZACION_ZONA



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
            yield (f"recoger{codigo}", nuevo, (0,0, penalizacion_nivel(pieza)))

def heuristica (estado, nodos, inventario, incluir_zona = True):
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
    g = {inicio: 0.0}
    padre =
