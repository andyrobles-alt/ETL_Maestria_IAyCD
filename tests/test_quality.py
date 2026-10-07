import pandas as pd
import yaml
import src.extract.extract_csv as extract_csv
import src.transform.clean_csv as transform_csv
from pandas.api.types import is_numeric_dtype
with open("config/config.yaml", "r") as file:
        config = yaml.safe_load(file)


#------------------
#Validacion de que los ingresos son numericos; los nulos del origen se conservan.
#------------------

def test_numeric_salary():

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

    df_transformacion_cg = transform_csv.clean(df_caracteristicas_generales_copia,"df_caracteristicas_generales_copia")
    df_transformacion_ocupados = transform_csv.clean(df_ocupados_copia, "df_ocupados_copia")

    #union de datasets
    lista_df = [df_transformacion_cg, df_transformacion_ocupados]
    claves_de_union = ["Anio_Encuesta", "Mes_Encuesta", "Id_Vivienda", "Id_Hogar", "Orden_Persona",]
    df_cg_ocupados = transform_csv.join_datasets(lista_df,claves_de_union)

    #traduccion de valores de columnas
    df_traducido = transform_csv.traslation_values(df_cg_ocupados)

    #Limpiza de valores de las columnas: se quitan nulos, se arreglan formatos
    df_traducido_clean = transform_csv.clean_values(df_traducido)

    assert is_numeric_dtype(df_traducido_clean['Ingreso_Laboral']),("Error: La columna 'Ingreso_Laboral' contiene valores no numéricos.")
