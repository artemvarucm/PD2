# Dashboard de Análisis de Tiempos de Espera

Este dashboard interactivo permite visualizar y analizar los tiempos de espera de aeronaves en diferentes puntos de holding del aeropuerto.

## Características

- **Filtrado interactivo:** Filtra los datos por tipo de aeronave, punto de holding y rango de fechas.
- **Estadísticas resumidas:** Muestra métricas clave como tiempo promedio, máximo, mínimo y mediano de espera.
- **Visualizaciones detalladas:**
  - Distribución de tiempos de espera (histograma)
  - Comparación por tipo de aeronave (boxplot)
  - Análisis temporal por hora y fecha (mapa de calor)
  - Tiempos promedio por punto de holding (gráfico de barras)
  - Serie temporal de tiempos de espera a lo largo del tiempo
  - Comparación entre tiempos de espera reales y predicciones
- **Modo de Visualización Ampliada:** Haz clic en cualquier gráfico para abrirlo en una ventana completa con filtros propios, permitiendo un análisis más detallado.

## Requisitos

- Python 3.7 o superior
- Dash
- Plotly
- Pandas
- NumPy

## Instalación

1. Asegúrate de tener todas las dependencias instaladas:

```bash
pip install dash plotly pandas numpy
```

2. Coloca el archivo de datos (CSV) en la misma carpeta que el dashboard o actualiza la ruta en el código.

## Uso

1. Ejecuta el dashboard con el script:

```bash
python run_dashboard.py
```

2. Abre tu navegador y ve a `http://127.0.0.1:8050/` para ver el dashboard.

3. Utiliza los controles de filtrado en la parte superior para personalizar el análisis.

4. **Nuevo:** Haz clic en cualquier gráfico para ampliarlo y visualizarlo en pantalla completa. En este modo ampliado, también puedes aplicar filtros adicionales específicos para ese gráfico.

## Estructura del Dashboard

El dashboard está organizado en secciones:

1. **Filtros:** Selección de tipo de aeronave, punto de holding y rango de fechas.
2. **Estadísticas resumidas:** Datos clave sobre los vuelos filtrados.
3. **Análisis de distribución:** Histograma y boxplot de los tiempos de espera.
4. **Análisis espacial y temporal:** Mapas de calor y gráficos de barras para analizar patrones.
5. **Series temporales:** Evolución de los tiempos de espera a lo largo del tiempo.
6. **Evaluación de predicciones:** Comparación entre los valores reales y predichos.
7. **Modo Ampliado:** Ventana modal que se abre al hacer clic en un gráfico para una visualización detallada.

## Personalización

- Para modificar el estilo visual, edita el archivo `assets/styles.css`.
- Para añadir o modificar visualizaciones, edita el archivo `dashboard_tiempos_espera.py`.

## Notas

- Este dashboard asume que las columnas específicas (como 'tiempo_espera', 'holding_point_*', etc.) existen en el archivo de datos.
- Si la columna 'prediccion_tiempo_espera' está presente, se mostrarán visualizaciones adicionales comparando las predicciones con los valores reales.
- Para cerrar la vista ampliada de un gráfico, haz clic en el botón "×" en la esquina superior derecha del modal o en cualquier área fuera del modal. 