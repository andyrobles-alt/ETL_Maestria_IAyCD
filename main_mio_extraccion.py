#================================================================
# 1. LIBRERIAS
#================================================================
'''
Se realiza la importacion de todas las librerias que se utilizaran en el proyecto
'''
import pandas as pd
from pathlib import Path

#================================================================
# 2. Lectura de los archivos CSV
#================================================================

#================================================================
# Diciembre
ruta = Path(__file__).resolve().parent / "Caracteristicas_generales_Dic.xlsx"
df_DIC_Caracteristicas_Generales = pd.read_excel(ruta)

ruta2 = Path(__file__).resolve().parent / "Ocupados_Dic.xlsx"
df_DIC_Ocupados = pd.read_excel(ruta2)

#================================================================
# Noviembre
ruta3 = Path(__file__).resolve().parent / "Caracteristicas_generales_Nov.xlsx"
df_NOV_Caracteristicas_Generales = pd.read_excel(ruta3)

ruta4 = Path(__file__).resolve().parent / "Ocupados_Nov.xlsx"
df_NOV_Ocupados = pd.read_excel(ruta4)

#================================================================
# Octubre
ruta5 = Path(__file__).resolve().parent / "Caracteristicas_generales_Oct.xlsx"
df_OCT_Caracteristicas_Generales = pd.read_excel(ruta5)

ruta6 = Path(__file__).resolve().parent / "Ocupados_Oct.xlsx"
df_OCT_Ocupados = pd.read_excel(ruta6)

# Unir características generales de octubre, noviembre y diciembre
df_caracteristicas = pd.concat(
    [
        df_OCT_Caracteristicas_Generales.copy().assign(Mes="Octubre"),
        df_NOV_Caracteristicas_Generales.copy().assign(Mes="Noviembre"),
        df_DIC_Caracteristicas_Generales.copy().assign(Mes="Diciembre"),
    ],
    ignore_index=True,
)

# Unir ocupados
df_ocupados = pd.concat(
    [
        df_OCT_Ocupados.copy().assign(Mes="Octubre"),
        df_NOV_Ocupados.copy().assign(Mes="Noviembre"),
        df_DIC_Ocupados.copy().assign(Mes="Diciembre"),
    ],
    ignore_index=True,
)

#print("Archivo de caracteristicas generales:")
#print(df_DIC_Caracteristicas_Generales.head())
#print("Archivo de caracteristicas ocupados:")
#print(df_DIC_Ocupados.head())
#print("Archivo consolidao:")
#print(df_caracteristicas.head())

#================================================================
# 3. ANALISIS EXPLORATORIO DE LOS DATOS
#================================================================
# 1. HACER EL JOIN ENTRE AMBOS CSV
# unir_modulos elimina las columnas compartidas y conserva PER y MES como llaves.

# orden = numero de la persona en el hogar 
# Directorio = identificador de la vivienda
# Secuencia_P = identificador del hogar
"""
df_datos_consolidados = pd.merge(
    df_caracteristicas, df_ocupados,
    on=['DIRECTORIO', 'SECUENCIA_P', 'ORDEN'], how='inner'
)
"""

from analisis_exploratorio_geih import unir_modulos, explorar_geih

# Incluye año y mes para evitar cruces de registros entre periodos.
df_datos_consolidados = unir_modulos(
    df_caracteristicas,
    df_ocupados
)


#df_datos_consolidados = pd.merge(df_DIC_Caracteristicas_Generales,df_DIC_Ocupados,on=['DIRECTORIO', 'SECUENCIA_P', 'ORDEN'], how='inner')

# 2. VEAMOS CUANTOS DATOS TENEMOS
#print("Datos consolidados:")
#print(df_datos_consolidados.shape)

# 3. Entender que tipo de informacion tenemos
#print("Tipo de información que tenemos:")
#print(df_datos_consolidados.info()) # Informacion sobre las caracteristicas de cada columna

# 4. Ahora vemos las estadisticas basicas para entender las variables numericas
#print("Estadistica basica de las variables numericas:")
#print(df_datos_consolidados.describe())

# 5. Filtrar y borrar
'''
Procedemos a filtrar y borrar las columnas que no vamos a usar. 
Este es un trabajo que se realiza previamente con ayuda del diccionario
'''
# Lista de columnas que SÍ vas a usar en tu AED
columnas_interes = ['PERIODO', 'MES', 'PER','DIRECTORIO','SECUENCIA_P','ORDEN','HOGAR','AREA','FEX_C18','DPTO','P3271','P6040','P6120','P3042','P3043','P3043S1','POB_MAY18','P6430','P6800','INGLABO','RAMA2D_R4']

# El DataFrame ahora solo tendrá esas columnas
df_filtrado = df_datos_consolidados[columnas_interes]
print("Dataframe filtrado:")
#print(df_filtrado.head())

