#------------------
#Librerias
#------------------
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yaml
import datetime as dt

import src.extract.extract_csv as extract_csv
import src.transform.clean_csv as transform_csv
import src.transform.gold_transformations as gold_transformations
import src.load.load_database as load_database

def main():

    #configuracion del archivo yaml
    with open("config/config.yaml", "r") as file:
        config = yaml.safe_load(file)
    #------------------
    #Extraccion
    #------------------
    with open(f"{config['paths']['logs']}/{config['source']['logs_file']}", "a",encoding='utf-8') as log_file:
        log_file.write(f"{dt.datetime.now()} INFO: Extracción de datos iniciada\n ")
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

    with open(f"{config['paths']['logs']}/{config['source']['logs_file']}", "a",encoding='utf-8') as log_file:
        log_file.write(f"{dt.datetime.now()} INFO: Extracción de datos completada\n ")
    
    #------------------
    #Transformacion
    #------------------
    with open(f"{config['paths']['logs']}/{config['source']['logs_file']}", "a",encoding='utf-8') as log_file:
        log_file.write(f"{dt.datetime.now()} INFO: Transformación de datos iniciada\n ")
    #Se dejan las columnas necesarias y se renombra
    df_transformacion_cg = transform_csv.clean(df_caracteristicas_generales_copia,"df_caracteristicas_generales_copia")
    df_transformacion_ocupados = transform_csv.clean(df_ocupados_copia, "df_ocupados_copia")
    #Se almacenan en archivos CSV
    df_transformacion_cg.to_csv(f"{config['paths']['silver_dir']}/{config['source']['csv_salida_cg_transformado']}")
    df_transformacion_ocupados.to_csv(f"{config['paths']['silver_dir']}/{config['source']['csv_salida_ocupados_transformado']}")
    
    #union de datasets
    lista_df = [df_transformacion_cg, df_transformacion_ocupados]
    claves_de_union = ["Anio_Encuesta", "Mes_Encuesta", "Id_Vivienda", "Id_Hogar", "Orden_Persona",]
    df_cg_ocupados = transform_csv.join_datasets(lista_df,claves_de_union)
    
    #traduccion de valores de columnas
    df_traducido = transform_csv.traslation_values(df_cg_ocupados)
    
    #Limpiza de valores de las columnas: se quitan nulos, se arreglan formatos
    df_traducido_clean = transform_csv.clean_values(df_traducido)
     #Se almacenan en archivos excel: limpieza del dataset unido
    df_traducido_clean.to_excel(f"{config['paths']['silver_dir']}/{config['source']['excel_salida_datasets_traducido_clean']}",index=False)

    #Analisis de cardinalidad - Activarlo para hacer un EDA rapido en consola
    #transform_csv.respuestas_OKRs_KPIs(df_caracteristicas_generales_copia,df_ocupados_copia,df_traducido_clean)
    
    

    #--------------------
    #TRANSFORMACION DE DATOS PARA GOLD
    #--------------------
    df_gold_data_Cali = gold_transformations.table_metropolitan_area(df_traducido_clean)
    df_gold_data_Cali.to_excel(f"{config['paths']['gold_dir']}/{config['source']['excel_salida_gold_data_Cali']}")
    df_kpis = gold_transformations.table_KPIs(df_gold_data_Cali)
    df_kpis.to_excel(f"{config['paths']['gold_dir']}/{config['source']['excel_salida_gold_data_KPIs']}")
    
    # Leer la tabla de KPI exportada
    ruta_kpis = (f"{config['paths']['gold_dir']}/{config['source']['excel_salida_gold_data_KPIs']}")
    df_KPIs_previsualizacion = pd.read_excel(ruta_kpis)
    
    # Generar el Excel de previsualización
    transform_csv.previsualizar_kpis(df_KPIs_previsualizacion,f"{config['paths']['gold_dir']}/{config['source']['previsualizacion_KPIs']}")
        
    with open(f"{config['paths']['logs']}/{config['source']['logs_file']}", "a",encoding='utf-8') as log_file:
        log_file.write(f"{dt.datetime.now()} INFO: Transformación de datos completada\n ")
    #--------------------
    #Load
    #--------------------
    with open(f"{config['paths']['logs']}/{config['source']['logs_file']}", "a",encoding='utf-8') as log_file:
        log_file.write(f"{dt.datetime.now()} INFO: Carga de datos iniciada\n ")
    #load_database.carga_datos(df_kpis,"df_kpis")
    #load_database.carga_datos(df_gold_data_Cali,"df_gold_data_Cali")
    with open(f"{config['paths']['logs']}/{config['source']['logs_file']}", "a",encoding='utf-8') as log_file:
        log_file.write(f"{dt.datetime.now()} INFO: Extraccion de datos completada\n ")

if __name__ == "__main__":
    main()
