#------------------
#Librerias
#------------------
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yaml

import src.extract.extract_csv as extract_csv
import src.transform.clean_csv as transform_csv
#------------------
#Extraccion
#------------------
def main():

    #configuracion del archivo yaml
    with open("config/config.yaml", "r") as file:
        config = yaml.safe_load(file)

    rutas_carac_generales = [
        f"{config['paths']['bronze_dir']}/{config['source']['caracteristicas_generales_dic']}",
        f"{config['paths']['bronze_dir']}/{config['source']['caracteristicas_generales_nov']}",
        f"{config['paths']['bronze_dir']}/{config['source']['caracteristicas_generales_oct']}"
        ]
   
    df_caracteristicas_generales_listas  = extract_csv.extract_csv(rutas_carac_generales)
    df_caracteristicas_generales = extract_csv.merge_csv(df_caracteristicas_generales_listas)
    print("Imprimindo dataframe final caracteristicas generales")
    print(df_caracteristicas_generales)
    df_caracteristicas_generales_copia = df_caracteristicas_generales.copy()
    print("caracteristicas generales copia")
    print(df_caracteristicas_generales_copia)
    #Excel usado para analisis exploratorio sin renombrar columnas
    df_caracteristicas_generales_copia.to_csv(f"{config['paths']['bronze_dir']}/{config['source']['csv_salida_cg_sinrenombrar']}")
    #Excel usado para analisis exploratorio
    df_caracteristicas_generales_renombrado = extract_csv.rename_columns(df_caracteristicas_generales)
    df_caracteristicas_generales_renombrado.to_csv(f"{config['paths']['bronze_dir']}/{config['source']['csv_salida_cg']}")

    rutas_ocupados = [
        f"{config['paths']['bronze_dir']}/{config['source']['ocupados_dic']}",
        f"{config['paths']['bronze_dir']}/{config['source']['ocupados_nov']}",
        f"{config['paths']['bronze_dir']}/{config['source']['ocupados_oct']}"
        ]

    df_ocupados_listas = extract_csv.extract_csv(rutas_ocupados)
    df_ocupados = extract_csv.merge_csv(df_ocupados_listas)
    print("Imprimindo df_ocupados")
    print(df_ocupados)
    df_ocupados_copia = df_ocupados.copy()
    print("Ocupados copia")
    print(df_ocupados_copia)
    #Excel usado para analisis exploratorio sin renombrar columnas
    df_ocupados_copia.to_csv(f"{config['paths']['bronze_dir']}/{config['source']['csv_salida_ocupados_sinrenombrar']}")
    #usado para analisis exploratorio
    df_ocupados_renombrado = extract_csv.rename_columns(df_ocupados)
    df_ocupados_renombrado.to_csv(f"{config['paths']['bronze_dir']}/{config['source']['csv_salida_ocupados']}")

    #------------------
    #Transformacion
    #------------------
    df_transformacion_cg = transform_csv.clean(df_caracteristicas_generales_copia,"df_caracteristicas_generales_copia")
    df_transformacion_ocupados = transform_csv.clean(df_ocupados_copia, "df_ocupados_copia")
    print("Columnas eliminadas/renombradas de cg")
    print(df_transformacion_cg)
    print("Columnas eliminadas/renombradas de ocupados")
    print(df_transformacion_ocupados)
    df_transformacion_cg.to_csv(f"{config['paths']['silver_dir']}/{config['source']['csv_salida_cg_transformado']}")
    df_transformacion_ocupados.to_csv(f"{config['paths']['silver_dir']}/{config['source']['csv_salida_ocupados_transformado']}")
    
    #union de datasets
    lista_df = [df_transformacion_cg, df_transformacion_ocupados]
    claves_de_union = ["Anio_Encuesta", "Mes_Encuesta", "Id_Vivienda", "Id_Hogar", "Orden_Persona",]
    df_cg_ocupados = transform_csv.join_datasets(lista_df,claves_de_union)
    print("Dataset unido")
    print(df_cg_ocupados)
    df_cg_ocupados.to_csv(f"{config['paths']['silver_dir']}/{config['source']['csv_salida_datasets_unidos']}")
   
    #traduccion de valores de columnas
    df_traducido = transform_csv.traslation_values(df_cg_ocupados)
    print("dataset traducido")
    print(df_traducido)
    df_traducido.to_excel(f"{config['paths']['silver_dir']}/{config['source']['excel_salida_datasets_traducido']}",index=False)

    #Limpiza de valores de las columnas
    df_traducido_clean = transform_csv.clean_values(df_traducido)
    print("limpieza de valores")
    print(df_traducido_clean)
    df_traducido_clean.to_excel(f"{config['paths']['silver_dir']}/{config['source']['excel_salida_datasets_traducido_clean']}",index=False)
    
if __name__ == "__main__":
    main()
