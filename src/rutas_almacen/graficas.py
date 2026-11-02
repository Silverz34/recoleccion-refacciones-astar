import matplotlib.pyplot as plt

def grafica_costos(df, archivo="costos.png"):
    """Costo total por pedido: orden del pedido vs A* ponderado"""
    plt.close('all') # Limpiar figuras previas en memoria
    tabla = df.pivot(index="Pedido", columns="Método", values="Costo")
    ax = tabla.plot(kind= "bar", figsize=(6, 4), rot = 0)
    ax.set_ylabel("Costo total de recolección")
    ax.set_title("Costo por pedido: orden vs A* ponderado")

    fig = ax.get_figure()
    fig.tight_layout()
    fig.savefig(archivo, dpi=150) # Sigue guardando la imagen
    return fig

def grafica_nodos(df, archivo="nodos.png"):
    """Nodos revisados por pedido según el peso w."""
    solo_astar = df[df["Método"].str.startswith("A*")]
    tabla = solo_astar.pivot(index="Pedido", columns="Método", values="Nodos revisados")
    ax = tabla.plot(kind="bar", figsize=(6, 4), rot= 0)
    ax.set_ylabel("Nodos revisados")
    ax.set_title("Nodos revisados por pedido según w")

    fig = ax.get_figure()
    fig.tight_layout()
    fig.savefig(archivo, dpi=150) # Sigue guardando la imagen
    return fig
