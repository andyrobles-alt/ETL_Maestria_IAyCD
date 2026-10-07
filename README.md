# ETL_Maestria_IAyCD

Pipeline ETL para analizar el relevo generacional en el empleo manufacturero con la Gran Encuesta Integrada de Hogares (GEIH) de octubre, noviembre y diciembre de 2025. Utiliza una arquitectura medallón: **Bronze → Silver → Gold → PostgreSQL/Supabase**.

**Estado del alcance:** el objetivo del proyecto es estudiar el municipio de Cali. El código actual filtra **Cali A.M.**, y los notebooks documentan que los insumos públicos no permiten separar Cali de Yumbo. Los resultados actuales son un prototipo metropolitano; el resultado municipal requiere incorporar y validar un identificador de municipio.

## 1. Contexto y objetivo

En una empresa manufacturera, reemplazar a una persona con años de experiencia también implica conservar conocimiento práctico que muchas veces no está documentado. El proyecto examina la presencia de trabajadores de **18 a 34 años** frente a quienes tienen **55 años o más**, como aproximación descriptiva a la presión de relevo generacional.

El objetivo es construir, en aproximadamente **40 horas de trabajo del equipo**, un pipeline reproducible que integre los datos del trimestre octubre–diciembre de 2025, aplique los factores de expansión y compare manufactura con los demás sectores, separando asalariados y trabajadores por cuenta propia.

El análisis no proyecta el comportamiento futuro, no predice retiros individuales ni establece relaciones de causa y efecto. La razón de reemplazo describe una relación entre grupos de edad; no demuestra que una persona joven pueda reemplazar las competencias de una persona mayor.

### Resultados clave previstos (OKR)

| Resultado clave | Entregable previsto |
|---|---|
| **KR1** | Gestionar en la primera semana el acceso al dato municipal y procesar los seis insumos definidos, con bitácora de carga. |
| **KR2** | Obtener una tabla persona-mes sin duplicados, con ubicación, edad, actividad, posición ocupacional y factor de expansión validados. |
| **KR3** | Entregar una tabla curada, tres KPI por grupo de comparación, diccionario de datos, reporte de calidad y visualización reproducible. |

Estos resultados expresan las metas del proyecto. La cobertura municipal permanece pendiente; las pruebas y los notebooks permiten revisar los controles implementados.

## 2. Datos y unidad de análisis

Se utilizan **dos módulos por mes**: Características generales y Ocupados. Los seis CSV deben estar en `data/bronze/`, con los nombres definidos en [config/config.yaml](config/config.yaml):

| Mes de 2025 | Características generales | Ocupados |
|---|---|---|
| Octubre | `caracteristicasgenerales_oct.csv` | `ocupados_oct.csv` |
| Noviembre | `caracteristicasgenerales_nov.csv` | `ocupados_nov.csv` |
| Diciembre | `caracteristicasgenerales_dic.csv` | `ocupados_dic.csv` |

La extracción espera archivos separados por **punto y coma (`;`)**, con codificación **Latin-1**. No descarga los datos automáticamente.

La unidad de análisis es una **observación persona-mes**. La clave implementada es:

```text
Anio_Encuesta + Mes_Encuesta + Id_Vivienda + Id_Hogar + Orden_Persona
```

Corresponde a las variables originales `PER + MES + DIRECTORIO + SECUENCIA_P + ORDEN`.

El cruce toma **Ocupados como población de referencia** y añade sus características generales. La unión exige claves no vacías, una correspondencia uno a uno y que cada ocupado tenga una coincidencia en Características generales.

## 3. Indicadores y grupos de comparación

**FEX** representa el factor de expansión de la encuesta, almacenado como `Factor_Expansion` y procedente de `FEX_C18`. Los KPI se calculan con pesos, no solo contando filas.

