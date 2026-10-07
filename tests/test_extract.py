
import pandas as pd
import yaml
import src.extract.extract_csv as extract_csv
import src.transform.clean_csv as transform_csv

with open("config/config.yaml", "r") as file:
        config = yaml.safe_load(file)

rutas_carac_generales = [
    f"{config['paths']['bronze_dir']}/{config['source']['caracteristicas_generales_dic']}",
    f"{config['paths']['bronze_dir']}/{config['source']['caracteristicas_generales_nov']}",
    f"{config['paths']['bronze_dir']}/{config['source']['caracteristicas_generales_oct']}"
    ]
   
df_caracteristicas_generales_listas  = extract_csv.extract_csv(rutas_carac_generales)
df_caracteristicas_generales = extract_csv.merge_csv(df_caracteristicas_generales_listas)
df_caracteristicas_generales_copia = df_caracteristicas_generales.copy() #Saco una copia para trabajar con ella en la transformacion y no dañar el dataframe final

rutas_ocupados = [
    f"{config['paths']['bronze_dir']}/{config['source']['ocupados_dic']}",
    f"{config['paths']['bronze_dir']}/{config['source']['ocupados_nov']}",
    f"{config['paths']['bronze_dir']}/{config['source']['ocupados_oct']}"
    ]

df_ocupados_listas = extract_csv.extract_csv(rutas_ocupados)
df_ocupados = extract_csv.merge_csv(df_ocupados_listas)
df_ocupados_copia = df_ocupados.copy() #Saco una copia para trabajar con ella en la transformacion y no dañar el dataframe final

#------------------
#Validacion de que no hay duplicados en los datasets antes y despues de eliminar los duplicados
#------------------

def test_keys_duplicates():
    #Se comparan los datasets antes y despues de hacer limpieza de diplucados y renombrar las columnas
    df_transformacion_cg = transform_csv.clean(df_caracteristicas_generales_copia,"df_caracteristicas_generales_copia")
    df_transformacion_ocupados = transform_csv.clean(df_ocupados_copia, "df_ocupados_copia")

    assert len(df_caracteristicas_generales_copia) == len(df_transformacion_cg)
    assert len(df_ocupados_copia) == len(df_transformacion_ocupados)