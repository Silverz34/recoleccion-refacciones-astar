import matploit.pyplot as plt

def grafica_costos(df, archivo="costos.png")
    """Costo total por pedido: orden del pedido vs A* ponderado"""
    tabla = df.pivot(index="pedido", columns="metodo", values="costo")
    ax = tabla.plot(kind= "bar", figsize=(9, 5), rot = 0)
    ax.set_ylabel("costo total de recolección")
    ax.set_title("costo por pedido: orden del pedido vs A* ponderado")
    plt.tight_layout()
    plt.savefig(archivo, dpi=150)
    plt.show()



def grafica_nodos(df, archivo="nodos.png"):
    """Nodos revisados por pedido según el peso w."""
    solo_astar = df[df["metodo"].str.startswith("A*")]
    tabla = solo_astar.pivot(index="pedido", columns="metodo", value= "nodos revisados")
    ax= tabla.plot(kind="bar", figsize=(9,5), rot= 0)
    ax.set_ylabel("nodos revisados")
    ax.set_title("Nodos revisados por pedido según w")
    plt.tight_layout()
    plt.savefig(archivo, dpi=150)
    plt.show()