| KPI | Cálculo | Interpretación |
|---|---|---|
| **Proporción de 55+** | Σ FEX de personas de 55+ / Σ FEX del grupo × 100 | Porcentaje ponderado de trabajadores mayores en el grupo. |
| **Razón de reemplazo** | Σ FEX de personas de 18–34 / Σ FEX de personas de 55+ | Jóvenes por cada trabajador mayor; un valor de 1 indica igual peso de ambos grupos. |
| **Edad mediana** | Primera edad cuyo peso acumulado alcanza al menos el 50 % del peso total | Edad central de la distribución ponderada. |

Los grupos previstos son manufactura asalariada, manufactura por cuenta propia, demás sectores asalariados y demás sectores por cuenta propia.

### Diferencias entre Gold y el análisis exploratorio

La implementación de Gold y el piloto de los notebooks usan poblaciones distintas:

| Criterio | Gold: `table_KPIs` | EDA de transformación |
|---|---|---|
| Cobertura | Cali A.M. | Cali A.M. |
| Edad | Conserva todas las edades del subconjunto | Exige edad de 18 años o más |
| Cuenta propia | Etiqueta `Trabajador por cuenta propia` | Código original `P6430 = 4` |
| Asalariados | Etiqueta como `Asalariado` toda posición diferente de cuenta propia | Solo códigos `P6430 = 1, 2, 3, 7`; excluye las demás posiciones |
| Sector | Agrupa las ramas traducidas de manufactura y la etiqueta `otras ramas` | Usa `RAMA2D_R4`: 10–33 para manufactura; otros códigos válidos para demás sectores |
| Controles adicionales | No aplica los filtros adicionales del piloto | Exige factor positivo y rama válida; presenta diagnósticos de tamaño de muestra |

Por estas diferencias, los valores de Gold y del EDA pueden variar. La clasificación de Gold requiere ajustarse antes de interpretar su etiqueta `Asalariado` como una delimitación estricta del empleo asalariado.

**Tratamiento del trimestre:** Gold agrupa las observaciones de los tres meses por sector y categoría; no produce KPI mensuales separados. Las proporciones y razones son cocientes de sumas ponderadas del trimestre. La mediana se calcula sobre la distribución agrupada. Una suma de factores de tres meses no debe interpretarse como población simultánea ni como número de personas únicas.

Si un grupo no tiene peso en personas de 55+, la razón de reemplazo queda indefinida. El EDA contempla este caso; Gold no incorpora una protección explícita frente a la división por cero.

## 4. Estructura y flujo del repositorio

```text
.
├── config/
│   └── config.yaml                 # Rutas y nombres de entradas/salidas
├── data/
│   ├── bronze/                     # Los seis CSV de entrada
│   ├── silver/                     # Datos transformados y tabla integrada
│   └── gold/                       # Subconjunto de Cali A.M. y KPI
├── src/
│   ├── extract/                    # Lectura y concatenación de CSV
│   ├── transform/                  # Limpieza, diccionarios y cálculo de KPI
│   └── load/                       # Carga a PostgreSQL con psycopg2
├── notebooks/                      # Exploración, controles y resultados del piloto
├── scripts/
│   └── execute_notebook.py         # Ejecución de notebooks en un kernel limpio
├── tests/                          # Pruebas de extracción, transformación y resultados
├── logs/                           # Bitácora y archivos locales de ejecución
├── main.py                         # Orquestación del pipeline completo
├── requirements.txt                # Dependencias de Python
├── .gitignore                      # Exclusiones del repositorio
└── .env                            # Configuración local de conexión; no se versiona
```

1. **Bronze / extracción:** lee los tres CSV de cada módulo y los concatena en un DataFrame por módulo.
2. **Silver / transformación:** selecciona y renombra columnas, elimina claves duplicadas conservando la primera fila, integra los módulos, traduce códigos y estandariza valores. Convierte edad e ingreso a valores numéricos; los ingresos nulos se conservan.
3. **Gold / indicadores:** selecciona Cali A.M. y calcula los tres KPI por sector y categoría ocupacional.
4. **Carga:** crea las tablas de destino si no existen e inserta los datos de Gold en PostgreSQL, incluido un destino Supabase con conexión PostgreSQL.

Los mapas de nombres y categorías están en [renombrar_columnas_geih.py](src/transform/renombrar_columnas_geih.py) y [diccionarios_geih.py](src/transform/diccionarios_geih.py).

