"""Reconciliacion de las etapas y calculo independiente de los KPIs reales."""

import numpy as np
import pandas as pd
import pytest
import yaml

from src.extract import extract_csv
from src.transform import clean_csv, gold_transformations
from src.transform.diccionarios_geih import DICCIONARIOS
from src.transform.renombrar_columnas_geih import NOMBRES_GEIH


KEYS = ['Anio_Encuesta', 'Mes_Encuesta', 'Id_Vivienda', 'Id_Hogar', 'Orden_Persona']
CG_COLUMNS = [
    'PERIODO', 'MES', 'PER', 'DIRECTORIO', 'SECUENCIA_P', 'ORDEN', 'HOGAR',
    'AREA', 'FEX_C18', 'DPTO', 'P3271', 'P6040', 'P6120', 'P3042', 'P3043',
    'P3043S1', 'POB_MAY18',
]
OCC_COLUMNS = [
    'PERIODO', 'MES', 'PER', 'DIRECTORIO', 'SECUENCIA_P', 'ORDEN', 'HOGAR',
    'AREA', 'FEX_C18', 'DPTO', 'P6430', 'P6800', 'INGLABO', 'RAMA2D_R4',
]


def build_frames():
    with open('config/config.yaml', encoding='utf-8') as archivo:
        config = yaml.safe_load(archivo)
    frames = {'config': config}
    for nombre, prefijo, identificador in [
        ('cg', 'caracteristicas_generales', 'df_caracteristicas_generales_copia'),
        ('ocupados', 'ocupados', 'df_ocupados_copia'),
    ]:
        rutas = [
            f"{config['paths']['bronze_dir']}/{config['source'][f'{prefijo}_{mes}']}"
            for mes in ['dic', 'nov', 'oct']
        ]
        partes = extract_csv.extract_csv(rutas)
        bruto = extract_csv.merge_csv(partes)
        frames[f'{nombre}_partes'] = partes
        frames[f'{nombre}_bruto'] = bruto
        frames[nombre] = clean_csv.clean(bruto.copy(), identificador)
    frames['unido'] = clean_csv.join_datasets([frames['cg'], frames['ocupados']], KEYS)
    frames['traducido'] = clean_csv.traslation_values(frames['unido'])
    frames['limpio'] = clean_csv.clean_values(frames['traducido'])
    frames['cali'] = gold_transformations.table_metropolitan_area(frames['limpio'])
    frames['kpis'] = gold_transformations.table_KPIs(frames['cali'])
    return frames


@pytest.fixture(scope='module')
def frames():
    return build_frames()


def test_extraction_preserves_all_months_and_rows(frames):
    for nombre in ['cg', 'ocupados']:
        bruto = frames[f'{nombre}_bruto']
        assert len(bruto) == sum(len(parte) for parte in frames[f'{nombre}_partes'])
        inicio = 0
        for parte in frames[f'{nombre}_partes']:
            # concat unifica tipos entre meses; los valores deben conservarse.
            pd.testing.assert_frame_equal(
                bruto.iloc[inicio:inicio + len(parte)], parte, check_dtype=False,
            )
            inicio += len(parte)
        assert set(bruto['MES']) == {10, 11, 12}


def test_cleaning_preserves_selected_values_and_person_month_keys(frames):
    for nombre, columnas in [('cg', CG_COLUMNS), ('ocupados', OCC_COLUMNS)]:
        esperado = frames[f'{nombre}_bruto'][columnas].rename(columns=NOMBRES_GEIH)
        assert not esperado[KEYS].isna().any().any()
        assert not esperado.duplicated(KEYS).any()
        pd.testing.assert_frame_equal(frames[nombre], esperado.reset_index(drop=True))


def test_join_reconciles_every_occupied_person_and_shared_fields(frames):
    cg = frames['cg'].set_index(KEYS)
    ocupados = frames['ocupados'].set_index(KEYS)
    assert ocupados.index.isin(cg.index).all()
    comunes = ocupados.columns.intersection(cg.columns)
    pd.testing.assert_frame_equal(cg.loc[ocupados.index, comunes], ocupados[comunes])
    esperado = cg.loc[ocupados.index].join(ocupados[ocupados.columns.difference(cg.columns)])
    actual = frames['unido'].set_index(KEYS)
    pd.testing.assert_frame_equal(actual.sort_index(), esperado[actual.columns].sort_index())


