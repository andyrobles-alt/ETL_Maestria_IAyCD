import pandas as pd

from src.transform.gold_transformations import table_KPIs


def test_table_kpis_retains_all_groups_and_preserves_input():
    filas = []
    for rama in ['industria', 'otras ramas']:
        for categoria in ['Empleado', 'Trabajador por cuenta propia']:
            filas.extend([
                {
                    'Rama_Act_Empleo_Ppal': rama,
                    'Categoria_Trabajo': categoria,
                    'Edad': 25,
                    'Factor_Expansion': 3.0,
                },
                {
                    'Rama_Act_Empleo_Ppal': rama,
                    'Categoria_Trabajo': categoria,
                    'Edad': 60,
                    'Factor_Expansion': 2.0,
                },
            ])
    entrada = pd.DataFrame(filas)
    original = entrada.copy(deep=True)

    resultado = table_KPIs(entrada)

    assert len(resultado) == 4
    assert set(zip(
        resultado['Rama_Act_Empleo_Ppal'], resultado['Categoria_Trabajo']
    )) == {
        ('Manufactura', 'Asalariado'),
        ('Manufactura', 'Trabajador por cuenta propia'),
        ('otras ramas', 'Asalariado'),
        ('otras ramas', 'Trabajador por cuenta propia'),
    }
    assert resultado['Proporcion_55+'].eq(40.0).all()
    assert resultado['Razon_Reemplazo'].eq(1.5).all()
    assert resultado['Edad_Mediana'].eq(25).all()
    pd.testing.assert_frame_equal(entrada, original)
