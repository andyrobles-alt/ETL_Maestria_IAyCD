import pandas as pd
from .renombrar_columnas_geih import renombrar_columnas_geih
from .diccionarios_geih import traducir_geih
#Dejamos solo columnas necesarias
def clean(df: pd.DataFrame, nombre_df: str)->pd.DataFrame:
    #Se eliminan columnas
    columnas_interes_cg = [    'PERIODO', 'MES', 'PER', 'DIRECTORIO', 'SECUENCIA_P','ORDEN', 'HOGAR', 'AREA', 'FEX_C18', 'DPTO',
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
    print("Renombrar columnas")
    # Se renombran las columnas
    df_data = renombrar_columnas_geih(data)
    #Eliminar duplicados
    df_data.dropna()
    return df_data

def join_datasets(dfs: list[pd.DataFrame], claves: list[str]) -> pd.DataFrame:
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
    df_traducido,reporte = traducir_geih(df)
    return df_traducido

def clean_values(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    data["Ingreso_Laboral"] = (data["Ingreso_Laboral"].replace(r"^\s*$", pd.NA, regex=True).fillna("NA"))
    data['Edad'] = data['Edad'].astype(object).fillna('Na')

    niveles_sin_diploma = ['Ninguno', 'Básica primaria (1o - 5o)', 'Básica secundaria (6o - 9o)']
    data.loc[
    data['Titulo_o_Diploma'].isna() & data['Nivel_Educativo'].isin(niveles_sin_diploma),
    'Titulo_o_Diploma'
    ] = 'sin diploma'

    data['Poblacion_Mayor_18'] = data['Poblacion_Mayor_18'].astype(object).fillna('Na')
    data['Area_Metropolitana'] = data['Area_Metropolitana'].fillna('otros')

    return data
