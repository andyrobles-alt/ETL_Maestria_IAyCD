"""Validacion del notebook con sus fuentes y una referencia independiente."""

import contextlib
import io
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


@pytest.fixture(scope='module', params=[
    'eda_transformacion.ipynb', 'eda_transformacion_validado.ipynb',
])
def eda(request):
    ruta = Path('notebooks') / request.param
    notebook = json.loads(ruta.read_text(encoding='utf-8'))
    contexto = {'__name__': '__main__'}
    for indice, celda in enumerate(notebook['cells']):
        if celda['cell_type'] == 'code':
            with contextlib.redirect_stdout(io.StringIO()):
                exec(compile(''.join(celda['source']), f'{ruta}:celda-{indice}', 'exec'), contexto)
    return contexto


def reference_population(eda, restricted=True):
    # Recuperar edades y factores de CG, y codigos de Ocupados.
    claves = eda['CLAVES']
    referencia = eda['ocupados'][claves + [
        'Rama_Act_Empleo_Ppal', 'Categoria_Trabajo', 'Area_Metropolitana'
    ]].join(eda['cg'].set_index(claves)[['Edad', 'Factor_Expansion']], on=claves)
    referencia = referencia.loc[referencia['Area_Metropolitana'].eq(76)].copy()
    if restricted:
        referencia = referencia.loc[
            referencia['Edad'].ge(18)
            & referencia['Factor_Expansion'].gt(0)
            & referencia['Rama_Act_Empleo_Ppal'].between(1, 99)
            & referencia['Categoria_Trabajo'].isin([1, 2, 3, 4, 7])
        ].copy()
    referencia['sector'] = np.where(
        referencia['Rama_Act_Empleo_Ppal'].between(10, 33), 'Manufactura', 'Otros sectores'
    )
    referencia['posicion'] = np.where(
        referencia['Categoria_Trabajo'].eq(4), 'Cuenta propia', 'Asalariados'
    )
    return referencia


def reference_statistics(grupo):
    edades = grupo['Edad'].to_numpy()
    pesos = grupo['Factor_Expansion'].to_numpy()
    probabilidades = pesos / pesos.sum()
    mayores = edades >= 55
    jovenes = (edades >= 18) & (edades <= 34)
    por_edad = grupo.groupby('Edad')['Factor_Expansion'].sum().sort_index()
    mediana = por_edad.index[np.searchsorted(por_edad.cumsum().to_numpy(), pesos.sum() / 2)]
    return {
        'n_grupo': len(grupo), 'n_18_34': int(jovenes.sum()), 'n_55_mas': int(mayores.sum()),
        'proporcion': np.dot(probabilidades, mayores) * 100,
        'razon': np.dot(probabilidades, jovenes) / np.dot(probabilidades, mayores),
        'mediana': float(mediana), 'kish': 1 / np.dot(probabilidades, probabilidades),
    }


def test_notebook_headers_and_person_month_controls(eda):
    assert len(eda['columnas_fuente']) == 6
    for nombre, columnas in eda['columnas_fuente'].items():
        assert len(columnas) == (55 if nombre.startswith('caracteristicasgenerales') else 202)
        assert {'PER', 'MES', 'DIRECTORIO', 'SECUENCIA_P', 'ORDEN', 'AREA'} <= set(columnas)
    assert eda['union_correcta']
    assert not any(eda['discrepancias'].values())
    assert eda['resumen_union'][['claves_nulas', 'claves_duplicadas']].to_numpy().sum() == 0
    assert eda['cruce_final']['_merge'].eq('both').all()


