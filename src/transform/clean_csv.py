import pandas as pd
from .renombrar_columnas_geih import renombrar_columnas_geih
from .diccionarios_geih import DICCIONARIOS, traducir_geih
#Dejamos solo columnas necesarias
def clean(df: pd.DataFrame, nombre_df: str)->pd.DataFrame:
    #Se eliminan columnas y se dejan solo las de interes, estas columnas se dedicidio dejarlar despues del EDA
    columnas_interes_cg = [    
    'PERIODO', 'MES', 'PER', 'DIRECTORIO', 'SECUENCIA_P',
    'ORDEN', 'HOGAR', 'AREA', 'FEX_C18', 'DPTO',
    'P3271', 'P6040', 'P6120', 'P3042', 'P3043',
    'P3043S1', 'POB_MAY18'
    ]
    columnas_interes_ocupados = [
    'PERIODO', 'MES', 'PER', 'DIRECTORIO', 'SECUENCIA_P',
    'ORDEN', 'HOGAR', 'AREA', 'FEX_C18', 'DPTO',
    'P6430', 'P6800', 'INGLABO', 'RAMA2D_R4'
    ]
    if nombre_df == 'df_caracteristicas_generales_copia':
        data = df[columnas_interes_cg]
        
    elif nombre_df == 'df_ocupados_copia':
        data = df[columnas_interes_ocupados]
    else:
        raise ValueError(f"Nombre de DataFrame no reconocido: {nombre_df}")
    print("clean_csv: Renombrar columnas")
    # Se renombran las columnas
    df_data = renombrar_columnas_geih(data)
    #Eliminar duplicados
    df_data.drop_duplicates(subset=["Anio_Encuesta", "Mes_Encuesta", "Id_Vivienda", "Id_Hogar", "Orden_Persona"], keep = 'first', inplace=True, ignore_index = True)
    return df_data

def join_datasets(dfs: list[pd.DataFrame], claves: list[str]) -> pd.DataFrame:
    print("join_datasets: Uniendo datasets")
    if not dfs:
        raise ValueError("Se necesita al menos un DataFrame para unir.")
    resultado = dfs[0].copy()

    for df in dfs[1:]:
        for nombre, tabla in (("resultado", resultado), ("siguiente DataFrame", df)):
            faltantes = [clave for clave in claves if clave not in tabla.columns]
            if faltantes:
                raise ValueError(f"Faltan claves en {nombre}: {faltantes}")
            if tabla[claves].isna().any().any():
                raise ValueError(f"Hay claves de union vacias en {nombre}.")

        columnas_nuevas = [
            columna for columna in df.columns if columna in claves or columna not in resultado.columns
        ]
        resultado = resultado.merge(
            df[columnas_nuevas],
            on=claves,
            how="right",
            validate="one_to_one",
            indicator=True,
        )
        sin_coincidencia = resultado["_merge"].ne("both").sum()
        if sin_coincidencia:
            raise ValueError(
                f"Hay {sin_coincidencia} filas sin coincidencia en el DataFrame anterior."
            )
        resultado = resultado.drop(columns="_merge")
    return resultado
#Se reemplazan los valores por los valores de los diccionarios creados
def traslation_values(df: pd.DataFrame) -> pd.DataFrame:
    print("traslation_values: Renombrar valores de las columnas")
    df_traducido,reporte = traducir_geih(df)
    return df_traducido
