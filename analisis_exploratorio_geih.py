"""AED de GEIH: Cali A.M., octubre-diciembre de 2025.

En extraccion.py, reemplaza el bloque que elimina columnas y une módulos por:
    from analisis_exploratorio_geih import unir_modulos, explorar_geih
    df_datos_consolidados = unir_modulos(df_caracteristicas, df_ocupados)

Después de renombrar df_filtrado, agrega:
    df_aed, tablas_aed = explorar_geih(df_filtrado)

Abre las tablas y los gráficos en el navegador. Cada tabla tiene un botón PNG.
Guarda la vista y las imágenes de tablas y gráficos a 300 ppp
en resultados_aed, junto a este archivo. No requiere paquetes adicionales.
Para elegir otra carpeta o evitar abrir el navegador:
    explorar_geih(df_filtrado, carpeta_salida="mis_resultados", abrir_informe=False)

Requiere pandas, numpy, matplotlib y tu archivo diccionarios_geih.py.
Definiciones: hojas Rev - Reglas y Dominios del Excel del proyecto.
Fuente GEIH: https://microdatos.dane.gov.co/index.php/catalog/853
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from html import escape
import base64
import webbrowser
from textwrap import fill
from diccionarios_geih import DICCIONARIOS


def unir_modulos(caracteristicas, ocupados):
    """Une una vez cada persona-mes y detecta duplicados o falta de coincidencia."""
    claves = ["PER", "MES", "DIRECTORIO", "SECUENCIA_P", "ORDEN"]
    a, b = caracteristicas.copy(), ocupados.copy()
    for tabla in (a, b):
        tabla[claves] = tabla[claves].apply(pd.to_numeric, errors="raise")
        if tabla[claves].isna().any().any():
            raise ValueError("Hay identificadores vacíos: revisa las llaves de unión.")
    # Los campos compartidos se conservan desde Características generales.
    comunes = a.columns.intersection(b.columns).difference(claves)
    unido = a.merge(b.drop(columns=comunes), on=claves, how="right",
                    validate="one_to_one", indicator=True)
    if unido["_merge"].ne("both").any():
        raise ValueError("Hay ocupados sin coincidencia en Características generales.")
    return unido.drop(columns="_merge")


def explorar_geih(df_filtrado, carpeta_salida=None, abrir_informe=True):
    """Presenta tablas e histogramas en el navegador y devuelve base y resúmenes."""
    # 1. Copia numérica: usar df_filtrado, antes de reemplazar códigos por textos.
    if not df_filtrado.columns.is_unique:
        raise ValueError("Hay columnas duplicadas. Revisa la selección antes del AED.")
    d = df_filtrado.copy()
    numericas = ["Edad", "Ingreso_Laboral", "Horas_Trabajo_Semanales"]
    codigos = ["AREA", "PER", "MES", "Rama_Act_Empleo_Ppal", "Categoria_Trabajo",
               "Sexo_Al_Nacer", "Nivel_Educativo", "FEX_C18"]
    d[numericas + codigos] = d[numericas + codigos].apply(
        pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
    d = d.loc[d["AREA"].eq(76) & d["PER"].eq(2025)
              & d["MES"].isin([10, 11, 12])].copy()
    if set(d["MES"].dropna()) != {10, 11, 12}:
        raise ValueError("Revisa AREA, PER y MES: deben existir los tres meses de 2025.")
    revision = {"Registros de Cali A.M. antes del filtro de edad": len(d)}
    edad_valida = d["Edad"].ge(15) & d["Edad"].mod(1).eq(0)
    revision["Excluidos por edad faltante, menor de 15 o no entera"] = (~edad_valida).sum()
    d = d.loc[edad_valida].copy()
    revision["Registros incluidos en el análisis"] = len(d)
    if d.empty:
        raise ValueError("No hay registros con edad válida para el análisis.")

    # 2. Grupos: otras posiciones y ramas desconocidas permanecen identificadas.
    rama = d["Rama_Act_Empleo_Ppal"]
    d["Sector"] = np.select(
        [rama.between(10, 33) & rama.mod(1).eq(0),
         rama.between(1, 99) & rama.mod(1).eq(0)],
        ["Manufactura", "Demás sectores"], default="Sin clasificar")
    d["Tipo_Trabajador"] = d["Categoria_Trabajo"].map({
        1: "Asalariado", 2: "Asalariado", 3: "Asalariado", 7: "Asalariado",
        4: "Cuenta propia", 5: "Otras posiciones", 6: "Otras posiciones",
        8: "Otras posiciones"}).fillna("Sin clasificar")
    d["Grupo_Edad"] = pd.cut(d["Edad"], bins=[14, 28, 54, np.inf],
                              labels=["15–28", "29–54", "55 o más"])
    d["Mes"] = d["MES"].map({10: "Octubre", 11: "Noviembre", 12: "Diciembre"})
    for columna, codigo in [("Sexo_Al_Nacer", "P3271"), ("Nivel_Educativo", "P3042")]:
        etiquetas = {int(k): v for k, v in DICCIONARIOS[codigo].items()}
        d[columna] = d[columna].map(etiquetas).fillna("Sin dato/código desconocido")

    # Los ceros de ingreso son válidos; negativos y horas imposibles se reportan.
    revision["Ingresos negativos tratados como faltantes"] = d["Ingreso_Laboral"].lt(0).sum()
    revision["Horas fuera de 0–168 tratadas como faltantes"] = (
        d["Horas_Trabajo_Semanales"].notna()
        & ~d["Horas_Trabajo_Semanales"].between(0, 168)).sum()
    d["Ingreso_Laboral"] = d["Ingreso_Laboral"].where(d["Ingreso_Laboral"].ge(0))
    d["Horas_Trabajo_Semanales"] = d["Horas_Trabajo_Semanales"].where(
        d["Horas_Trabajo_Semanales"].between(0, 168))
    d["Peso"] = d["FEX_C18"].where(d["FEX_C18"].gt(0))
    revision["Registros sin peso válido"] = d["Peso"].isna().sum()
    m = d.loc[d["Sector"].eq("Manufactura")].copy()
    tablas = {"Preparación de la base": pd.Series(revision, name="Registros")}

    # 3. Conteos reales de registros, sin factores de expansión.
    grupos = ["Sector", "Tipo_Trabajador"]
    tablas["Tamaños muestrales"] = d.groupby(
        ["MES"] + grupos + ["Grupo_Edad"], observed=True).size().rename("n_registros")
    tablas["Calidad de variables numéricas"] = pd.DataFrame({
        "Faltantes_o_invalidos": d[numericas].isna().sum(),
        "Porcentaje": d[numericas].isna().mean() * 100})

    # Media, mediana, dispersión y percentiles muestrales; media ponderada aparte.
    def resumen(base, campos):
        filas = []
        for nombre, g in base.groupby(campos, observed=True):
            nombre = nombre if isinstance(nombre, tuple) else (nombre,)
            for variable in numericas:
                x = g[variable].dropna()
                q1, q3 = x.quantile([0.25, 0.75])
                r = dict(zip(campos, nombre))
                valido = g[variable].notna() & g["Peso"].notna()
                r.update(Variable=variable, n=x.size, n_pond=valido.sum(), Faltantes=len(g) - x.size,
                         Media=x.mean(), Mediana=x.median(), DE=x.std(),
                         Min=x.min(), P25=q1, P75=q3, Max=x.max(), Asimetria=x.skew(),
                         Media_pond=np.average(g.loc[valido, variable],
                             weights=g.loc[valido, "Peso"]) if valido.any() else np.nan)
                filas.append(r)
        return pd.DataFrame(filas)

    tablas["Descriptivos muestrales por sector y posición (Media_pond usa FEX)"] = resumen(d, grupos)
    # Los extremos por regla 1.5*RIC se señalan; no se eliminan automáticamente.
    ingreso = m["Ingreso_Laboral"]
    q1, q3 = ingreso.quantile([0.25, 0.75])
    m["Ingreso_Extremo"] = ingreso.lt(q1 - 1.5 * (q3 - q1)) | ingreso.gt(q3 + 1.5 * (q3 - q1))
    tablas["Revisión de ingreso en manufactura"] = pd.Series({
        "Registros": len(m), "Faltantes_o_invalidos": ingreso.isna().sum(),
        "Ingresos_cero": ingreso.eq(0).sum(), "Extremos_1.5_RIC": m["Ingreso_Extremo"].sum()})

    # 4. Composición ponderada. Cada fila suma 100 % entre edades válidas.
    # Aquí no se estiman totales trimestrales: dividir todos los pesos por 3
    # no cambia estas proporciones ni las medias ponderadas.
    p = d.loc[d["Peso"].notna()]
    for campos in [["Sector"], grupos]:
        t = p.pivot_table(index=campos, columns="Grupo_Edad", values="Peso",
                          aggfunc="sum", observed=True, fill_value=0)
        tablas["Edad ponderada (%) por " + ", ".join(campos)] = t.div(t.sum(axis=1), axis=0) * 100

    # 5. Edad–ingreso y controles: tablas de manufactura con todas las posiciones.
    for campo in ["Grupo_Edad", "Sexo_Al_Nacer", "Nivel_Educativo", "Tipo_Trabajador"]:
        tablas["Descriptivos muestrales de manufactura por " + campo] = resumen(m, [campo])
    for campo in ["Sexo_Al_Nacer", "Nivel_Educativo", "Tipo_Trabajador"]:
        g = m.groupby(campo, observed=True)
        t = g.size().to_frame("n_registros")
        pesos = g["Peso"].sum(min_count=1)
        t["Porcentaje_ponderado"] = pesos / pesos.sum() * 100
        tablas["Composición de manufactura por " + campo] = t

    # 6. Histogramas comparables: mismos intervalos y 100 % dentro de cada grupo.
    plt.style.use("seaborn-v0_8-whitegrid")
    colores = ["#176B87", "#D77A36"]
    figuras = []

    def histograma(ax, base, variable, campo, categorias, bins, etiqueta):
        for categoria, color in zip(categorias, colores):
            g = base.loc[base[campo].eq(categoria)].dropna(subset=[variable, "Peso"])
            if not g.empty:
                ax.hist(g[variable], bins=bins, weights=100 * g["Peso"] / g["Peso"].sum(),
                        histtype="step", linewidth=2, color=color,
                        label=f"{categoria} (n={len(g)})")
        ax.set(xlabel=etiqueta, ylabel="Porcentaje ponderado del grupo")
        if ax.get_legend_handles_labels()[0]:
            ax.legend(fontsize=9)

    edades = np.arange(15, max(25, np.ceil(d["Edad"].max() / 5) * 5 + 5), 5)
    fig, ax = plt.subplots(1, 2, figsize=(12, 4), constrained_layout=True)
    histograma(ax[0], d, "Edad", "Sector", ["Manufactura", "Demás sectores"], edades, "Edad (años)")
    histograma(ax[1], m, "Edad", "Tipo_Trabajador", ["Asalariado", "Cuenta propia"], edades, "Edad (años)")
    ax[0].set_title("Edad: manufactura y demás sectores")
    ax[1].set_title("Edad en manufactura por posición")
    fig.suptitle("Cali A.M. · Octubre–diciembre de 2025")
    figuras.append(("Distribución de edades por sector y posición ocupacional", fig))

    mi = m.dropna(subset=["Ingreso_Laboral", "Peso"]).copy()
    if not mi.empty:
        mi["Ingreso_Millones"] = mi["Ingreso_Laboral"] / 1_000_000
        mi["Log_Ingreso"] = np.log1p(mi["Ingreso_Laboral"])
        fig, ax = plt.subplots(1, 2, figsize=(12, 4), constrained_layout=True)
        for eje, variable, etiqueta in zip(ax, ["Ingreso_Millones", "Log_Ingreso"],
                ["Ingreso laboral (millones de COP)", "log(1 + ingreso laboral en COP)"]):
            bins = np.histogram_bin_edges(mi[variable], bins=25)
            histograma(eje, mi, variable, "Tipo_Trabajador", ["Asalariado", "Cuenta propia"], bins, etiqueta)
        fig.suptitle("Ingresos en manufactura · Incluye ceros y valores extremos")
        figuras.append(("Distribución del ingreso por posición ocupacional", fig))

        # Ingreso por grupo de edad: barras con los mismos intervalos y escalas.
        # Cada panel suma 100 %; se conservan los ingresos cero y los extremos.
        limite = max(1, np.ceil(mi["Ingreso_Millones"].max()))
        intervalos = np.linspace(0, limite, 11)
        fig, ejes = plt.subplots(1, 3, figsize=(14, 5), sharex=True, sharey=True,
                                 constrained_layout=True)
        for eje, grupo, color in zip(ejes, ["15–28", "29–54", "55 o más"],
                                    ["#176B87", "#D77A36", "#548765"]):
            g = mi.loc[mi["Grupo_Edad"].eq(grupo)]
            eje.set_title(f"{grupo} años (n={len(g)})")
            eje.set_xlabel("Ingreso laboral (millones de COP)")
            eje.set_xticks(np.linspace(0, limite, 6))
            eje.ticklabel_format(axis="x", style="plain", useOffset=False)
            if not g.empty:
                eje.hist(g["Ingreso_Millones"], bins=intervalos,
                         weights=100 * g["Peso"] / g["Peso"].sum(),
                         color=color, edgecolor="white", linewidth=1)
            else:
                eje.text(0.5, 0.5, "Sin datos válidos", ha="center",
                         va="center", transform=eje.transAxes)
            eje.set_xlim(0, limite)
            eje.grid(axis="x", visible=False)
        ejes[0].set_ylabel("Porcentaje ponderado del grupo de edad")
        fig.suptitle("Distribución del ingreso por edad en manufactura\n"
                     "Cali A.M. · Octubre–diciembre de 2025")
        fig.supxlabel("Cada barra muestra qué porcentaje del grupo está en ese intervalo de ingreso.\n"
                      "Ponderación: FEX_C18 · n: registros con ingreso y peso válidos", fontsize=10)
        figuras.append(("Distribución del ingreso por grupo de edad", fig))
    # La salida queda disponible antes de cerrar las figuras; no se imprime en consola.
    carpeta = Path(carpeta_salida) if carpeta_salida else Path(__file__).resolve().parent / "resultados_aed"
    ruta = presentar_resultados(tablas, figuras, carpeta)
    d.attrs["informe_html"] = str(ruta)
    for _, fig in figuras:
        plt.close(fig)
    if abrir_informe:
        webbrowser.open(ruta.as_uri())
    return d, tablas


def guardar_tabla_png(t, titulo, ruta):
    """Dibuja una tabla con título, unidades y filas ajustadas al texto."""
    datos = t.reset_index() if not isinstance(t.index, pd.RangeIndex) else t.copy()
    datos.columns = ["Estadístico o categoría" if str(c) == "index" else str(c).replace("_", " ")
                     for c in datos.columns]

    def formato(x):
        if pd.isna(x):
            return "—"
        if isinstance(x, (float, np.floating)):
            return f"{x:,.2f}".translate(str.maketrans(",.", ".,"))
        return str(x)

    filas = [list(datos.columns)] + [[formato(x) for x in fila]
                                    for fila in datos.itertuples(index=False, name=None)]
    # Anchos y altos adaptados: los encabezados largos no se cortan.
    largos = np.array([min(38, max(18, max(len(f[c]) for f in filas)))
                       for c in range(len(datos.columns))], dtype=float)
    anchos = largos / largos.sum()
    filas = [[fill(x, width=max(10, int(ancho * 110))) for x, ancho in zip(f, anchos)]
             for f in filas]
    altos = [0.22 * max(x.count("\n") + 1 for x in f) + 0.16 for f in filas]
    titulo = fill(titulo.replace("_", " "), width=95)
    margen_titulo = 0.34 * (titulo.count("\n") + 1) + 0.2
    alto = sum(altos) + margen_titulo + 0.8
    fig = plt.figure(figsize=(10.5, alto), facecolor="white")
    ax = fig.add_axes([0.03, 0.7 / alto, 0.94, sum(altos) / alto])
    ax.axis("off")
    tabla = ax.table(cellText=filas, colWidths=anchos, cellLoc="right", bbox=[0, 0, 1, 1])
    tabla.auto_set_font_size(False)
    tabla.set_fontsize(10.5)
    for (r, c), celda in tabla.get_celld().items():
        celda.set_height(altos[r] / sum(altos))
        celda.set_edgecolor("#D9DFE3")
        celda.set_linewidth(0.6)
        celda.set_facecolor("#E6F0F4" if r == 0 else ("#F6F8FA" if r % 2 == 0 else "white"))
        if r == 0:
            celda.set_text_props(weight="bold", ha="center")
        elif c == 0:
            celda.set_text_props(ha="left")
    fig.text(0.03, 1 - 0.15 / alto, titulo, va="top", fontsize=12, weight="bold")
    fig.text(0.03, 0.4 / alto, "Cali A.M. · Octubre–diciembre de 2025 · Fuente: GEIH del DANE", fontsize=9)
    fig.text(0.03, 0.16 / alto, "—: no disponible. Las medidas ponderadas se identifican en los títulos y encabezados.", fontsize=9)
    fig.savefig(ruta, dpi=300, facecolor="white")
    plt.close(fig)


def presentar_resultados(tablas, figuras, carpeta):
    """Genera tablas copiables y gráficos descargables en una sola vista local."""
    carpeta = Path(carpeta).resolve()
    carpeta.mkdir(parents=True, exist_ok=True)
    etiquetas = {"n": "n válido", "n_pond": "n con peso válido", "Media": "Media muestral",
                 "Mediana": "Mediana muestral", "DE": "Desviación estándar",
                 "Min": "Mínimo", "Max": "Máximo", "P25": "Percentil 25",
                 "P75": "Percentil 75", "Asimetria": "Asimetría", "Media_pond": "Media ponderada"}
    unidades = {"Edad": "Edad en años", "Ingreso_Laboral": "Ingreso laboral en COP",
                "Horas_Trabajo_Semanales": "Horas de trabajo semanales"}

    contador_png = 0

    def tabla_html(t, titulo):
        nonlocal contador_png
        # Se mantienen todos los datos; solo se redondea su presentación.
        t = t.copy()
        mostrar_indice = not isinstance(t.index, pd.RangeIndex)
        conteos = t.index.intersection(["n válido", "n con peso válido", "Faltantes"])
        if len(conteos):
            t = t.astype(object)
            for fila in conteos:
                t.loc[fila] = t.loc[fila].map(lambda x: f"{int(x):,}".replace(",", "."))
        if mostrar_indice:
            t.index = t.index.map(lambda x: str(x).replace("_", " "))
        contenido = '<div class="tabla">' + t.to_html(
            border=0, na_rep="—", escape=True, index=mostrar_indice,
            float_format=lambda x: f"{x:,.2f}".translate(str.maketrans(",.", ".,"))) + '</div>'
        # Las tablas extensas se guardan por partes con todos sus encabezados.
        partes = (len(t) + 19) // 20
        for parte, inicio in enumerate(range(0, len(t), 20), 1):
            contador_png += 1
            nombre = f"tabla_{contador_png:02d}.png"
            sufijo = f" (parte {parte} de {partes})" if partes > 1 else ""
            guardar_tabla_png(t.iloc[inicio:inicio + 20], titulo + sufijo, carpeta / nombre)
            imagen = base64.b64encode((carpeta / nombre).read_bytes()).decode("ascii")
            contenido += (f'<p><a class="boton" download="{nombre}" href="data:image/png;base64,{imagen}">'
                          f'Guardar tabla PNG{sufijo}</a></p><details><summary>Ver tabla como imagen{sufijo}</summary>'
                          f'<img src="data:image/png;base64,{imagen}" alt="{escape(titulo + sufijo)}"></details>')
        return contenido

    bloques, indice = [], []
    for numero, (titulo, original) in enumerate(tablas.items(), 1):
        indice.append(f'<li><a href="#tabla{numero}">{escape(titulo)}</a></li>')
        bloque = [f'<section id="tabla{numero}"><h2>Tabla {numero}. {escape(titulo)}</h2>']
        t = original.to_frame(name=original.name or "Valor") if isinstance(original, pd.Series) else original
        if t.empty:
            bloque.append('<p>Sin registros disponibles para esta tabla.</p>')
        elif "Variable" in t.columns:
            # Estadísticos en filas y grupos en columnas: evita tablas demasiado anchas.
            campos = [c for c in t.columns if c not in etiquetas and c not in ["Variable", "Faltantes"]]
            for variable, g in t.groupby("Variable", sort=False):
                matriz = g.drop(columns="Variable").set_index(campos).T.rename(index=etiquetas)
                matriz.columns = [" / ".join(map(str, c)) if isinstance(c, tuple) else str(c)
                                  for c in matriz.columns]
                for inicio in range(0, len(matriz.columns), 4):
                    bloque.append(f'<h3>{escape(unidades.get(variable, variable))}</h3>')
                    bloque.append(tabla_html(matriz.iloc[:, inicio:inicio + 4],
                                  f"Tabla {numero}. {titulo} — {unidades.get(variable, variable)}"))
        else:
            # Los índices de varios niveles se convierten en columnas legibles.
            if isinstance(t.index, pd.MultiIndex):
                t = t.reset_index()
            t.columns = [str(c).replace("_", " ") for c in t.columns]
            bloque.append(tabla_html(t, f"Tabla {numero}. {titulo}"))
        bloques.append("".join(bloque) + '</section>')

    for numero, (titulo, fig) in enumerate(figuras, 1):
        nombre = f"grafico_{numero:02d}.png"
        fig.savefig(carpeta / nombre, dpi=300, bbox_inches="tight", facecolor="white")
        # Imagen incrustada: la vista HTML también funciona al copiarla a otra carpeta.
        imagen = base64.b64encode((carpeta / nombre).read_bytes()).decode("ascii")
        indice.append(f'<li><a href="#figura{numero}">{escape(titulo)}</a></li>')
        bloques.append(f'<section id="figura{numero}"><h2>Figura {numero}. {escape(titulo)}</h2>'
                       f'<img src="data:image/png;base64,{imagen}" alt="{escape(titulo)}">'
                       f'<p><a download="{nombre}" href="data:image/png;base64,{imagen}">'
                       'Guardar imagen PNG</a></p></section>')

    cabecera = '''<!doctype html><html lang="es"><meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Análisis exploratorio GEIH 2025</title><style>
    body{font:16px/1.5 Arial,sans-serif;color:#202a32;background:#fff;max-width:1200px;margin:36px auto;padding:0 24px}
    h1,h2,h3{line-height:1.25}h1{font-size:28px}h2{font-size:21px;margin-top:36px}h3{font-size:17px}
    section{border-top:1px solid #ccd5db;padding-top:8px;margin:32px 0}a{color:#176b87}
    .tabla{overflow-x:auto;margin:16px 0 28px}table{border-collapse:collapse;width:100%;font-size:14px}
    th,td{border:1px solid #d9dfe3;padding:9px 12px;text-align:right;vertical-align:middle}
    thead th{background:#e6f0f4;color:#152a36}tbody th{text-align:left;font-weight:normal}
    tbody tr:nth-child(even){background:#f6f8fa}img{display:block;width:100%;height:auto}
    nav{columns:2;column-gap:40px}nav li{break-inside:avoid;margin:4px 0}
    .boton{display:inline-block;background:#176b87;color:white;padding:9px 14px;border-radius:4px;text-decoration:none}
    details{margin-bottom:24px}summary{cursor:pointer;color:#176b87}
    @media(max-width:700px){nav{columns:1}body{padding:0 12px}}
    @media print{nav{display:none}section{border:0}.tabla{overflow:visible}thead{display:table-header-group}
    tr,img{break-inside:avoid}body{max-width:none;margin:0}a[download]{display:none}}
    </style><body><h1>Análisis exploratorio del empleo manufacturero</h1>
    <p>Cali A.M. (Cali y Yumbo) · Octubre a diciembre de 2025 · Microdatos públicos de la GEIH.</p>
    <p>Las tablas describen edades, ingresos, horas trabajadas y composición de los grupos.
    La base incluye ocupados de 15 años o más; manufactura corresponde a las divisiones 10 a 33.
    Asalariados: categorías 1, 2, 3 y 7; cuenta propia: categoría 4. Otras posiciones permanecen identificadas.</p>
    <p><strong>Lectura estadística.</strong> n es el número de registros con valor válido para cada variable.
    Media, mediana, desviación estándar (divisor n − 1), percentiles y asimetría son muestrales, sin ponderar.
    La media ponderada, las composiciones porcentuales y los histogramas utilizan FEX_C18 positivo;
    n con peso válido indica el número de registros que aporta a esa media ponderada.</p>
    <p>Los porcentajes etarios suman 100 % dentro de cada sector o combinación de sector y posición.
    En cada histograma, los porcentajes suman 100 % dentro del grupo con variable y peso válidos.
    Los faltantes no se imputan; los ingresos cero y extremos se conservan.
    Los extremos se señalan fuera de [P25 − 1,5 RIC; P75 + 1,5 RIC], donde RIC = P75 − P25.
    El símbolo — indica que el estadístico no está disponible. Las medidas se muestran con dos decimales;
    los conteos, como enteros.</p>
    <p>Los conteos corresponden a registros mensuales apilados, no a personas únicas del trimestre.
    Estos resultados son descriptivos; no incluyen intervalos de confianza ni pruebas de hipótesis.</p>
    <p>Fuente: elaboración a partir de <a href="https://microdatos.dane.gov.co/index.php/catalog/853">GEIH 2025 del DANE</a>.
    Cada tabla dispone de un botón Guardar tabla PNG y una vista como imagen.
    Las tablas y figuras se guardan en PNG a 300 ppp; las tablas extensas se dividen por partes.</p>
    '''
    ruta = carpeta / "informe_exploratorio_geih.html"
    ruta.write_text(cabecera + '<nav><ol>' + "".join(indice) + '</ol></nav>'
                    + "".join(bloques) + '</body></html>', encoding="utf-8")
    return ruta