def test_notebook_temporal_sums_and_quality_counts(eda):
    final = eda['df_traducido_clean']
    meses = eda['meses'].set_index(['Anio_Encuesta', 'Mes_Encuesta'])
    assert set(meses.index) == {(2025, 10), (2025, 11), (2025, 12)}
    for periodo, fila in meses.iterrows():
        fuente = eda['ocupados'].loc[
            eda['ocupados']['Anio_Encuesta'].eq(periodo[0])
            & eda['ocupados']['Mes_Encuesta'].eq(periodo[1])
        ]
        assert fila['n_ocupados'] == len(fuente)
        assert fila['suma_factor'] == pytest.approx(np.sum(fuente['Factor_Expansion']))
    claves = eda['CLAVES']
    edades = eda['ocupados'][claves].join(eda['cg'].set_index(claves)['Edad'], on=claves)['Edad']
    codigos = eda['ocupados']
    assert eda['calidad']['edad_menor_18'] == int(edades.lt(18).sum())
    assert eda['calidad']['ingreso_laboral_nulo'] == int(codigos['Ingreso_Laboral'].isna().sum())
    assert eda['calidad']['posicion_fuera_alcance'] == int(
        (~codigos['Categoria_Trabajo'].isin([1, 2, 3, 4, 7])).sum()
    )
    assert eda['calidad']['rama_sin_codigo_valido'] == int((~codigos['Rama_Act_Empleo_Ppal'].between(1, 99)).sum())
    assert eda['calidad']['rama_etiquetada_otras_ramas'] == int((~codigos['Rama_Act_Empleo_Ppal'].between(10, 33)).sum())
    assert len(final) == len(codigos)


def test_notebook_pilot_population_and_every_weighted_indicator(eda):
    referencia = reference_population(eda)
    claves = eda['CLAVES']
    pd.testing.assert_index_equal(
        pd.MultiIndex.from_frame(eda['piloto'][claves]).sort_values(),
        pd.MultiIndex.from_frame(referencia[claves]).sort_values(),
    )
    indicadores = eda['indicadores_piloto'].set_index(['sector', 'posicion'])
    assert len(indicadores) == 4
    for grupo, fuente in referencia.groupby(['sector', 'posicion']):
        esperado = reference_statistics(fuente)
        actual = indicadores.loc[grupo]
        assert actual['n_grupo'] == esperado['n_grupo']
        assert actual['n_18_34'] == esperado['n_18_34']
        assert actual['n_55_mas'] == esperado['n_55_mas']
        assert actual['proporcion_55_mas_pct'] == pytest.approx(round(esperado['proporcion'], 1))
        assert actual['razon_reemplazo'] == pytest.approx(round(esperado['razon'], 2))
        assert actual['edad_mediana_ponderada'] == esperado['mediana']
        assert actual['n_efectivo_aprox'] == pytest.approx(round(esperado['kish'], 1))
        assert 0 < actual['n_efectivo_aprox'] <= actual['n_grupo'] + 0.05
        for columna, n in [
            ('alerta_grupo', esperado['n_grupo']),
            ('alerta_razon_18_34', esperado['n_18_34']),
            ('alerta_razon_55_mas', esperado['n_55_mas']),
        ]:
            prefijo = 'CRÍTICO' if n < 30 else 'CAUTELA' if n < 100 else 'Sin alerta'
            assert actual[columna].startswith(prefijo)


def test_notebook_gold_comparison_explains_population_difference(eda):
    referencia = reference_population(eda, restricted=False)
    assert {'sector', 'posicion', 'proporcion_55_mas_pct', 'razon_reemplazo'} <= set(
        eda['comparacion_gold'].columns
    )
    assert all(columna.isascii() and '?' not in columna for columna in eda['comparacion_gold'])
    comparacion = eda['comparacion_gold'].set_index(['sector', 'posicion'])
    assert len(referencia) == len(eda['cali_total']) == 3349
    assert len(eda['piloto']) == 3178
    assert len(eda['cali_excluido']) == 171
    for grupo, fuente in referencia.groupby(['sector', 'posicion']):
        esperado = reference_statistics(fuente)
        actual = comparacion.loc[grupo]
        assert actual['proporcion_55_mas_gold_pct'] == pytest.approx(esperado['proporcion'])
        assert actual['razon_reemplazo_gold'] == pytest.approx(esperado['razon'])
        assert actual['edad_mediana_gold'] == esperado['mediana']


def test_notebook_median_and_alert_boundaries(eda):
    assert eda['mediana_ponderada']([18, 34, 55], [1, 1, 10]) == 55
    assert eda['mediana_ponderada']([60, 20], [1, 1]) == 20
    for n, prefijo in [(29, 'CRÍTICO'), (30, 'CAUTELA'), (99, 'CAUTELA'), (100, 'Sin alerta')]:
        assert eda['alerta_n'](n).startswith(prefijo)