## 5. Instalación y configuración

Ejecuta los comandos desde la **raíz del repositorio**, donde están `main.py` y `requirements.txt`. Las instrucciones siguientes están escritas para **Windows PowerShell**.

### 5.1. Preparar Python

El entorno local del proyecto utiliza **Python 3.14**. Necesitas Python, los seis CSV y una base PostgreSQL para ejecutar también la carga.

Crea un entorno virtual e instala las dependencias:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install pytest
```

`pytest` se instala por separado porque no está declarado en el `requirements.txt` actual. Los comandos usan directamente el Python del entorno; no es necesario activarlo.

### 5.2. Preparar los datos y las carpetas

Verifica que los seis archivos de la sección 2 estén en `data/bronze/`. Si cambias sus nombres o ubicaciones, actualiza `config/config.yaml`.

Crea las carpetas locales de salida:

```powershell
New-Item -ItemType Directory -Force -Path data/silver, data/gold, logs | Out-Null
```

Este paso es necesario después de clonar: esas carpetas están ignoradas por Git y `main.py` no las crea antes de escribir. Si modificas las rutas de la configuración, crea las carpetas correspondientes.

### 5.3. Configurar PostgreSQL o Supabase

Crea un archivo llamado `.env` en la raíz del proyecto, con la variable que lee [load_database.py](src/load/load_database.py):

```dotenv
DATABASE_URL="postgresql://USUARIO:CONTRASENA@HOST:5432/BASE_DE_DATOS"
```

Reemplaza los valores de ejemplo por los de tu base. Para Supabase, utiliza la cadena de conexión PostgreSQL suministrada por el servicio, con su puerto y parámetros. La cuenta necesita permisos para crear tablas e insertar registros.

`.env` contiene configuración privada y está incluido en `.gitignore`. Cada persona que clone el repositorio debe crear su propia configuración local.

## 6. Ejecutar el pipeline

Con los datos, las carpetas y la conexión preparados:

```powershell
.\.venv\Scripts\python.exe main.py
```

`main.py` ejecuta extracción, transformación, generación de Gold y carga. Actualmente no dispone de una opción de consola para omitir la base de datos.

### Archivos generados

Los nombres siguientes corresponden a la configuración actual:

| Capa | Archivo | Contenido |
|---|---|---|
| Silver | `data/silver/caracteristicasgenerales_transformado.csv` | Características generales seleccionadas y renombradas, con claves deduplicadas. |
| Silver | `data/silver/ocupados_trimestre_transformado.csv` | Ocupados de los tres meses, con columnas seleccionadas y claves deduplicadas. |
| Silver | `data/silver/df_traducido_clean.xlsx` | Tabla integrada, traducida y estandarizada. |
| Gold | `data/gold/df_gold_data_Cali.xlsx` | Tabla curada del subconjunto de Cali A.M. |
| Gold | `data/gold/df_gold_data_KPIs.xlsx` | Tres KPI por combinación de sector y categoría. |
| Logs | `logs/logs.txt` | Fechas y mensajes de las etapas; se añaden al archivo existente. |

En PostgreSQL se crean o utilizan las tablas **`df_kpis`** y **`df_gold_data_Cali`**. La carga agrega una clave técnica `id` autogenerada.

**Al repetir la ejecución:** los archivos de salida se sobrescriben y los registros se vuelven a insertar en la base. La carga actual no realiza actualización, reemplazo ni deduplicación de registros existentes; varias ejecuciones pueden duplicar los datos del destino. Para reproducir una carga inicial, utiliza una base de prueba con esas tablas aún sin datos.

Comprueba los archivos generados y el número de filas en las tablas. La función de carga captura e imprime algunos errores SQL, por lo que un mensaje final en el log no basta para confirmar que los datos se insertaron.

## 7. Ejecutar las pruebas

Para ejecutar toda la suite:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

La suite completa requiere los CSV de Bronze y los productos de Silver y Gold, porque las pruebas de EDA leen esos archivos. Genera primero las salidas con el pipeline. Las pruebas actuales no llaman al módulo de carga ni validan una conexión PostgreSQL.

| Archivo | Qué revisa |
|---|---|
| `tests/test_extract.py` | Que la selección y deduplicación conserve el número de registros de los insumos actuales. |
| `tests/test_transform.py` | Unicidad de las claves y columnas esperadas en la integración. |
| `tests/test_quality.py` | Tipo numérico del ingreso laboral, conservando los nulos del origen. |
| `tests/test_gold_transformations.py` | Grupos de KPI, valores ponderados y conservación del DataFrame de entrada. |
| `tests/test_etl_results.py` | Extracción, cruce persona-mes, traducciones, calidad y KPI contrastados con cálculos independientes. |
| `tests/test_eda_transformacion.py` | Ambos notebooks de transformación, su población de análisis y su comparación con Gold. |

También puedes ejecutar cada archivo por separado:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_gold_transformations.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_extract.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_quality.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_transform.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_etl_results.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_eda_transformacion.py -q
```

