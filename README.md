# ETL_Maestria_IAyCD

Pipeline ETL para analizar el relevo generacional en el empleo manufacturero con la Gran Encuesta Integrada de Hogares (GEIH) de octubre, noviembre y diciembre de 2025. Utiliza una arquitectura medallón: **Bronze → Silver → Gold**, genera un reporte Excel con los KPI y sus gráficos, y dispone de carga a **PostgreSQL/Supabase**. Las llamadas de carga están habilitadas en `main.py`, por lo que la ejecución completa requiere una conexión PostgreSQL válida.

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
4. **Previsualización:** lee el Excel de KPI y genera un segundo Excel que conserva los datos originales e incorpora gráficos explicativos.
5. **Carga:** después de generar el reporte, `main.py` llama a `load_database.carga_datos` para insertar los KPI y la tabla curada de Cali A.M. en PostgreSQL/Supabase. El módulo crea las tablas de destino si no existen.

Los mapas de nombres y categorías están en [renombrar_columnas_geih.py](src/transform/renombrar_columnas_geih.py) y [diccionarios_geih.py](src/transform/diccionarios_geih.py).

## 5. Instalación y configuración

Ejecuta los comandos desde la **raíz del repositorio**, donde están `main.py` y `requirements.txt`. Las instrucciones siguientes están escritas para **Windows PowerShell**.

### 5.1. Preparar Python

El entorno local del proyecto utiliza **Python 3.14**. Para ejecutar `main.py` completo necesitas Python, los seis CSV, una base PostgreSQL accesible y la variable `DATABASE_URL` configurada.

Crea un entorno virtual e instala las dependencias:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install pytest
```

`pytest` se instala por separado porque aún no está declarado en el `requirements.txt` actual. El reporte Excel utiliza `pandas`, `matplotlib`, `openpyxl` y `Pillow`, que ya están incluidos en ese archivo. `pathlib` e `io` forman parte de Python. Los comandos usan directamente el Python del entorno; no es necesario activarlo. Si ya tienes un entorno llamado `venv`, sustituye `.venv` por `venv` en los comandos.

### 5.2. Preparar los datos y las carpetas

Verifica que los seis archivos de la sección 2 estén en `data/bronze/`. Si cambias sus nombres o ubicaciones, actualiza `config/config.yaml`.

Crea las carpetas locales de salida:

```powershell
New-Item -ItemType Directory -Force -Path data/silver, data/gold, logs | Out-Null
```

Este paso es necesario después de clonar: esas carpetas están ignoradas por Git y `main.py` no las crea antes de escribir. Si modificas las rutas de la configuración, crea las carpetas correspondientes.

### 5.3. Configurar PostgreSQL o Supabase

La carga está habilitada y requiere una conexión válida. Crea un archivo llamado `.env` en la raíz del proyecto con la variable que lee [load_database.py](src/load/load_database.py), o define `DATABASE_URL` en el entorno de ejecución:

```dotenv
DATABASE_URL="postgresql://USUARIO:CONTRASENA@HOST:5432/BASE_DE_DATOS"
```

Reemplaza los valores de ejemplo por los de tu base. Para Supabase, utiliza la cadena de conexión PostgreSQL suministrada por el servicio, con su puerto y parámetros. La cuenta necesita permisos para crear tablas e insertar registros.

`.env` contiene configuración privada y está incluido en `.gitignore`. Cada persona que clone el repositorio debe crear su propia configuración local.

### 5.4. Revisar la configuración del reporte

[config/config.yaml](config/config.yaml) define las rutas y los nombres de los archivos. El reporte utiliza estas claves, ya presentes en la configuración actual:

```yaml
paths:
  gold_dir: "data/gold"

source:
  excel_salida_gold_data_KPIs: "df_gold_data_KPIs.xlsx"
  previsualizacion_KPIs: "previsualizacion_KPIs.xlsx"