#Limpieza del dataset final
def clean_values(df: pd.DataFrame) -> pd.DataFrame:
    print("clean_values: Limpieza del dataset final")
    data = df.copy()
    data['Ingreso_Laboral'] = pd.to_numeric(data['Ingreso_Laboral'],errors='coerce')
    data['Edad'] = pd.to_numeric(data['Edad'],errors='coerce')

    niveles_sin_diploma = ['Ninguno', 'Básica primaria (1o - 5o)', 'Básica secundaria (6o - 9o)', 'Preescolar']
    data.loc[
    data['Titulo_o_Diploma'].isna() & data['Nivel_Educativo'].isin(niveles_sin_diploma),
    'Titulo_o_Diploma'
    ] = 'sin diploma'

    data['Poblacion_Mayor_18'] = data['Poblacion_Mayor_18'].fillna(0)
    data['Area_Metropolitana'] = data['Area_Metropolitana'].astype("string").fillna('otros')
    data['Departamento'] = data['Departamento'].astype('string')
    data['Sexo_Al_Nacer'] = data['Sexo_Al_Nacer'].astype('string')
    data['Nivel_Educativo'] = data['Nivel_Educativo'].astype('string')
    data['Titulo_o_Diploma'] = data['Titulo_o_Diploma'].astype('string')
    data['Categoria_Trabajo'] = data['Categoria_Trabajo'].astype('string')
    data = data.drop(columns=["Titulo_Diploma_EnQue"])
    data = data.drop(columns=["Pago_Mensual_Salud"])

    ramas_validas = set(DICCIONARIOS["RAMA2D_R4"].values())
    data["Rama_Act_Empleo_Ppal"] = (
        data["Rama_Act_Empleo_Ppal"]
        .astype("string")
        .where(lambda rama: rama.isin(ramas_validas), "otras ramas")
    )
    return data

def respuestas_OKRs_KPIs(df_caracteristicas_generales_copia,df_ocupados_copia,df_traducido_clean):
    print("respuestas_OKRs_KPIs: revision de cardinalidad")
    print("**********Info de cg**********")
    print(df_caracteristicas_generales_copia.info())
    print(df_caracteristicas_generales_copia.isnull().sum())
    print("**********Info de ocupados**********")
    print(df_ocupados_copia.info())
    print(df_ocupados_copia.isnull().sum())
    print("**********Info de dataset final**********")
    print(df_traducido_clean.info())
    print(df_traducido_clean.isnull().sum())

    claves_de_union = ['PER', 'MES', 'DIRECTORIO', 'SECUENCIA_P', 'ORDEN']
    print("**********Buscar claves duplicadas en los módulos originales**********")
    print(df_caracteristicas_generales_copia.duplicated(claves_de_union).sum(), df_ocupados_copia.duplicated(claves_de_union).sum())
    print("**********Comprobar que cada ocupado tenga pareja en Características generales**********")
    union = df_ocupados_copia[claves_de_union].merge(df_caracteristicas_generales_copia[claves_de_union], on=claves_de_union, how='left', validate='one_to_one', indicator=True)
    print(union['_merge'].value_counts())
    print("**********Preparar las claves del DataFrame final para compararlas**********")
    final_claves = df_traducido_clean.rename(columns={'Anio_Encuesta': 'PER', 'Mes_Encuesta': 'MES', 'Id_Vivienda': 'DIRECTORIO', 'Id_Hogar': 'SECUENCIA_P', 'Orden_Persona': 'ORDEN'})
    print("**********Verificar que Ocupados y el final tengan exactamente las mismas personas-mes**********")
    comparacion = df_ocupados_copia[claves_de_union].merge(final_claves[claves_de_union], on=claves_de_union, how='outer', validate='one_to_one', indicator=True)
    print(comparacion['_merge'].value_counts())

