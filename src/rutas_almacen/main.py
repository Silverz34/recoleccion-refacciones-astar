from almacen import crear_nodos, crear_grafo, INVENTARIO
from busqueda import Estado, sucesores, heuristica, a_estrella

nodos = crear_nodos()
grafo = crear_grafo(nodos)

for w in (1, 1.5, 2):
    r = a_estrella("P2", ["R-101", "R-303"], nodos, grafo, INVENTARIO, w=w)
    print(w, round(r["costo"],2),r["orden"], r["revisados"], round(r["tiempo"]* 1000, 2), "ms")
