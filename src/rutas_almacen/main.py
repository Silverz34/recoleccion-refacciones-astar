from almacen import crear_nodos, crear_grafo, INVENTARIO
from busqueda import Estado, sucesores, heuristica

nodos = crear_nodos()
grafo = crear_grafo(nodos)

e = Estado("A2", frozenset({"R-101", "R-203"}))
for accion, nuevo, costo in sucesores(e, nodos, grafo, INVENTARIO):
    print(accion, costo)

e4 = Estado("A2", frozenset({"R-101", "R-203"}))
print(round(heuristica(e4, nodos, INVENTARIO), 2))
print(round(heuristica(e4, nodos, INVENTARIO, incluir_zona=False), 2))

e5 = Estado("ENT", frozenset({"R-101", "R-203"}))
print(round(heuristica(e5, nodos, INVENTARIO), 2))
