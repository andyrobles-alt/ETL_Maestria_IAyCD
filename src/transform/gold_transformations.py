import pandas as pd
def table_metropolitan_area(df_traducido_clean: pd.DataFrame)-> pd.DataFrame:
    columnas_gold = [ 'Id_Vivienda', 'Id_Hogar','Numero_Hogar','Orden_Persona','Anio_Encuesta','Mes_Encuesta','Edad', 'Rama_Act_Empleo_Ppal', 'Categoria_Trabajo', 'Factor_Expansion']
    df_gold = df_traducido_clean.loc[df_traducido_clean['Area_Metropolitana'] == 'CALI  A.M.', columnas_gold]
    return df_gold

def table_KPIs(df_traducido_clean: pd.DataFrame)-> pd.DataFrame:
    #columnas_interes = ['Edad','Rama_Act_Empleo_Ppal','Categoria_Trabajo', 'Factor_Expansion']
    columnas_interes = ['Rama_Act_Empleo_Ppal','Categoria_Trabajo']
    df_kpis = df_traducido_clean.copy()
    df_kpis.loc[df_kpis['Rama_Act_Empleo_Ppal'] != 'otras ramas', columnas_interes[0]] = 'Manufactura'
    df_kpis.loc[df_kpis['Categoria_Trabajo'] != 'Trabajador por cuenta propia', columnas_interes[1]] = 'Asalariado'
    grupos = df_kpis.groupby(['Rama_Act_Empleo_Ppal','Categoria_Trabajo'])
    resultados = []
    for (empleo, categoria),grupo in grupos:
        #Total_grupo
        grupo_total = grupo['Factor_Expansion'].sum()

        #Suma de factor de expansion de los mayores
        mayores = grupo.loc[grupo['Edad']>=55, 'Factor_Expansion'].sum()
        #Suma de factor de expansion de los jovenes
        jovenes = grupo.loc[grupo['Edad'].between(18,34),'Factor_Expansion'].sum()

        #Definimos KPIs
        #KPI1: Proporción de 55+
        proporcion_55_flex = (mayores / grupo_total)*100

        #KPI2: Razón de reemplazo
        razon_reemplazo = (jovenes / mayores)

        #KPI3: Edad mediana
        edad_ordenada = grupo.sort_values('Edad')
        edad_acumulada_fex = edad_ordenada['Factor_Expansion'].cumsum()

        mediana_edad = edad_ordenada.loc[edad_acumulada_fex >= (grupo_total/2),'Edad'].iloc[0]

        #Guarda_resultados:
       
        resultados.append({
            'Rama_Act_Empleo_Ppal': empleo,
            'Categoria_Trabajo': categoria,
            'Proporcion_55+': proporcion_55_flex,
            'Razon_Reemplazo': razon_reemplazo,
            'Edad_Mediana': mediana_edad
        })
    tabla_kpis = pd.DataFrame(resultados)
    return tabla_kpis


