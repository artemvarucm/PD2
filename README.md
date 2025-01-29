## Proyecto de Datos desarrollado con los datos de señales ADS-B de aviones

#### OBJETIVO: encontrar el orden de despegue de los aviones

### INDICE
- [🚀 Ejecutar el proyecto](#ejecutar-el-proyecto)
- [💡 Estructura del proyecto](#)
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
Ejecución del notebook seleccionando el entorno virtual seleccionado

### 🛠️ Para desarrolladores
#### Documentación consultada

1. Problema original: https://mode-s.org/1090mhz/

2. PDF con más detalles sobre ADS-B: https://airmetar.main.jp/radio/ADS-B%20Decoding%20Guide.pdf

3. Documentación pyModeS: https://mode-s.org/pymodes/api/index.html