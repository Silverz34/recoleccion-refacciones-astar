import math
from collections import defaultdict
from dataclasses import dataclass

PENALIZACION_NIVEL = {1: 0, 2: 2, 3: 4}
PENALIZACION_ZONA = 5


#Estructura del nodo
@dataclass(frozen=True)
class Nodo:
    id: str
    zona: str
    estante : int | None
    x: float
    y: float

#Ezquina superior izquierda de cada zona
ZONAS = {"A" : (0,0), "B": (20,0), "C":(0,16), "D":(20,16)}
COLUMNAS = (0,4,8) #3 estantes x fila
FILAS = (0,4) # 2 filas x zona

def crear_nodos():
    nodos = {}
    for zona , (ox, oy) in ZONAS.items():
        n = 1
        for dy in FILAS:
            for dx in COLUMNAS:
                id_ = f"{zona}{n}"
                nodos[id_] = Nodo(id_, zona, n, ox + dx, oy + dy)
                n += 1
        # Acceso por zona : entre el pasillo entran las dos filas
        nodos[f"{zona}-ACC"] = Nodo(f"{zona}-ACC", zona, None, ox + 4, oy + 2)
    nodos["P1"] = Nodo("P1", "Pasillo", None, 14, 2)
    nodos["P2"] = Nodo("P2", "Pasillo", None, 14, 18)
    nodos["ENT"] = Nodo("ENT", "Pasillo", None, 14, 10)
    return nodos


# construccion de las aristas

def crear_grafo(nodos):
    pares = []
    for zona in ZONAS:
        #Estantes vecinos en la misma fila
        for inicio in (1, 4):
            pares.append((f"{zona}{inicio}", f"{zona}{inicio + 1}"))
            pares.append((f"{zona}{inicio + 1}", f"{zona}{inicio + 2}"))
        #Cada estante con el acceso de su zona
        for n in range(1, 7):
            pares.append((f"{zona}{n}", f"{zona}-ACC"))

    #Acceso, pasillos centrales y entrada
    pares += [("A-ACC", "P1"), ("B-ACC", "P1"),
             ("C-ACC", "P2"), ("D-ACC", "P2"),
             ("P1", "ENT"), ("P2", "ENT")
    ]
    grafo = defaultdict(dict)
    for a, b in pares :
        d = math.hypot(nodos[a].x - nodos[b].x, nodos[a].y - nodos[b].y)
        grafo [a][b] = d
        grafo [b][a] = d
    return grafo


def costo_paso(nodos, grafo, origen, destino):
    """Distancia + 5 si se entra a una zona distinta de la actual."""
    costo = grafo[origen][destino]
    zona_destino = nodos[destino].zona
    if zona_destino != "Pasillo" and nodos[origen].zona != zona_destino:
        costo += PENALIZACION_ZONA
    return costo

# Inventario y penalizacion por nivel de estanteria

@dataclass(frozen= True)
class Pieza :
    codigo: str
    nodo : str
    nivel : int

INVENTARIO = {p.codigo: p for p in[
    Pieza("R-101", "A2", 1), Pieza("R-102", "A5", 3), Pieza("R-103", "A6", 2),
    Pieza("R-201", "B1", 2), Pieza("R-202", "B4", 1), Pieza("R-203", "B6", 3),
    Pieza("R-301", "C3", 1), Pieza("R-302", "C5", 2), Pieza("R-303", "C2", 3),
    Pieza("R-401", "D1", 3), Pieza("R-402", "D4", 2), Pieza("R-403", "D6", 1),
]}

def penalizacion_nivel(pieza):
    return PENALIZACION_NIVEL[pieza.nivel]

def validar_inventario (nodos, inventario):
    """Revisar que cada pieza esté en unn estante real y con un nivel valido"""
    for p in inventario.values():
        assert p.nodo in nodos and nodos[p.nodo].estante is not None, p
        assert p.nivel in PENALIZACION_NIVEL, p


if __name__ == "__main__":
 nodos = crear_nodos()
 grafo = crear_grafo(nodos)
 print(len(nodos))
 print(sum(len(v) for v in grafo.values())//2)
 print(costo_paso(nodos, grafo, "A-ACC", "P1"))
 print(costo_paso(nodos, grafo, "P1", "B-ACC"))
 print(round(costo_paso(nodos, grafo, "A1", "A-ACC"), 2))
 validar_inventario(nodos, INVENTARIO)
 print(len(INVENTARIO))
 print(penalizacion_nivel(INVENTARIO["R-102"]))
 print(penalizacion_nivel(INVENTARIO["R-101"]))
