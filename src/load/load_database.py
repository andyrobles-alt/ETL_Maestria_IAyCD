import pandas as pd
import psycopg2
from dotenv import load_dotenv
import os
from pandas.api.types import (
    is_bool_dtype,
    is_integer_dtype,
    is_float_dtype,
    is_datetime64_any_dtype,
)

def map_dtype(columna):
    if is_bool_dtype(columna.dtype):
        return "BOOLEAN"
    if is_integer_dtype(columna.dtype):
        return "BIGINT"
    if is_float_dtype(columna.dtype):
        return "DOUBLE PRECISION"
    if is_datetime64_any_dtype(columna.dtype):
        return "TIMESTAMP"
    return "TEXT"

# Load environment variables from .env
load_dotenv()

def carga_datos(df_final,table_name):

    # Fetch variables
    DATABASE_URL = os.getenv("DATABASE_URL")

    # Connect to the database
    connection = psycopg2.connect(DATABASE_URL)
    cursor = connection.cursor()

    df_insert = df_final.copy().astype(object)
    df_insert = df_insert.where(pd.notnull(df_insert),None)
 
    try:
        # =====================================================
        # 1. Crear tabla si no existe
        # =====================================================
        definiciones = []
        for col in df_final.columns:
            tipo_postgres = map_dtype(df_final[col])
            definiciones.append(f'"{col}" {tipo_postgres}')

        create_table_query = f"""
            CREATE TABLE IF NOT EXISTS "{table_name}" (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            {", ".join(definiciones)}
            );
        """
        cursor.execute(create_table_query)
        # Confirmar cambios en PostgreSQL
        connection.commit()
        print(
            f'Tabla "{table_name}" creada o verificada correctamente.'
        )
        # =====================================================
        # 2. INSERTAR DATOS
        # =====================================================
        # Construir nombres de columnas
        columnas_sql = ", ".join(
            [f'"{col}"' for col in df_insert.columns]
        )
        # Crear un %s por cada columna
        placeholders = ", ".join(
            ["%s"] * len(df_insert.columns)
        )
        # Construir INSERT
        insert_query = f"""
            INSERT INTO "{table_name}" ({columnas_sql})
            VALUES ({placeholders})
        """
        # Convertir cada fila del DataFrame en una tupla
        data = [
            tuple(
                None if pd.isna(valor) else valor
                for valor in fila
            )
            for fila in df_insert.itertuples(
                index=False,
                name=None
            )
        ]
        # Insertar todas las filas
        cursor.executemany(
            insert_query,
            data
        )
        # =====================================================
        # 3. CONFIRMAR TRANSACCIÓN
        # =====================================================
        connection.commit()
        print(
            f'Se insertaron {len(data)} registros '
            f'en la tabla "{table_name}".'
        )

    except Exception as e:
        # Deshacer cambios si ocurre un error
        connection.rollback()
        print(f"Error al crear la tabla: {e}")

    finally:
        # Cerrar conexión
        cursor.close()
        connection.close()
