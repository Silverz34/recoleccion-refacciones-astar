from almacen import crear_nodos, crear_grafo, INVENTARIO
from busqueda import Estado, sucesores

nodos = crear_nodos()
grafo = crear_grafo(nodos)

e = Estado("A2", frozenset({"R-101", "R-203"}))
for accion, nuevo, costo in sucesores(e, nodos, grafo, INVENTARIO):
    print(accion, costo)