def test_translation_preserves_rows_and_applies_configured_domains(frames):
    original = frames['unido']
    traducido = frames['traducido']
    assert list(original.columns) == list(traducido.columns)
    dominios = {
        'Area_Metropolitana': 'Area_Metropolitana', 'Departamento': 'Departamento',
        'Sexo_Al_Nacer': 'P3271', 'Nivel_Educativo': 'P3042',
        'Titulo_o_Diploma': 'P3043', 'Categoria_Trabajo': 'P6430',
        'Rama_Act_Empleo_Ppal': 'RAMA2D_R4',
    }
    for columna in original.columns:
        esperado = original[columna]
        if columna in dominios:
            mapa = {int(codigo): valor for codigo, valor in DICCIONARIOS[dominios[columna]].items()}
            esperado = esperado.replace(mapa)
        pd.testing.assert_series_equal(traducido[columna], esperado, check_dtype=False)


def test_value_cleanup_preserves_measures_and_classifies_only_manufacturing(frames):
    traducido, limpio = frames['traducido'], frames['limpio']
    assert len(limpio) == len(traducido)
    assert set(limpio.columns) == set(traducido.columns) - {'Titulo_Diploma_EnQue', 'Pago_Mensual_Salud'}
    for columna in KEYS + ['Edad', 'Ingreso_Laboral', 'Factor_Expansion', 'Horas_Trabajo_Semanales']:
        pd.testing.assert_series_equal(limpio[columna], traducido[columna], check_dtype=False)
    manufactura = frames['unido']['Rama_Act_Empleo_Ppal'].between(10, 33)
    assert limpio.loc[~manufactura, 'Rama_Act_Empleo_Ppal'].eq('otras ramas').all()
    pd.testing.assert_series_equal(
        limpio.loc[manufactura, 'Rama_Act_Empleo_Ppal'],
        traducido.loc[manufactura, 'Rama_Act_Empleo_Ppal'], check_dtype=False,
    )
    pesos = limpio['Factor_Expansion'].to_numpy()
    assert np.isfinite(pesos).all() and (pesos > 0).all()
    assert limpio['Edad'].between(0, 110).all()
    assert pd.api.types.is_numeric_dtype(limpio['Ingreso_Laboral'])


def test_cali_contains_exactly_source_area_76(frames):
    esperado = frames['limpio'].loc[frames['unido']['Area_Metropolitana'].eq(76)]
    pd.testing.assert_frame_equal(frames['cali'], esperado[frames['cali'].columns])
    assert not frames['cali'].duplicated(KEYS).any()


def independent_kpis(frames):
    # Clasificar desde los codigos originales, sin reutilizar table_KPIs.
    fuente = frames['unido'].loc[frames['unido']['Area_Metropolitana'].eq(76)].copy()
    fuente['sector'] = np.where(fuente['Rama_Act_Empleo_Ppal'].between(10, 33), 'Manufactura', 'otras ramas')
    fuente['categoria'] = np.where(fuente['Categoria_Trabajo'].eq(4), 'Trabajador por cuenta propia', 'Asalariado')
    resultados = []
    for (sector, categoria), grupo in fuente.groupby(['sector', 'categoria']):
        edades = grupo['Edad'].to_numpy()
        pesos = grupo['Factor_Expansion'].to_numpy()
        total = np.sum(pesos)
        mayores = np.dot(pesos, edades >= 55)
        jovenes = np.dot(pesos, (edades >= 18) & (edades <= 34))
        # Acumular pesos por edad, en lugar de ordenar los registros individuales.
        pesos_por_edad = grupo.groupby('Edad')['Factor_Expansion'].sum().sort_index()
        posicion = np.searchsorted(np.cumsum(pesos_por_edad.to_numpy()), total / 2)
        resultados.append({
            'Rama_Act_Empleo_Ppal': sector, 'Categoria_Trabajo': categoria,
            'Proporcion_55+': 100 * mayores / total, 'Razon_Reemplazo': jovenes / mayores,
            'Edad_Mediana': pesos_por_edad.index[posicion],
        })
    return pd.DataFrame(resultados)


def test_real_kpis_match_independent_weighted_calculations(frames):
    pd.testing.assert_frame_equal(frames['kpis'], independent_kpis(frames), rtol=1e-10, atol=1e-10)
    assert len(frames['kpis']) == 4
    assert np.isfinite(frames['kpis'].select_dtypes(include='number').to_numpy()).all()


def test_kpi_age_boundaries_and_weighted_median():
    entrada = pd.DataFrame({
        'Rama_Act_Empleo_Ppal': ['otras ramas'] * 7,
        'Categoria_Trabajo': ['Trabajador por cuenta propia'] * 7,
        'Edad': [17, 18, 34, 35, 54, 55, 70],
        'Factor_Expansion': [1., 2., 3., 4., 5., 6., 10.],
    })
    resultado = gold_transformations.table_KPIs(entrada).iloc[0]
    assert resultado['Proporcion_55+'] == pytest.approx(100 * 16 / 31)
    assert resultado['Razon_Reemplazo'] == pytest.approx(5 / 16)
    assert resultado['Edad_Mediana'] == 55
