from random import choices
from rich import prompt
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

consola = Console()

def mostrar_inventario(inventario, nodos):
    tabla = Table(title="Inventario disponible")
    for columna in ("pieza", "estante", "Zona", "nivel"):
        tabla.add_column(columna)
    for pieza in inventario.values():
        tabla.add_row(pieza.codigo, pieza.nodo, nodos[pieza.nodo].zona, str(pieza.nivel))
    consola.print(tabla)


def pedir_pedido(nodos, inventario):
    """ Pide posicion inicial y dos piezas distintas; repite hasta que sea valida"""
    consola.print("Posiciones validas: " + ", ".join(nodos))
    inicio = Prompt.ask("Posición inicial del recolector", choices=list(nodos),
                            default="ENT", case_sensitive=False, show_choices=False)
    primera = Prompt.ask("Primera piezas del pedido", choices=list(inventario), case_sensitive=False, show_choices=False)
    restantes = [c for c in inventario if c != primera]
    segunda = Prompt.ask("Segunda pieza del pedido", choices=restantes, case_sensitive=False, show_choices=False)
    return inicio, [primera, segunda]


def pedir_peso():
    return float(Prompt.ask("Peso w del A*", choices=["1", "1.5", "2"], default="1"))