Para revisar el procesamiento desde Bronze sin configurar PostgreSQL ni generar previamente Silver y Gold, puedes ejecutar las cinco primeras pruebas de la tabla; excluye el test de EDA. Que pasen las pruebas no certifica la cobertura municipal ni la precisión estadística de los indicadores.

## 8. Revisar el análisis exploratorio

Después de generar Silver y Gold, abre [eda_transformacion_validado.ipynb](notebooks/eda_transformacion_validado.ipynb) y selecciona el entorno `.venv` como kernel en tu editor compatible con Jupyter. El notebook muestra controles de unión, calidad, cobertura, indicadores del piloto y comparación con Gold. [eda_transformacion.ipynb](notebooks/eda_transformacion.ipynb) contiene también ese análisis.

Para recalcular y guardar sus salidas desde la consola:

```powershell
.\.venv\Scripts\python.exe scripts/execute_notebook.py notebooks/eda_transformacion_validado.ipynb --cwd .
```

El comando ejecuta las celdas en un kernel limpio y **actualiza las salidas del archivo notebook**. No modifica los CSV ni los Excel de entrada. `main.py` no ejecuta automáticamente los notebooks ni exporta gráficos.

Los notebooks presentan diagnósticos del tamaño de muestra y explican las limitaciones del piloto. Esos controles ayudan a interpretar los resultados, pero no equivalen a una evaluación de precisión del diseño muestral.

## 9. Problemas frecuentes

| Situación | Qué revisar |
|---|---|
| No se encuentra `config/config.yaml` | Ejecuta los comandos desde la raíz del proyecto. |
| No se encuentra un CSV de entrada | Revisa los seis nombres y las rutas de `config/config.yaml`. |
| No se puede escribir el log o un archivo de salida | Crea `logs/`, `data/silver/` y `data/gold/` antes de ejecutar. |
| Aparece `ModuleNotFoundError` | Instala las dependencias con el mismo Python de `.venv` que utilizas para ejecutar. |
| Pytest o el notebook no encuentra archivos de Silver/Gold | Genera previamente las salidas del pipeline. |
| La conexión PostgreSQL falla | Revisa `DATABASE_URL`, credenciales, host, puerto y conectividad. |
| La carga muestra un error SQL | Verifica permisos y compatibilidad del esquema de las tablas; revisa las filas insertadas. |
| Gold y EDA presentan KPI distintos | Consulta sus diferencias de población y clasificación en la sección 3. |

## 10. Archivos locales y versionamiento

El `.gitignore` actual excluye `.env`, los entornos virtuales, cachés, `logs/`, `data/silver/` y `data/gold/`. Los insumos de Bronze no están excluidos por esas reglas.

Silver, Gold y logs se generan localmente. Si un archivo ya estaba versionado antes de añadirlo a `.gitignore`, la regla por sí sola no lo retira del seguimiento ni del historial de Git.

## Equipo

Carlos Andrés Agredo Robles · Juan Andres Gutierrez · Camilo Ernesto Balanta
