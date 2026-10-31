from dataclasses import dataclass

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

if __name__ == "__main__":
 print(len(crear_nodos()))
