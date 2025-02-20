## Proyecto de Datos desarrollado con los datos de señales ADS-B de aviones

#### OBJETIVO: encontrar el orden de despegue de los aviones

### INDICE
- [🚀 Ejecutar el proyecto](#ejecutar-el-proyecto)
- [💡 Estructura del proyecto](#estructura-del-proyecto)
- [🗂️ Datos](#)
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

**Ejecución dashboards interactivos**
Los dashboards se ejecutan desde el **directorio raíz**.
```bash
$ uv run src/visualization/aire_tierra/dashboard.py
$ uv run src/visualization/despegues/dashboard.py
$ uv run src/visualization/mapa/dashboard.py
```

### 💡 Estructura del proyecto
```
|- assets: contiene el conjunto de recursos globales del
|    proyecto imágenes, capturas, js usadas, como iconos.
|
|- data: contiene los datos preprocesados, listos para usar.
|    |
|    |- ex1: datos de tiempos de espera y aviones en aire y tierra
|    |- ex2: datos para la visualización del mapa
|
|- docs: contiene la documentación,
|   junto con algunos problemas que pueden surgir.
|
|- mapas: guarda los .html las visualizaciones del mapa
|
|-  src: contiene todo el código, principalmente 
|       archivos que sirven para transformar y visualizar los datos
    |
    |- exploracion: notebooks con análisis de los datos generados,
    |   lo usamos para hacer pruebas antes de tomar
    |   decisiones o sacar conclusiones sobre los resultados
    |
    |- utils: módulo para preprocesar más fácilmente,
    |   las clases se usaron al inicio del desarrollo
    |   y representan cada tipo de mensaje.
    |
    |- visualization: código de visualizaciones de datos.
    |   |
    |   |- carpetas (aire_tierra, despegues, mapa)
    |       |- assets - carpeta con los archivos necesarios 
    |       |   para la visualización, como estilos, imágenes...
    |       |- dasboard.py - dashboard interactivo para 
    |       |   el análisis de las gráficas
    |       |- (notebook jupyter) - visualizaciones en el notebook
    |       |   contiene comentarios con gráficas
    |
    |- main.py: archivo para iterar sobre los datos crudos,
    |   donde cada fila representa características concretas,
    |   y transformarlos en filas con todas las posibles características.
    |   Hace uso de utils para el preprocesamiento.
    |
    |- procesado_aire_tierra.py: archivo para sacar los datos
    |   de aviones en tierra y en aire.
    |
    |- procesado_mapa.py: archivo para sacar las posiciones
    |   de los aviones para visualizarlo en el mapa.
    |
    |- procesado_tiempos_espera_1.py: archivo para la primera parte del 
    |    procesado de tiempos de espera, se sacan las columnas necesarias.
    |
    |- procesado_tiempos_espera_2.py: archivo para la segunda parte del procesado
    | de tiempos de espera, se filtran justo los momentos de espera y los despegues.
```
### 🛠️ Para desarrolladores
#### Documentación consultada

1. Problema original: https://mode-s.org/1090mhz/

2. PDF con más detalles sobre ADS-B: https://airmetar.main.jp/radio/ADS-B%20Decoding%20Guide.pdf

3. Documentación pyModeS: https://mode-s.org/pymodes/api/index.html