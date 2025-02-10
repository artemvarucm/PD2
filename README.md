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

Instalación uv:
1. pip install uv
2. localizar donde se ha instalado el paquete(probablemente en C:\Users\TuUsuario\AppData\Local\Packages\PythonSoftwareFoundation\LocalCache\local-packages\Python311(o la versión de la que se disponga)\site-packages\uv
3. añadir esta dirección en el path en las variables de entorno


```bash
$ uv sync
$ source .venv/bin/activate
```
**Ejecución del notebook seleccionando el entorno virtual .venv**

### 💡 Estructura del proyecto
```
|- assets: contiene el conjunto de imágenes usadas, como iconos.
|
|- data: contiene los datos preprocesados, listos para usar.
|
|- docs: contiene la documentación, junto con algunos problemas que pueden surgir.
|
|- mapas: contiene las visualizaciones del mapa
|
|-  src: contiene todo el código, principalmente archivos que sirven para transformar y visualizar los datos
    |
    |- exploracion: notebooks con análisis de los datos generados
    |
    |- utils: módulo para preprocesar más fácilmente.
    |
    |- visualization: código de visualizaciones de datos.
    |
    |- main.py: archivo para iterar sobre los datos crudos, donde cada fila representa características concretas, y transformarlos en filas con todas las posibles características. Hace uso de utils para el preprocesamiento.
    |
    |- preprocessing.py: archivo para sacar los datos de aviones en tierra y en aire.

```
### 🛠️ Para desarrolladores
#### Documentación consultada

1. Problema original: https://mode-s.org/1090mhz/

2. PDF con más detalles sobre ADS-B: https://airmetar.main.jp/radio/ADS-B%20Decoding%20Guide.pdf

3. Documentación pyModeS: https://mode-s.org/pymodes/api/index.html