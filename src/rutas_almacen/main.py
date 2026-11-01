import pandas as pd
from rutas_almacen.almacen import crear_nodos, crear_grafo, INVENTARIO
from rutas_almacen.busqueda import a_estrella, ruta_orden_pedido
from rutas_almacen.graficas import grafica_costos, grafica_nodos
from rutas_almacen.salida import mostrar_ruta


PEDIDOS = [
    ("P1", "ENT", ["R-101", "R-203"]),
    ("P2", "A1", ["R-403", "R-102"]),
    ("P3", "B1", ["R-401", "R-103"]),
    ("P4", "ENT", ["R-203", "R-302"]),
]
PESOS = (1, 1.5, 2)

def fila(pedido, metodo, r, cota=None):
    return {
        "Pedido": pedido,
        "Método": metodo,
        "Orden": " → ".join(r["orden"]),
        "Costo": round(r["costo"], 2),
        "Distancia": round(r["distancia"], 2),
        "Zona": r["zona"],
        "Nivel": r["nivel"],
        "Nodos revisados": r["revisados"],
        "Tiempo (ms)": round(r["tiempo"] * 1000, 3),
        "Cumple cota": cota,
    }

def evaluar(nodos, grafo):
    filas = []
    for pedido, inicio, codigos in PEDIDOS:
        base = ruta_orden_pedido(inicio, codigos, nodos, grafo, INVENTARIO)
        filas.append(fila(pedido, "Orden del pedido", base))
        r_optimo = a_estrella(inicio, codigos, nodos, grafo, INVENTARIO, w=1.0)
        optimo = r_optimo["costo"]
        for w in PESOS:
            r = r_optimo if w == 1 else a_estrella(inicio, codigos, nodos, grafo, INVENTARIO, w=w)
            cota = r["costo"] <= w * optimo + 1e-9
            filas.append(fila(pedido, f"A* w={w}", r, cota))
    return pd.DataFrame(filas)

if __name__ == "__main__":
    nodos = crear_nodos()
    grafo = crear_grafo(nodos)
    df = evaluar(nodos, grafo)
    print(df.to_string(index=False))
    grafica_costos(df)
    grafica_nodos(df)
    r = a_estrella("A1", ["R-403", "R-102"], nodos, grafo, INVENTARIO, w=1.0)
    mostrar_ruta(r, "A1", nodos, INVENTARIO)