def previsualizar_kpis(
    df_KPIs: pd.DataFrame,
    ruta_salida: str = "data/gold/previsualizacion_KPIs.xlsx"
) -> str:
    import matplotlib.pyplot as plt
    from openpyxl.drawing.image import Image
    from pathlib import Path
    from io import BytesIO

    print("previsualizar_kpis: Generando reporte Excel")

    # Copia para preparar las etiquetas sin modificar los datos originales
    data = df_KPIs.copy()
    data['Grupo'] = (
        data['Rama_Act_Empleo_Ppal']
        .fillna('Sin rama')
        .replace({'otras ramas': 'Otros sectores'})
        .astype(str)
        + '\n'
        + data['Categoria_Trabajo']
        .fillna('Sin categoría')
        .replace({'Trabajador por cuenta propia': 'Cuenta propia'})
        .astype(str)
    )

    # Columna, hoja, título, unidad, cálculo y explicación
    indicadores = [
        (
            'Proporcion_55+', 'Proporcion_55',
            'Peso de los trabajadores de 55 años o más',
            'Porcentaje del grupo',
            'Cálculo: Σ FEX (55+) / Σ FEX (grupo) × 100',
            'Cada barra indica qué porcentaje del grupo tiene 55 años o más.'
        ),
        (
            'Razon_Reemplazo', 'Razon_Reemplazo',
            'Jóvenes por cada trabajador de 55 años o más',
            'Jóvenes de 18–34 por trabajador de 55+',
            'Cálculo: Σ FEX (18–34) / Σ FEX (55+)',
            'La línea roja en 1 indica igual peso de jóvenes y trabajadores de 55+.'
        ),
        (
            'Edad_Mediana', 'Edad_Mediana',
            'Edad central de cada grupo',
            'Edad mediana ponderada (años)',
            'Cálculo: primera edad cuyo FEX acumulado alcanza el 50 % del grupo',
            'La mediana resume la edad central teniendo en cuenta los factores de expansión.'
        )
    ]

    ruta = Path(ruta_salida)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    imagenes = []

    with pd.ExcelWriter(ruta, engine='openpyxl') as writer:
        # Conservar todas las filas y columnas originales
        df_KPIs.to_excel(writer, sheet_name='Datos_KPI', index=False)

        for columna, hoja_nombre, titulo, unidad, calculo, lectura in indicadores:
            data[columna] = (
                pd.to_numeric(data[columna], errors='coerce')
                .replace([float('inf'), -float('inf')], float('nan'))
            )
            validos = data.dropna(subset=[columna]).sort_values(columna)

            hoja = writer.book.create_sheet(hoja_nombre)
            hoja['A1'] = titulo
            hoja['A2'] = calculo
            hoja['A3'] = lectura

            if validos.empty:
                hoja['A5'] = 'No hay valores válidos para graficar este indicador.'
                continue

            fig, ax = plt.subplots(figsize=(12, 6))
            barras = ax.barh(
                validos['Grupo'], validos[columna],
                color='#2878B5', height=0.55
            )

            # Los valores incluyen la unidad para facilitar su lectura
            if columna == 'Proporcion_55+':
                etiquetas = [f'{valor:.1f}%' for valor in validos[columna]]
                ax.set_xlim(0, 100)
            elif columna == 'Edad_Mediana':
                etiquetas = [f'{valor:.1f} años' for valor in validos[columna]]
                ax.set_xlim(0, validos[columna].max() * 1.3 + 1)
            else:
                etiquetas = [f'{valor:.2f}' for valor in validos[columna]]
                ax.set_xlim(0, max(1.3, validos[columna].max() * 1.3))
                ax.axvline(1, color='#C44E52', linestyle='--', linewidth=2)

            ax.bar_label(barras, labels=etiquetas, padding=5, fontsize=11)
            ax.set_xlabel(unidad)
            ax.set_ylabel('Sector y categoría laboral')
            ax.set_title(
                'Cali A.M. · Octubre–diciembre de 2025\n'
                f'{len(validos)} de {len(data)} grupos con valores válidos',
                fontsize=10
            )
            ax.grid(axis='x', alpha=0.2)
            ax.set_axisbelow(True)

            fig.suptitle(titulo, fontsize=15, fontweight='bold')
            fig.text(
                0.02, 0.02,
                f'{lectura}\n{calculo}\n'
                'FEX: factor de expansión. Grupos según la clasificación actual de Gold.',
                fontsize=9
            )
            fig.tight_layout(rect=[0, 0.15, 1, 0.93])

            # Insertar el gráfico directamente en el Excel
            imagen = BytesIO()
            fig.savefig(imagen, format='png', dpi=120)
            plt.close(fig)
            imagen.seek(0)
            imagenes.append(imagen)

            hoja.add_image(Image(imagen), 'A5')
            hoja.sheet_view.showGridLines = False

    for imagen in imagenes:
        imagen.close()

    print(f'previsualizar_kpis: Reporte guardado en {ruta}')
    return str(ruta)