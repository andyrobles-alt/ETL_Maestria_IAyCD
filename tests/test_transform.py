import pandas as pd
import yaml
import src.extract.extract_csv as extract_csv
import src.transform.clean_csv as transform_csv

with open("config/config.yaml", "r") as file:
        config = yaml.safe_load(file)


#------------------
#Validacion de no hay duplicados en las llaves de union de los datasets
#------------------

def test_keys_duplicates():

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
    
    assert not df_transformacion_cg.duplicated(subset=["Anio_Encuesta", "Mes_Encuesta", "Id_Vivienda", "Id_Hogar", "Orden_Persona"]).any()
    assert not df_transformacion_ocupados.duplicated(subset=["Anio_Encuesta", "Mes_Encuesta", "Id_Vivienda", "Id_Hogar", "Orden_Persona"]).any()

def test_expected_columns():

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
    columnas_interes = [
    'Periodo_Recoleccion',
    'Mes_Encuesta',
    'Anio_Encuesta',
    'Id_Vivienda',
    'Id_Hogar',
    'Orden_Persona',
    'Numero_Hogar',
    'Area_Metropolitana',
    'Factor_Expansion',
    'Departamento',
    'Sexo_Al_Nacer',
    'Edad',
    'Pago_Mensual_Salud',
    'Nivel_Educativo',
    'Titulo_o_Diploma',
    'Titulo_Diploma_EnQue',
    'Poblacion_Mayor_18',
    'Categoria_Trabajo',
    'Horas_Trabajo_Semanales',
    'Ingreso_Laboral',
    'Rama_Act_Empleo_Ppal'
]
    assert list(df_cg_ocupados.columns) == columnas_interes