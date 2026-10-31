from dataclasses import dataclass
from almacen import costo_paso, penalizacion_nivel


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
