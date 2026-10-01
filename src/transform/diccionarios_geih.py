"""
Traducción de códigos GEIH para una copia de presentación del DataFrame.
"""

import re
import pandas as pd

NOMBRES_COLUMNAS = {
    'SECUENCIA_P': 'SECUENCIA_P',
    'ORDEN': 'ORDEN',
    'HOGAR': 'HOGAR',
    'REGIS': 'REGIS',
    'Area_Metropolitana': 'Area_Metropolitana',
    'CLASE': 'CLASE',
    'Departamento': 'Departamento',
    'P3271': 'Sexo_Al_Nacer',
    'P3042': 'Nivel_Educativo',
    'P3043': 'Titulo_o_Diploma',
    'P3043S1': 'Titulo_Diploma_EnQue',
    'P6430': 'Categoria_Trabajo',
    'P6420S2': 'Rama_Actividad_Economica',
    'RAMA2D_R4': 'Rama_Act_Empleo_Ppal',
    'P3044S2': 'Productos_Comercializados',
}
# Diccionarios con claves de texto normalizadas.
DICCIONARIOS = {
    # Identificador: el Excel no define categorías para este campo.
    'SECUENCIA_P': {
    },
    # Identificador: el Excel no define categorías para este campo.
    'ORDEN': {
    },
    # Identificador: el Excel no define categorías para este campo.
    'HOGAR': {
    },
    # Diccionario!J12, Diccionario!J67
    'REGIS': {
        '10': 'Registro de personas',
        '60': 'Registro de ocupados',
        '70': 'Registro de los no ocupados',
    },
    # Diccionario!J13, Diccionario!J68
    'Area_Metropolitana': {
        '5': 'MEDELLIN A.M.',
        '8': 'BARRANQUILLA A.M.',
        '11': 'BOGOTA',
        '13': 'CARTAGENA',
        '15': 'TUNJA',
        '17': 'MANIZALEZ A.M.',
        '18': 'FLORENCIA',
        '19': 'POPAYAN',
        '20': 'VALLEDUPAR',
        '23': 'MONTERIA',
        '27': 'QUIBDO',
        '41': 'NEIVA',
        '44': 'RIOACHA',
        '47': 'SANTA MARTA',
        '50': 'VILLAVICENCIO',
        '52': 'PASTO',
        '54': 'CUCUTA A.M.',
        '63': 'ARMENIA',
        '66': 'PEREIRA A.M.',
        '68': 'BUCARAMANGA A.M.',
        '70': 'SINCELEJO',
        '73': 'IBAGUE',
        '76': 'CALI  A.M.',
        '88': 'SAN ANDRES',
        '81': 'ARAUCA',
        '85': 'CASANARE',
        '86': 'PUTUMAYO',
        '91': 'AMAZONAS',
        '94': 'GUAINIA',
        '95': 'GUAVIARE',
        '97': 'VAUPES',
        '99': 'VICHADA',
    },
    # Diccionario!J14, Diccionario!J69
    'CLASE': {
        '1': 'Cabecera',
        '2': 'Resto',
    },
    # Diccionario!J16, Diccionario!J71
    'Departamento': {
        '5': 'ANTIOQUIA',
        '8': 'ATLANTICO',
        '11': 'BOGOTA',
        '13': 'BOLIVAR',
        '15': 'BOYACA',
        '17': 'CALDAS',
        '18': 'CAQUETA',
        '19': 'CAUCA',
        '20': 'CESAR',
        '23': 'CORDOBA',
        '25': 'CUNDINAMARCA',
        '27': 'CHOCO',
        '41': 'HUILA',
        '44': 'LA GUAJIRA',
        '47': 'MAGDALENA',
        '50': 'META',
        '52': 'NARIÑO',
        '54': 'NORTE DE SANTANDER',
        '63': 'QUINDIO',
        '66': 'RISALRALDA',
        '68': 'SANTANDER',
        '70': 'SUCRE',
        '73': 'TOLIMA',
        '76': 'VALLE',
        '81': 'ARAUCA',
        '85': 'CASANARE',
        '86': 'PUTUMAYO',
        '88': 'SAN ANDRES',
        '91': 'AMAZONAS',
        '94': 'GUAINIA',
        '95': 'GUAVIARE',
        '97': 'VAUPES',
        '99': 'VICHADA',
    },
    # Diccionario!J19
    'P3271': {
        '1': 'Masculino',
        '2': 'Femenino',
    },
    # Diccionario!J52
    'P3042': {
        '1': 'Ninguno',
        '2': 'Preescolar',
        '3': 'Básica primaria (1o - 5o)',
        '4': 'Básica secundaria (6o - 9o)',
        '5': 'Media académica (Bachillerato clásico)',
        '6': 'Media técnica (Bachillerato técnico)',
        '7': 'Normalista',
        '8': 'Técnica profesional',
        '9': 'Tecnológica',
        '10': 'Universitaria',
        '11': 'Especialización',
        '12': 'Maestría',
        '13': 'Doctorado',
        '99': 'No sabe, no informa',
    },
    # Diccionario!J55
    'P3043': {
        '1': 'Ninguno',
        '2': 'Media académica (Bachillerato clásico)',
        '3': 'Media técnica (Bachillerato técnico)',
        '4': 'Normalista',
        '5': 'Técnica profesional',
        '6': 'Tecnológica',
        '7': 'Universitaria',
        '8': 'Especialización',
        '9': 'Maestría',
        '10': 'Doctorado',
        '99': 'No sabe, no informa',
    },
    # Dominio vacío en el Excel; requiere catálogo para traducirlo.
    'P3043S1': {
    },
    # Diccionario!J87
    'P6430': {
        '1': 'Obrero o empleado de empresa particular',
        '2': 'Obrero o empleado del gobierno',
        '3': 'Empleado doméstico',
        '4': 'Trabajador por cuenta propia',
        '5': 'Patrón o empleador',
        '6': 'Trabajador familiar sin remuneración',
        '7': 'Jornalero o Peón',
        '8': 'Otro',
    },
    # Dominio vacío en el Excel; requiere catálogo para traducirlo.
    'P6420S2': {
    },
    # Diccionario!J259
    'RAMA2D_R4': {
        '10': 'Elaboración de productos alimenticios',
        '11': 'Elaboración de bebidas',
        '12': 'Elaboración de productos de tabaco',
        '13': 'Fabricación de productos textiles',
        '14': 'Confección de prendas de vestir',
        '15': 'Curtido y recurtido de cueros; fabricación de calzado y artículos de viaje',
        '16': 'Transformación de la madera y fabricación de productos de madera y corcho, excepto muebles',
        '17': 'Fabricación de papel, cartón y productos de papel y cartón',
        '18': 'Actividades de impresión y producción de copias a partir de grabaciones originales',
        '19': 'Coquización, fabricación de productos de la refinación del petróleo y mezcla de combustibles',
        '20': 'Fabricación de sustancias y productos químicos',
        '21': 'Fabricación de productos farmacéuticos, sustancias químicas medicinales y productos botánicos',
        '22': 'Fabricación de productos de caucho y de plástico',
        '23': 'Fabricación de otros productos minerales no metálicos',
        '24': 'Fabricación de productos metalúrgicos básicos',
        '25': 'Fabricación de productos elaborados de metal, excepto maquinaria y equipo',
        '26': 'Fabricación de productos informáticos, electrónicos y ópticos',
        '27': 'Fabricación de aparatos y equipo eléctrico',
        '28': 'Fabricación de maquinaria y equipo n.c.p.',
        '29': 'Fabricación de vehículos automotores, remolques y semirremolques',
        '30': 'Fabricación de otros tipos de equipo de transporte',
        '31': 'Fabricación de muebles, colchones y somieres',
        '32': 'Otras industrias manufactureras',
        '33': 'Instalación, mantenimiento y reparación especializada de maquinaria y equipo',
        
    },
    # Dominio vacío en el Excel; requiere catálogo para traducirlo.
    'P3044S2': {
    },
}