```

Este bloque es un fragmento de la configuración: conserva las demás claves de entradas, salidas y logs. `main.py` construye las rutas combinando `paths.gold_dir` con cada nombre de `source`. El archivo de KPI y el reporte deben tener nombres diferentes, porque el reporte se guarda como un nuevo archivo.

## 6. Ejecutar el pipeline

Con el entorno, los datos, las carpetas y la conexión PostgreSQL preparados:

```powershell
.\.venv\Scripts\python.exe main.py
```

`main.py` ejecuta extracción, transformación, generación de Gold, el reporte Excel de previsualización y la carga a PostgreSQL, en ese orden. Las dos llamadas de carga están activas. No existe una opción de consola para omitir la base de datos. Los archivos locales se generan antes de intentar la conexión; su existencia no confirma que la carga haya finalizado.

### Archivos generados

Los nombres siguientes corresponden a la configuración actual:

| Capa | Archivo | Contenido |
|---|---|---|
| Silver | `data/silver/caracteristicasgenerales_transformado.csv` | Características generales seleccionadas y renombradas, con claves deduplicadas. |
| Silver | `data/silver/ocupados_trimestre_transformado.csv` | Ocupados de los tres meses, con columnas seleccionadas y claves deduplicadas. |
| Silver | `data/silver/df_traducido_clean.xlsx` | Tabla integrada, traducida y estandarizada. |
| Gold | `data/gold/df_gold_data_Cali.xlsx` | Tabla curada del subconjunto de Cali A.M. |
| Gold | `data/gold/df_gold_data_KPIs.xlsx` | Tres KPI por combinación de sector y categoría. |
| Reporte | `data/gold/previsualizacion_KPIs.xlsx` | Datos originales del DataFrame de KPI y tres hojas con gráficos explicativos. |
| Logs | `logs/logs.txt` | Fechas y mensajes de las etapas; se añaden al archivo existente. |

### Reporte Excel de previsualización

La función `previsualizar_kpis`, en [clean_csv.py](src/transform/clean_csv.py), recibe el DataFrame leído desde `df_gold_data_KPIs.xlsx` y la ruta del nuevo reporte. `main.py` la llama después de exportar Gold.

| Hoja | Contenido |
|---|---|
| `Datos_KPI` | Todas las filas y columnas del DataFrame recibido, conservadas sin la limpieza utilizada para graficar. |
| `Proporcion_55` | Barras del porcentaje ponderado de trabajadores de 55+ por sector y categoría. |
| `Razon_Reemplazo` | Barras de jóvenes de 18–34 por trabajador de 55+, con una línea de referencia en 1. |
| `Edad_Mediana` | Barras de la edad mediana ponderada de cada grupo, expresada en años. |

Cada gráfico incluye valores, unidades, periodo, cobertura, cálculo y explicación. Las imágenes se insertan directamente en el Excel; no se generan PNG externos ni son gráficos nativos editables de Excel. La función trabaja con una copia para preparar las etiquetas y excluye valores no numéricos o infinitos únicamente de los gráficos; conserva los datos originales en `Datos_KPI`.

El reporte compara KPI agregados por grupo; no muestra distribuciones individuales de edad o ingreso. El valor de 1 en la razón indica igual peso de jóvenes y mayores, no garantiza suficiencia del relevo. La visualización conserva las definiciones y limitaciones de Gold descritas en la sección 3.

### Carga a PostgreSQL

La ejecución crea o utiliza las tablas **`df_kpis`** y **`df_gold_data_Cali`**. La carga agrega una clave técnica `id` autogenerada.

**Al repetir la ejecución:** los archivos de Silver, Gold y el reporte se sobrescriben, el log acumula mensajes y los registros se vuelven a insertar en la base. El módulo de carga no realiza actualización, reemplazo ni deduplicación de registros existentes. Varias ejecuciones pueden duplicar los datos del destino. Para reproducir una carga inicial, utiliza una base de prueba con esas tablas aún sin datos.

Comprueba los archivos generados y el número de filas en las tablas de PostgreSQL. La función de carga captura e imprime algunos errores SQL, por lo que los mensajes de consola y del log deben contrastarse con los registros del destino para confirmar una inserción correcta.

## 7. Ejecutar las pruebas

Para ejecutar toda la suite:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

La suite completa requiere los CSV de Bronze y los productos de Silver y Gold, porque las pruebas de EDA leen esos archivos. Genera primero las salidas con el pipeline. Las pruebas actuales no llaman al módulo de carga, no validan una conexión PostgreSQL ni verifican el contenido visual del reporte Excel.

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

El comando ejecuta las celdas en un kernel limpio y **actualiza las salidas del archivo notebook**. No modifica los CSV ni los Excel de entrada. `main.py` no ejecuta automáticamente los notebooks; sí genera el reporte Excel con gráficos de KPI descrito en la sección 6.

Los notebooks presentan diagnósticos del tamaño de muestra y explican las limitaciones del piloto. Esos controles ayudan a interpretar los resultados, pero no equivalen a una evaluación de precisión del diseño muestral.

## 9. Problemas frecuentes

| Situación | Qué revisar |
|---|---|
| No se encuentra `config/config.yaml` | Ejecuta los comandos desde la raíz del proyecto. |
| No se encuentra un CSV de entrada | Revisa los seis nombres y las rutas de `config/config.yaml`. |
| No se puede escribir el log o un archivo de salida | Crea `logs/`, `data/silver/` y `data/gold/` antes de ejecutar. |
| Aparece `ModuleNotFoundError` | Instala las dependencias con el mismo Python de `.venv` que utilizas para ejecutar. |
| Pytest o el notebook no encuentra archivos de Silver/Gold | Genera previamente las salidas del pipeline. |
| Falta la clave `previsualizacion_KPIs` | Comprueba que exista dentro de `source` en `config/config.yaml`. |
| Aparece `list indices must be integers or slices, not str` al construir la ruta | Usa `config['source']['previsualizacion_KPIs']`; `source` pertenece al diccionario `config`. |
| No se puede sobrescribir el reporte Excel | Cierra `previsualizacion_KPIs.xlsx` en Excel y revisa los permisos de la carpeta. |
| La conexión PostgreSQL falla | Revisa `DATABASE_URL`, credenciales, host, puerto y conectividad; la carga forma parte de la ejecución actual de `main.py`. |
| La carga muestra un error SQL | Verifica permisos y compatibilidad del esquema de las tablas; revisa las filas insertadas. |
| Gold y EDA presentan KPI distintos | Consulta sus diferencias de población y clasificación en la sección 3. |

## 10. Archivos locales y versionamiento

El `.gitignore` actual excluye `.env`, los entornos virtuales, cachés, `logs/`, `data/silver/` y `data/gold/`. Los insumos de Bronze no están excluidos por esas reglas.

Silver, Gold, el reporte de previsualización y los logs se generan localmente. `previsualizacion_KPIs.xlsx` queda excluido por la regla `/data/gold/`, mientras que `config/config.yaml`, `main.py`, `src/transform/clean_csv.py` y `requirements.txt` deben versionarse para que otra persona pueda reproducirlo. Si un archivo ya estaba versionado antes de añadirlo a `.gitignore`, la regla por sí sola no lo retira del seguimiento ni del historial de Git.

### Comprobar si los cambios llegaron a GitHub

Desde la raíz del repositorio, estos comandos permiten revisar los archivos pendientes y la configuración del último commit sin hacer un push:

```powershell
git status --short
git diff HEAD -- README.md config/config.yaml main.py src/transform/clean_csv.py requirements.txt
git show HEAD:config/config.yaml
git rev-parse HEAD
git ls-remote origin refs/heads/main
```

`git diff HEAD` muestra diferencias locales, tanto preparadas como sin preparar, frente al último commit. `git show` permite comprobar si ese commit incluye `source.previsualizacion_KPIs`. Si los hashes de los dos últimos comandos coinciden, el último commit local coincide con la rama `main` del remoto en ese momento; los cambios locales sin commit todavía no forman parte de ese resultado.

La referencia local `origin/main` puede estar desactualizada: por sí sola no confirma el estado actual de GitHub. Los productos de Silver y Gold, el reporte y los logs no tienen que aparecer en el remoto para reproducir el pipeline, porque se regeneran al ejecutar el proyecto.

## Equipo

Carlos Andrés Agredo Robles · Juan Andres Gutierrez · Camilo Ernesto Balanta
