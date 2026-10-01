import pandas as pd
from .renombrar_columnas_geih import renombrar_columnas_geih

#Extraer CSV en un dataframe
def extract_csv(ruta: list[str]) -> pd.DataFrame: #anotadores
    print("extract_csv: Recorriendo listas de csv")
    data = [pd.read_csv(r, encoding="latin-1", sep=";",low_memory=False) for r in ruta]
    return data

#Unir CSVs
def merge_csv(ruta: str) -> pd.DataFrame:
    print("extract_csv: Uniendo CSVs")
    df_final = pd.concat(ruta)
    return df_final

#Renombrar columnas de los CSVs
def  rename_columns (ruta: str) -> pd.DataFrame:
    print("extract_csv: Renombrar columnas")
    df_data = renombrar_columnas_geih(ruta)
    return df_data