IDENTIFICADORES = {"SECUENCIA_P", "ORDEN", "HOGAR"}

def normalizar_codigo(valor):
    """Iguala 1, '1', '01' y 1.0 solo para buscar la etiqueta."""
    if pd.isna(valor):
        return None
    texto = str(valor).strip()
    if not texto:
        return None
    if re.fullmatch(r"[0-9]+(?:[.,]0+)?", texto):
        return str(int(re.split(r"[.,]", texto)[0]))
    return texto

def traducir_geih(df):
    """Devuelve (copia legible, reporte de valores sin equivalencia).

    No modifica ni filtra registros. Solo renombra las columnas solicitadas y
    sustituye los códigos cuya etiqueta está documentada. Los identificadores
    quedan intactos. Admite aplicar la función a una copia ya traducida.
    """
    if not df.columns.is_unique:
        raise ValueError("Hay columnas duplicadas. Resuélvelas antes de traducir.")

    salida = df.copy()
    pendientes = []

    for original, nuevo in NOMBRES_COLUMNAS.items():
        nombres = {original.upper(), nuevo.upper()}
        candidatas = [c for c in salida.columns
                      if str(c).strip().upper() in nombres]
        if not candidatas:
            continue
        if len(candidatas) > 1:
            raise ValueError(f"Hay dos columnas para {original}: {candidatas}")

        columna = candidatas[0]
        salida = salida.rename(columns={columna: nuevo})
        if original in IDENTIFICADORES:
            continue

        serie = salida[nuevo]
        mapa = DICCIONARIOS[original]
        codigos = serie.map(normalizar_codigo)
        etiquetas = codigos.map(mapa)
        salida[nuevo] = serie.astype(object).where(etiquetas.isna(), etiquetas)

        sin_etiqueta = (codigos.notna() & etiquetas.isna()
                        & ~serie.isin(list(mapa.values())))
        motivo = ("Sin catálogo de equivalencias en el Excel" if not mapa
                  else "Código no incluido en el dominio disponible")
        for valor, cantidad in serie[sin_etiqueta].astype(str).value_counts().items():
            pendientes.append({"Variable": original, "Columna": nuevo,
                               "Valor_original": valor, "Registros": int(cantidad),
                               "Motivo": motivo})

    reporte = pd.DataFrame(pendientes, columns=[
        "Variable", "Columna", "Valor_original", "Registros", "Motivo"
    ])
    return salida,reporte

