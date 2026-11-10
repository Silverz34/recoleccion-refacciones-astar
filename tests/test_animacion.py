import matplotlib

matplotlib.use("Agg")

import shutil

import pytest
from matplotlib.animation import FuncAnimation
from matplotlib.figure import Figure

from rutas_almacen.almacen import INVENTARIO, crear_grafo, crear_nodos
from rutas_almacen.animacion import animar_busqueda, animar_ruta, exportar
from rutas_almacen.busqueda import a_estrella

pytestmark = pytest.mark.filterwarnings("ignore:Animation was deleted")

PEDIDOS = [
    ("ENT", ["R-101", "R-203"], 60.47),
    ("A1", ["R-403", "R-102"], 57.94),
    ("B1", ["R-401", "R-103"], 89.89),
    ("ENT", ["R-203", "R-302"], 78.47),
]


@pytest.fixture(scope="module")
def nodos():
    return crear_nodos()


@pytest.fixture(scope="module")
def grafo(nodos):
    return crear_grafo(nodos)


def _correr(nodos, grafo, inicio="B1", codigos=("R-401", "R-103"), w=1.0):
    traza = []
    r = a_estrella(inicio, list(codigos), nodos, grafo, INVENTARIO, w=w, traza=traza)
    return r, traza

class TestTraza:
    @pytest.mark.parametrize("inicio,codigos,costo", PEDIDOS)
    def test_traza_no_cambia_el_resultado(self, nodos, grafo, inicio, codigos, costo):
        sin = a_estrella(inicio, codigos, nodos, grafo, INVENTARIO)
        con_none = a_estrella(inicio, codigos, nodos, grafo, INVENTARIO, traza=None)
        con_lista = a_estrella(inicio, codigos, nodos, grafo, INVENTARIO, traza=[])
        for r in (con_none, con_lista):
            assert r["costo"] == sin["costo"]
            assert r["pasos"] == sin["pasos"]
            assert r["orden"] == sin["orden"]
            assert r["revisados"] == sin["revisados"]
        assert sin["costo"] == pytest.approx(costo, abs=0.01)

    @pytest.mark.parametrize("inicio,codigos,costo", PEDIDOS)
    def test_una_entrada_por_nodo_revisado(self, nodos, grafo, inicio, codigos, costo):
        traza = []
        r = a_estrella(inicio, codigos, nodos, grafo, INVENTARIO, traza=traza)
        assert len(traza) == r["revisados"]
        assert [t["paso"] for t in traza] == list(range(1, len(traza) + 1))

    def test_primera_y_ultima_entrada(self, nodos, grafo):
        r, traza = _correr(nodos, grafo)
        assert traza[0]["nodo"] == "B1" and traza[0]["previo"] is None
        assert traza[0]["accion"] == "inicio" and traza[0]["g"] == 0
        assert traza[-1]["meta"] and traza[-1]["pendientes"] == []
        assert traza[-1]["g"] == pytest.approx(r["costo"])
        assert not any(t["meta"] for t in traza[:-1])

    def test_f_es_g_mas_w_por_h(self, nodos, grafo):
        _, t1 = _correr(nodos, grafo, w=1.0)
        _, t2 = _correr(nodos, grafo, w=2.0)
        assert t2[0]["f"] == pytest.approx(2 * t1[0]["f"])

    def test_claves_de_la_traza(self, nodos, grafo):
        _, traza = _correr(nodos, grafo)
        esperadas = {"paso", "nodo", "pendientes", "g", "f", "frontera", "accion", "previo", "meta"}
        assert all(set(t) == esperadas for t in traza)

class TestAnimaciones:
    def test_animar_busqueda_cuadros(self, nodos, grafo):
        r, traza = _correr(nodos, grafo)
        sin_final = animar_busqueda(nodos, grafo, traza, INVENTARIO, ["R-401", "R-103"], "B1", fig=Figure())
        con_final = animar_busqueda(nodos, grafo, traza, INVENTARIO, ["R-401", "R-103"], "B1",
                                    resultado=r, fig=Figure())
        assert isinstance(sin_final, FuncAnimation) and isinstance(con_final, FuncAnimation)
        assert sin_final.n_cuadros == len(traza)
        assert con_final.n_cuadros == len(traza) + 1

    def test_animar_busqueda_dibuja_todos_los_cuadros(self, nodos, grafo):
        r, traza = _correr(nodos, grafo)
        fig = Figure()
        anim = animar_busqueda(nodos, grafo, traza, INVENTARIO, ["R-401", "R-103"], "B1", resultado=r, fig=fig)
        for k in range(anim.n_cuadros):
            anim._func(k)
            fig.canvas.draw()

    def test_animar_busqueda_traza_vacia(self, nodos, grafo):
        with pytest.raises(ValueError):
            animar_busqueda(nodos, grafo, [], fig=Figure())

    def test_animar_ruta_cuadros(self, nodos, grafo):
        r, _ = _correr(nodos, grafo)
        movimientos = sum(1 for a, _, _ in r["pasos"] if a.startswith("ir a"))
        recogidas = sum(1 for a, _, _ in r["pasos"] if a.startswith("recoger"))
        anim = animar_ruta(nodos, grafo, r, "B1", INVENTARIO, ["R-401", "R-103"],
                           subpasos=4, pausa_recoger=3, fig=Figure())
        assert isinstance(anim, FuncAnimation)
        assert anim.n_cuadros == 1 + 4 * movimientos + 3 * recogidas

    def test_animar_ruta_termina_en_el_costo_total(self, nodos, grafo):
        r, _ = _correr(nodos, grafo)
        fig = Figure()
        anim = animar_ruta(nodos, grafo, r, "B1", INVENTARIO, ["R-401", "R-103"], fig=fig)
        anim._func(anim.n_cuadros - 1)
        textos = [t.get_text() for t in fig.axes[0].texts]
        assert any(f"costo acumulado = {r['costo']:.2f} de {r['costo']:.2f}" in t for t in textos)
        assert any("pendientes: ninguna" in t for t in textos)

    def test_pedido_con_pieza_en_el_inicio(self, nodos, grafo):
        r, traza = _correr(nodos, grafo, inicio="A2", codigos=("R-101", "R-102"))
        anim = animar_ruta(nodos, grafo, r, "A2", INVENTARIO, ["R-101", "R-102"], fig=Figure())
        anim._func(0)
        anim._func(anim.n_cuadros - 1)

class TestExportar:
    def _anim_corta(self, nodos, grafo):
        r, traza = _correr(nodos, grafo, inicio="ENT", codigos=("R-101", "R-203"))
        return animar_busqueda(nodos, grafo, traza[:4], INVENTARIO, ["R-101", "R-203"], "ENT", fig=Figure())

    def test_extension_no_soportada(self, nodos, grafo, tmp_path):
        with pytest.raises(ValueError):
            exportar(self._anim_corta(nodos, grafo), tmp_path / "video.avi")

    def test_exportar_gif(self, nodos, grafo, tmp_path):
        pytest.importorskip("PIL")
        destino = exportar(self._anim_corta(nodos, grafo), tmp_path / "busqueda.gif", dpi=50)
        assert destino.exists() and destino.stat().st_size > 0

    def test_exportar_mp4(self, nodos, grafo, tmp_path):
        if shutil.which("ffmpeg") is None:
            pytest.skip("ffmpeg no está instalado")
        destino = exportar(self._anim_corta(nodos, grafo), tmp_path / "busqueda.mp4", dpi=50)
        assert destino.exists() and destino.stat().st_size > 0
