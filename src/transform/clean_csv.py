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
    print("clean_csv: Eliminar duplicados")
    df_data.dropna()
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


def traslation_values(df: pd.DataFrame) -> pd.DataFrame:
    print("traslation_values: Renombrar valores de las columnas")
    df_traducido,reporte = traducir_geih(df)
    return df_traducido

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