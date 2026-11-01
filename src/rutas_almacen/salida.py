from rich.console import Console
from rich.table import Table
from rutas_almacen.almacen import costo_paso, penalizacion_nivel


consola = Console()

def mostrar_ruta(resultado, inicio, nodos, inventario, titulo="Ruta de recoleccion"):
    pasos = resultado["pasos"]

    camino = [inicio] + [nodo for accion, nodo, _ in pasos if accion.startswith("ir a")]
    consola.rule(f"[bold]{titulo}[/bold]")
    consola. print(f"Posicion inicial : [bold]{inicio}[/bold]")
    consola.print("Recorrido: " + " -> ".join(camino))

    paradas = Table(title="Paradas de recoleccion")
    for columna in ("#", "pieza", "estante", "zona", "nivel", "penalización"):
        paradas.add_column(columna, justify="right" if columna in ("#", "nivel", "penalizacion")else "left")
    for i, codigo in enumerate(resultado["orden"],1):
        pieza = inventario[codigo]
        paradas.add_row(str(i), codigo, pieza.nodo, nodos[pieza.nodo].zona,
        str(pieza.nivel), str(penalizacion_nivel(pieza)))

    consola.print(paradas)


    costos = Table(title="Costo total desglosado")
    costos.add_column("Concepto")
    costos.add_column("Costo", justify="right")
    costos.add_row("Distancia", f"{resultado['distancia']:.2f}")
    costos.add_row("Penalización por cambio de zona", f"{resultado['zona']:.2f}")
    costos.add_row("Penalización por nivel",f"{resultado['nivel']:-2f}")
    costos.add_section()
    costos.add_row("[bold]Total[/bold]", f"[bold]{resultado['costo']:.2f}[/bold]")
    consola.print(costos)
    consola.print(f"Nodos revisados: {resultado['revisados']} | " f"Tiempo: {resultado['tiempo'] * 1000:.2f} ms")
