import pandas as pd

def extract_csv(ruta:str) -> pd.DataFrame: #anotadores
    data = pd.read_csv(ruta)
    return data