# 5. Renombrar las columnas
'''
Debido a que tenemos el diccionario proporcionado por el DANE, podemos hacer uso de este para renombrar aquellas columnas
que tienen identificadores

'''
# Creamos un diccionario con la siguiente estructura: 'NombreViejo': 'NombreNuevo'
diccionario_nombres = {
    'P3271': 'Sexo_Al_Nacer',
    'P6040': 'Edad',
    'P6120': 'Cuando_Paga_o_Descuentan',
    'P3042': 'Nivel_Educativo',
    'P3043': 'Titulo_o_Diploma',
    'P3043S1': 'Titulo_Diploma_EnQue',
    'P6430':'Categoria_Trabajo',
    'P6800':'Horas_Trabajo_Semanales',
    'RAMA2D_R4':'Rama_Act_Empleo_Ppal',
    #'P3044S2':'Productos_Comercializados',
    #'P6420S2':'Rama_Actividad_Economica',
    #'P6500':'Comisiones',
    #'P6510S1':'Salario',
    #'P3042':'Nivel_Educativo', Se elimina porque ya se encuentra en el diccionario de nombres
    'PT': 'Poblacion_Total',
    'INGLABO': 'Ingreso_Laboral'
}

# Renombras las columnas de una sola vez
df_filtrado.rename(columns=diccionario_nombres, inplace=True)
print("Archivo con data total filtrada y renombrada:")
print(df_filtrado.head())

# Muestra tablas en la consola e histogramas en ventanas.
df_aed, tablas_aed = explorar_geih(df_filtrado)

df_filtrado.to_excel(
    Path(__file__).resolve().parent / "data_total_filtrada_y_renombrada.xlsx",
    index=False
)

#--------------------------------------------------------
#6. Reemplazar los códigos por sus etiquetas de texto
#--------------------------------------------------------

from diccionarios_geih import traducir_geih

# Sustituye df_filtrado por el nombre de tu DataFrame.
df_legible, sin_equivalencia = traducir_geih(df_filtrado)

print("Archivo con reemplazo de etiquetas de texto:")
print(df_legible.head())

# Revisar los valores que no tienen una etiqueta en el Excel.
print("Sin equivalencias")
#print(sin_equivalencia)

df_legible.insert(11,"DEPTO_COD", df_filtrado["DPTO"])  # Mantener el código de departamento original

#--------------------------------------------------------
#7. Ajustar los campos vacios de la version legible
#--------------------------------------------------------
niveles_sin_diploma = ['Ninguno', 'Básica primaria (1o - 5o)', 'Básica secundaria (6o - 9o)']
df_legible.loc[
    df_legible['Titulo_o_Diploma'].isna() & df_legible['Nivel_Educativo'].isin(niveles_sin_diploma),
    'Titulo_o_Diploma'
] = 'Sin diploma'

df_legible['Ingreso_Laboral'] = df_legible['Ingreso_Laboral'].astype(object).fillna('Na')
df_legible['AREA'] = df_legible['AREA'].fillna('otros')

# Completar solo los vacios de menores de 18, sin modificar Cuando_Paga_o_Descuentan.
# Completar los campos vacios de Edad.
df_legible['Edad'] = df_legible['Edad'].astype(object).fillna('Na')

# Exportar la versión con textos.
df_legible.to_csv(
    "GEIH_filtrado_legible.csv",
    sep=";",
    index=False,
    encoding="utf-8-sig"
)


print("Informacion de columnas")
print(df_caracteristicas.info())
print("Informacion de columnas de archivo filtrado")
print(df_filtrado.info())

#--------------------------------------------------------
#7. Ajustar los campos vacios de la version legible
#--------------------------------------------------------
niveles_sin_diploma = ['Ninguno', 'Básica primaria (1o - 5o)', 'Básica secundaria (6o - 9o)']
df_legible.loc[
    df_legible['Titulo_o_Diploma'].isna() & df_legible['Nivel_Educativo'].isin(niveles_sin_diploma),
    'Titulo_o_Diploma'
] = 'Sin diploma'

df_legible['Ingreso_Laboral'] = df_legible['Ingreso_Laboral'].astype(object).fillna('Na')
df_legible['AREA'] = df_legible['AREA'].fillna('otros')

# Completar los campos vacios de Edad.
df_legible['Edad'] = df_legible['Edad'].astype(object).fillna('Na')

# Exportar la versión con textos.
df_legible.to_csv(
    "GEIH_filtrado_legible.csv",
    sep=";",
    index=False,
    encoding="utf-8-sig"
)
print("Informacion de columnas")
print(df_caracteristicas.info())
print("Informacion de columnas de archivo filtrado")
print(df_filtrado.info())

