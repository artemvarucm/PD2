## Proyecto de Datos desarrollado con los datos de señales ADS-B de aviones

#### OBJETIVO: encontrar el orden de despegue de los aviones

### INDICE
- [🚀 Ejecutar el proyecto](#ejecutar-el-proyecto)
    - [Entrega 1: Visualizaciones](#entrega-1:-visualizaciones)
    - [Entrega 2: Modelos](#entrega-2:-modelos)
- [💡 Estructura del proyecto](#estructura-del-proyecto)
- [🛠️ Para desarrolladores](#para-desarrolladores)
<!--- [Estrategias](#)-->

### 🚀 Ejecutar el proyecto
#### Requisitos
+ `python` >= 3.12
+ `uv` >= 0.4
#### Ejecución
Instalación de librerías y activación del entorno

**Instalación uv:**
1. pip install uv
2. localizar donde se ha instalado el paquete(probablemente en C:\Users\TuUsuario\AppData\Local\Packages\PythonSoftwareFoundation\LocalCache\local-packages\Python311(o la versión de la que se disponga)\site-packages\uv
3. añadir esta dirección en el path en las variables de entorno

**Activación del entorno uv:**
```bash
$ uv sync
$ source .venv/bin/activate
```
**Ejecución del notebook seleccionando el entorno virtual .venv**

### Entrega 1: Visualizaciones
Los dashboards se ejecutan desde el **directorio raíz**.
```bash
$ uv run src/visualization/aire_tierra/dashboard.py
$ uv run src/visualization/despegues/dashboard.py
$ uv run src/visualization/mapa/dashboard.py
```

### Entrega 2: Modelos
#### Procesado
Hay que ajustar las rutas en cada archivo.
```bash
$ uv run src/procesado_datos/ml_1-preprocesado_masivos.py
$ uv run src/procesado_datos/ml_2-concat.py
$ uv run src/procesado_datos/ml_3-sampling.py
$ uv run src/procesado_datos/ml_4-añade_columnas_extra.py
$ uv run src/procesado_datos/ml_5-train_test_split.py
```
Todos estos archivos funcionan en un pipeline que sacan 2 archivos: train y test
#### Modelos


### 💡 Estructura del proyecto
`assets`: contiene el conjunto de recursos globales del
    proyecto imágenes, capturas, js usadas, como iconos.

`docs`: contiene alguna documentación, junto con algunos problemas que pueden surgir.
        Se completa con la wiki del github.

`data`: contiene alguna documentación, junto con algunos problemas que pueden surgir.
        Se completa con la wiki del github.
- `ex1`: entrega 1
- `ex2`: entrega 2
- `geojson`: archivos geojsons
- `scenarios`: archivos de escenarios
- `Train`: archivos utilizados en train/test 

`src/evaluacion/`: contiene el dashboard `dashboard_tiempos_espera.py` para evaluación de modelos junto con los datos de predicciones, para evaluar solo hay que cambiar la ruta. Se ejecuta con uv run dashboard_tiempos_espera.py

`src/exploracion`: contiene notebooks de exploracion
- `src/exploracion/entrega_1`: contiene notebooks de exploracion de la primera entrega.
- `src/exploracion/entrega_2`: contiene notebooks de exploracion de la segunda entrega.
    - `procesado_nuevo.ipynb`: es para analizar los datos SIN samplear.
    - `sampled.ipynb`: es para analizar los datos sampleados
    - `aeropuerto_geojsons.py`: es para visualizar los geojsons

`src/procesado_datos/`: código que se usa para procesar y sacar los datos. 
- Archivos que empiezan por `viz_` se utilizaban para los ejercicios de la entrega 1
- Archivos que empiezan por `ml_`(ml_2-concat.py...) forman el pipeline del preprocesado de la entrega 2
- Archivo `datos_meteo.py` (versión .py "limpia" del notebook `web_scraping_meteorologicos.ipynb``)

`src/procesado_datos/codigo_cluster_cloudera`: directorio con el código para ejecutar el procesado en el cluster con Spark

`src/procesado_datos/utils`: módulo para preprocesar más fácilmente, las clases se usaron al inicio del desarrollo y representan cada tipo de mensaje.

`src/visualization`: código de visualizaciones de datos de la primera entrega.

`src/modelado/`: código usado para los diferentes modelos IA para predicciones.

`src/modelado`: código de todos los modelos
- `src/modelado/tensorflow`: código tensorflow
    - `src/modelado/tensorflow/modelado_con_sampleo_y_pistas_ocupadas.ipynb` : código usado para el modelo de tensorflow antes de tener los datos sampleados.
    - `src/modelado/tensorflow/pruebaModeloPistasTensorFlow.py`: código para entranar la red neuronal con los datos definitivos.
- `src/modelado/modeloXGBOOST`
    - `src/modelado/modeloXGBOOST/TrainModel`: código del modelo, entrena el modelo y guarda los resultados de test.
    - `src/modelado/modeloXGBOOST/PredictTest`: código para predecir sobre el conjunto de test (mucho más rápido que ejcutar el modelo entero de nuevo).
    - `src/modelado/modeloXGBOOST/PreprocesadoScenario`: código para preprocesar los datos que llegan en un escenario.
    - `src/modelado/modeloXGBOOST/PredictScenario`: código para predecir un ICAO concreto de un escenario.




### 🛠️ Para desarrolladores
#### Documentación consultada

1. Problema original: https://mode-s.org/1090mhz/

2. PDF con más detalles sobre ADS-B: https://airmetar.main.jp/radio/ADS-B%20Decoding%20Guide.pdf

3. Documentación pyModeS: https://mode-s.org/pymodes/api/index.html
