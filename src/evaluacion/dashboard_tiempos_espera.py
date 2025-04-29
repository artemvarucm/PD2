import dash
from dash import Dash, html, dcc, callback, Output, Input, State, ctx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import os
import json

# Cargar el dataset
# Ajusta la ruta según dónde tengas tu archivo de datos
# Asumimos que está en la misma carpeta o especifica la ruta correcta
df = pd.read_csv('/Users/alewar/Documents/Universidad/Tercero/PD2/PD2/src/evaluacion/predicciones_xgb_with_queue_final.csv')
df['prediccion_tiempo_espera'] = df['pred']

# Asegurar que la carpeta assets existe
if not os.path.exists('assets'):
    os.makedirs('assets')

# Inicialización de la aplicación Dash
app = Dash(__name__, assets_folder='assets', suppress_callback_exceptions=True)

# Lista de gráficos para poder hacer referencia a ellos
graph_ids = [
    'tiempo-espera-histogram',
    'boxplot-aircraft-type',
    'heatmap-hora-fecha',
    'barplot-holding-point',
    'time-series-plot',
    'prediccion-vs-real'
]

# Función para crear un contenedor de gráfico con botón de ampliación
def create_graph_container(graph_id, title):
    return html.Div([
        html.Div([
            html.H4(title, className="graph-title"),
            html.Button("Ver en grande", id=f"btn-{graph_id}", className="btn-expand")
        ], className="graph-header"),
        dcc.Graph(
            id=graph_id,
            config={'displayModeBar': True},
            figure={}
        )
    ], className="graph-container")

# Configuración del layout principal del dashboard
app.layout = html.Div([
    html.H1("Dashboard de Análisis de Tiempos de Espera en Puntos de Holding", 
            style={'textAlign': 'center', 'color': '#503D36', 'fontSize': 24}),
    
    # Sección de filtros
    html.Div([
        html.Div([
            html.Label('Filtrar por Tipo de Aeronave:'),
            dcc.Dropdown(
                id='aircraft-type-dropdown',
                options=[
                    {'label': 'Todos', 'value': 'all'},
                    {'label': 'Heavy (larger than 136000 kg)', 'value': 'Heavy (larger than 136000 kg)'},
                    {'label': 'High vortex aircraft', 'value': 'High vortex aircraft'},
                    {'label': 'Light (less than 7000 kg)', 'value': 'Light (less than 7000 kg)'},
                    {'label': 'Medium 1 (between 7000 kg and 34000 kg)', 'value': 'Medium 1 (between 7000 kg and 34000 kg)'},
                    {'label': 'Medium 2 (between 34000 kg to 136000 kg)', 'value': 'Medium 2 (between 34000 kg to 136000 kg)'}
                ],
                value='all',
                style={'width': '100%'}
            ),
        ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),
        
        html.Div([
            html.Label('Filtrar por Holding Point:'),
            dcc.Dropdown(
                id='holding-point-dropdown',
                options=[
                    {'label': 'Todos', 'value': 'all'},
                ] + [{'label': col.replace('holding_point_', ''), 'value': col.replace('holding_point_', '')} 
                     for col in df.columns if col.startswith('holding_point_')],
                value='all',
                style={'width': '100%'}
            ),
        ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),
        
        html.Div([
            html.Label('Rango de Fechas:'),
            dcc.DatePickerRange(
                id='date-range-picker',
                min_date_allowed=pd.to_datetime(df['fecha_despegue']).min(),
                max_date_allowed=pd.to_datetime(df['fecha_despegue']).max(),
                start_date=pd.to_datetime(df['fecha_despegue']).min(),
                end_date=pd.to_datetime(df['fecha_despegue']).max(),
                style={'width': '100%'}
            ),
        ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),
    ], style={'display': 'flex'}),
    
    # Sección de estadísticas resumen
    html.Div([
        html.Div(id='stats-container', className='stats-container')
    ]),
    
    # Primera fila de gráficos
    html.Div([
        # Gráfico de distribución de tiempos de espera
        html.Div([
            create_graph_container('tiempo-espera-histogram', 'Distribución de Tiempos de Espera')
        ], style={'width': '50%', 'display': 'inline-block'}),
        
        # Boxplot por tipo de aeronave
        html.Div([
            create_graph_container('boxplot-aircraft-type', 'Tiempos de Espera por Tipo de Aeronave')
        ], style={'width': '50%', 'display': 'inline-block'}),
    ], style={'display': 'flex'}),
    
    # Segunda fila de gráficos
    html.Div([
        # Mapa de calor por hora y fecha
        html.Div([
            create_graph_container('heatmap-hora-fecha', 'Tiempo de Espera Promedio por Hora y Fecha')
        ], style={'width': '50%', 'display': 'inline-block'}),
        
        # Tiempos de espera promedio por punto de holding
        html.Div([
            create_graph_container('barplot-holding-point', 'Tiempo de Espera Promedio por Punto de Holding')
        ], style={'width': '50%', 'display': 'inline-block'}),
    ], style={'display': 'flex'}),
    
    # Tercera fila de gráficos
    html.Div([
        # Serie temporal de tiempos de espera
        html.Div([
            create_graph_container('time-series-plot', 'Evolución del Tiempo de Espera por Día')
        ], style={'width': '50%', 'display': 'inline-block'}),
        
        # Comparación entre predicción y valor real
        html.Div([
            create_graph_container('prediccion-vs-real', 'Comparación: Tiempo de Espera Real vs Predicción')
        ], style={'width': '50%', 'display': 'inline-block'}),
    ], style={'display': 'flex'}),
    
    # Modal para mostrar gráfico ampliado con diseño mejorado
    html.Div([
        html.Div([
            html.Div([
                html.Span("×", id="close-modal", className="close-btn"),
                html.H3(id="modal-title", children="Gráfico Ampliado"),
                
                # Nueva estructura con filtros a un lado y el gráfico al otro
                html.Div([
                    # Panel lateral para filtros
                    html.Div([
                        html.Div([
                            html.H4("Filtros", className="filter-title"),
                            
                            html.Div([
                                html.Label('Tipo de Aeronave:'),
                                dcc.Dropdown(
                                    id='modal-aircraft-type-dropdown',
                                    options=[
                                        {'label': 'Todos', 'value': 'all'},
                                        {'label': 'Heavy (larger than 136000 kg)', 'value': 'Heavy (larger than 136000 kg)'},
                                        {'label': 'High vortex aircraft', 'value': 'High vortex aircraft'},
                                        {'label': 'Light (less than 7000 kg)', 'value': 'Light (less than 7000 kg)'},
                                        {'label': 'Medium 1 (between 7000 kg and 34000 kg)', 'value': 'Medium 1 (between 7000 kg and 34000 kg)'},
                                        {'label': 'Medium 2 (between 34000 kg to 136000 kg)', 'value': 'Medium 2 (between 34000 kg to 136000 kg)'}
                                    ],
                                    value='all',
                                    style={'width': '100%', 'marginBottom': '15px'}
                                ),
                            ], className="filter-section"),
                            
                            html.Div([
                                html.Label('Punto de Holding:'),
                                dcc.Dropdown(
                                    id='modal-holding-point-dropdown',
                                    options=[
                                        {'label': 'Todos', 'value': 'all'},
                                    ] + [{'label': col.replace('holding_point_', ''), 'value': col.replace('holding_point_', '')} 
                                        for col in df.columns if col.startswith('holding_point_')],
                                    value='all',
                                    style={'width': '100%', 'marginBottom': '15px'}
                                ),
                            ], className="filter-section"),
                            
                            html.Div([
                                html.Label('Rango de Fechas:'),
                                dcc.DatePickerRange(
                                    id='modal-date-range-picker',
                                    min_date_allowed=pd.to_datetime(df['fecha_despegue']).min(),
                                    max_date_allowed=pd.to_datetime(df['fecha_despegue']).max(),
                                    start_date=pd.to_datetime(df['fecha_despegue']).min(),
                                    end_date=pd.to_datetime(df['fecha_despegue']).max(),
                                    style={'width': '100%'}
                                ),
                            ], className="filter-section"),
                        ], className="filter-panel-content")
                    ], className="filter-panel"),
                    
                    # Área del gráfico
                    html.Div([
                        html.Div(id="modal-stats-prediction", className="prediction-stats"),
                        html.Div([
                                # Añadir los botones directamente en el layout inicial
                                html.Div([
                                    html.H5("Análisis Adicionales:", style={"marginTop": "15px"}),
                                    html.Div([
                                        html.Button("Ocultar", id="btn-advanced-hide", className="analysis-button"),
                                        html.Button("Por Categoría de Error", id="btn-error-analysis", className="analysis-button"),
                                        html.Button("Por Tiempo del Día", id="btn-time-analysis", className="analysis-button"),
                                        html.Button("Residuales", id="btn-residuals", className="analysis-button")
                                    ], className="analysis-buttons")
                                ], className="prediction-analysis-controls"),
                                # Área para gráficos adicionales
                                html.Div(id="additional-analysis-area", className="additional-analysis-area")
                            ], id="prediction-analysis-container", style={"display": "none"}),
                        dcc.Graph(id='modal-graph', style={'height': '75vh'})
                    ], className="graph-panel"),
                ], className="modal-flex-container"),
                
                # Store para guardar qué gráfico está activo
                dcc.Store(id='active-graph', data=None)
            ], className="modal-content")
        ], id="graph-modal", className="modal")
    ]),
])

# Función para filtrar el dataframe según las selecciones
def filter_dataframe(aircraft_type, holding_point, start_date, end_date):
    filtered_df = df.copy()
    
    # Convertir fechas a formato datetime si no lo están
    if not pd.api.types.is_datetime64_dtype(filtered_df['fecha_despegue']):
        filtered_df['fecha_despegue'] = pd.to_datetime(filtered_df['fecha_despegue'])
    
    # Filtrar por rango de fechas
    filtered_df = filtered_df[(filtered_df['fecha_despegue'] >= start_date) & 
                              (filtered_df['fecha_despegue'] <= end_date)]
    
    # Filtrar por tipo de aeronave si no es 'all'
    if aircraft_type != 'all':
        filtered_df = filtered_df[filtered_df['aircraft_type'] == aircraft_type]
    
    # Filtrar por holding point si no es 'all'
    if holding_point != 'all':
        filtered_df = filtered_df[filtered_df[f'holding_point_{holding_point}'] == 1]
    
    return filtered_df

# Callback para los botones de ampliación de gráficos
@callback(
    [Output('graph-modal', 'style'),
     Output('active-graph', 'data'),
     Output('modal-title', 'children'),
     Output('modal-aircraft-type-dropdown', 'value'),
     Output('modal-holding-point-dropdown', 'value'),
     Output('modal-date-range-picker', 'start_date'),
     Output('modal-date-range-picker', 'end_date'),
     Output('prediction-analysis-container', 'style')],
    [Input(f'btn-{graph_id}', 'n_clicks') for graph_id in graph_ids],
    [State('aircraft-type-dropdown', 'value'),
     State('holding-point-dropdown', 'value'),
     State('date-range-picker', 'start_date'),
     State('date-range-picker', 'end_date')]
)
def open_modal(*args):
    # Los últimos 4 args son los states
    current_aircraft_type = args[-4]
    current_holding_point = args[-3]
    current_start_date = args[-2]
    current_end_date = args[-1]
    
    # Los primeros args son los clicks de los botones
    button_clicks = args[:-4]
    
    # Verificar qué botón fue clickeado
    triggered = ctx.triggered_id
    
    if triggered is None:
        return {'display': 'none'}, None, "Gráfico Ampliado", current_aircraft_type, current_holding_point, current_start_date, current_end_date, {"display": "none"}
    
    # Extraer el ID del gráfico del ID del botón (quitar el prefijo 'btn-')
    if triggered and triggered.startswith('btn-'):
        graph_id = triggered[4:]  # Quita 'btn-' del principio
    else:
        return {'display': 'none'}, None, "Gráfico Ampliado", current_aircraft_type, current_holding_point, current_start_date, current_end_date, {"display": "none"}
    
    # Títulos para cada gráfico
    graph_titles = {
        'tiempo-espera-histogram': 'Distribución de Tiempos de Espera',
        'boxplot-aircraft-type': 'Tiempos de Espera por Tipo de Aeronave/Punto de Holding',
        'heatmap-hora-fecha': 'Tiempo de Espera Promedio por Hora y Fecha',
        'barplot-holding-point': 'Tiempo de Espera Promedio por Punto de Holding',
        'time-series-plot': 'Evolución del Tiempo de Espera por Día',
        'prediccion-vs-real': 'Comparación: Tiempo de Espera Real vs Predicción'
    }
    
    # Si es la comparación de predicción, mostrar panel adicional
    prediction_panel_style = {"display": "block"} if graph_id == 'prediccion-vs-real' else {"display": "none"}
    
    # Mostrar modal con el gráfico seleccionado
    return {'display': 'block'}, graph_id, graph_titles.get(graph_id, "Gráfico Ampliado"), current_aircraft_type, current_holding_point, current_start_date, current_end_date, prediction_panel_style

# Callback para cerrar el modal
@callback(
    Output('graph-modal', 'style', allow_duplicate=True),
    Input('close-modal', 'n_clicks'),
    prevent_initial_call=True
)
def close_modal(n_clicks):
    if n_clicks:
        return {'display': 'none'}
    return {'display': 'none'}

# Callback para actualizar el gráfico del modal
@callback(
    [Output('modal-graph', 'figure'),
     Output('modal-stats-prediction', 'children')],
    [Input('active-graph', 'data'),
     Input('modal-aircraft-type-dropdown', 'value'),
     Input('modal-holding-point-dropdown', 'value'),
     Input('modal-date-range-picker', 'start_date'),
     Input('modal-date-range-picker', 'end_date')]
)
def update_modal_graph(active_graph, aircraft_type, holding_point, start_date, end_date):
    if active_graph is None:
        return {}, []
    
    # Convertir fechas a formato datetime
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    # Filtrar el dataframe
    filtered_df = filter_dataframe(aircraft_type, holding_point, start_date, end_date)
    
    # Estadísticas para el panel de predicción (inicialmente vacío)
    prediction_stats = []
    
    # Crear la figura según el gráfico activo
    if active_graph == 'tiempo-espera-histogram':
        fig = px.histogram(
            filtered_df, 
            x='tiempo_espera',
            nbins=30,
            title='Distribución de Tiempos de Espera',
            labels={'tiempo_espera': 'Tiempo de Espera (segundos)', 'count': 'Frecuencia'},
            color_discrete_sequence=['#4C78A8']
        )
        
        fig.update_layout(
            xaxis_title='Tiempo de Espera (segundos)',
            yaxis_title='Frecuencia',
            bargap=0.1,
            height=700
        )
    
    elif active_graph == 'boxplot-aircraft-type':
        if aircraft_type != 'all':
            # Identificar los holding points activos
            holding_cols = [col for col in filtered_df.columns if col.startswith('holding_point_') and filtered_df[col].sum() > 0]
            
            # Crear un dataframe con el holding point como columna categórica
            plot_df = filtered_df.copy()
            plot_df['holding_point'] = 'Ninguno'
            
            for col in holding_cols:
                point_name = col.replace('holding_point_', '')
                plot_df.loc[plot_df[col] == 1, 'holding_point'] = point_name
            
            # Filtrar solo las filas con un holding point asignado
            plot_df = plot_df[plot_df['holding_point'] != 'Ninguno']
            
            # Crear boxplot
            fig = px.box(
                plot_df,
                x='holding_point',
                y='tiempo_espera',
                title=f'Tiempos de Espera por Punto de Holding para {aircraft_type}',
                labels={'holding_point': 'Punto de Holding', 'tiempo_espera': 'Tiempo de Espera (segundos)'},
                color='holding_point'
            )
        else:
            # Mostrar boxplot por tipo de aeronave
            fig = px.box(
                filtered_df,
                x='aircraft_type',
                y='tiempo_espera',
                title='Tiempos de Espera por Tipo de Aeronave',
                labels={'aircraft_type': 'Tipo de Aeronave', 'tiempo_espera': 'Tiempo de Espera (segundos)'},
                color='aircraft_type'
            )
        
        fig.update_layout(
            xaxis={'tickangle': -45},
            margin={'b': 100},
            height=700
        )
    
    elif active_graph == 'heatmap-hora-fecha':
        # Asegurarse de que tenemos columnas de hora y fecha
        if not pd.api.types.is_datetime64_dtype(filtered_df['fecha_despegue']):
            filtered_df['fecha_despegue'] = pd.to_datetime(filtered_df['fecha_despegue'])
        
        # Crear una tabla pivote con los tiempos de espera promedio por hora y fecha
        pivot_df = filtered_df.pivot_table(
            index='fecha_despegue',
            columns='hora_despegue',
            values='tiempo_espera',
            aggfunc='mean'
        ).fillna(0)
        
        # Crear mapa de calor
        fig = px.imshow(
            pivot_df,
            labels=dict(x='Hora del Día', y='Fecha', color='Tiempo de Espera (segundos)'),
            title='Tiempo de Espera Promedio por Hora y Fecha',
            color_continuous_scale='viridis'
        )
        
        fig.update_layout(
            xaxis_title='Hora del Día',
            yaxis_title='Fecha',
            coloraxis_colorbar=dict(title='Tiempo (s)'),
            height=700
        )
    
    elif active_graph == 'barplot-holding-point':
        # Identificar los holding points activos
        holding_cols = [col for col in filtered_df.columns if col.startswith('holding_point_')]
        
        # Calcular el tiempo promedio por holding point
        holding_times = []
        for col in holding_cols:
            point_name = col.replace('holding_point_', '')
            avg_time = filtered_df[filtered_df[col] == 1]['tiempo_espera'].mean()
            if not pd.isna(avg_time):
                holding_times.append({'holding_point': point_name, 'avg_tiempo': avg_time, 'count': filtered_df[col].sum()})
        
        # Crear un dataframe con los resultados
        holding_df = pd.DataFrame(holding_times)
        
        if len(holding_df) > 0:
            # Ordenar por tiempo promedio
            holding_df = holding_df.sort_values('avg_tiempo', ascending=False)
            
            # Usar go.Figure en lugar de px.bar para evitar el error de template
            fig = go.Figure()
            
            # Añadir barras con colores basados en la cuenta
            max_count = holding_df['count'].max()
            min_count = holding_df['count'].min()
            
            # Normalizar los valores de conteo para el color
            normalized_counts = (holding_df['count'] - min_count) / (max_count - min_count) if max_count > min_count else [0.5] * len(holding_df)
            colorscale = px.colors.sequential.Viridis
            
            # Añadir barras con texto
            for i, row in holding_df.iterrows():
                # Calcular el color basado en la cuenta normalizada
                color_idx = int(normalized_counts.iloc[i] * (len(colorscale) - 1))
                color = colorscale[color_idx]
                
                fig.add_trace(go.Bar(
                    x=[row['holding_point']],
                    y=[row['avg_tiempo']],
                    name=row['holding_point'],
                    marker_color=color,
                    text=f"Vuelos: {int(row['count'])}",
                    textposition='auto',
                    hoverinfo='text',
                    hovertext=f"Punto: {row['holding_point']}<br>Promedio: {row['avg_tiempo']:.2f}s<br>Vuelos: {int(row['count'])}"
                ))
            
            fig.update_layout(
                title='Tiempo de Espera Promedio por Punto de Holding',
                xaxis={'title': 'Punto de Holding', 'tickangle': -45},
                yaxis={'title': 'Tiempo Promedio (segundos)'},
                showlegend=False  # Ocultar leyenda ya que cada barra tiene su propio nombre
            )
            
            # Añadir una barra de color como referencia
            fig.update_layout(
                coloraxis=dict(
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(
                        title='Cantidad de Vuelos',
                        x=1.02,
                        y=0.5
                    )
                )
            )
        else:
            # Si no hay datos, mostrar un gráfico vacío
            fig = go.Figure()
            fig.update_layout(
                title='No hay datos suficientes para mostrar',
                xaxis_title='Punto de Holding',
                yaxis_title='Tiempo Promedio (segundos)'
            )
    
    elif active_graph == 'time-series-plot':
        # Asegurarse de que tenemos columnas de hora y fecha
        if not pd.api.types.is_datetime64_dtype(filtered_df['fecha_despegue']):
            filtered_df['fecha_despegue'] = pd.to_datetime(filtered_df['fecha_despegue'])
        
        # Crear una columna de fecha-hora combinada
        filtered_df['datetime'] = pd.to_datetime(filtered_df['despegue'])
        
        # Ordenar por fecha-hora
        filtered_df = filtered_df.sort_values('datetime')
        
        # Agregar por día y calcular estadísticas
        daily_stats = filtered_df.groupby('fecha_despegue').agg(
            avg_tiempo=('tiempo_espera', 'mean'),
            max_tiempo=('tiempo_espera', 'max'),
            min_tiempo=('tiempo_espera', 'min'),
            count=('tiempo_espera', 'count')
        ).reset_index()
        
        # Crear gráfico de línea
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=daily_stats['fecha_despegue'],
            y=daily_stats['avg_tiempo'],
            mode='lines+markers',
            name='Promedio',
            line=dict(color='blue', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=daily_stats['fecha_despegue'],
            y=daily_stats['max_tiempo'],
            mode='lines',
            name='Máximo',
            line=dict(color='red', width=1, dash='dash')
        ))
        
        fig.add_trace(go.Scatter(
            x=daily_stats['fecha_despegue'],
            y=daily_stats['min_tiempo'],
            mode='lines',
            name='Mínimo',
            line=dict(color='green', width=1, dash='dash')
        ))
        
        # Añadir tamaño de muestra como texto
        for i, row in daily_stats.iterrows():
            fig.add_annotation(
                x=row['fecha_despegue'],
                y=row['avg_tiempo'],
                text=f"n={int(row['count'])}",
                showarrow=False,
                yshift=10
            )
        
        fig.update_layout(
            title='Evolución del Tiempo de Espera por Día',
            xaxis_title='Fecha',
            yaxis_title='Tiempo de Espera (segundos)',
            hovermode='closest',
            height=700
        )
    
    elif active_graph == 'prediccion-vs-real':
        # Verificar si tenemos columnas de predicción
        if 'prediccion_tiempo_espera' in filtered_df.columns:
            # Calcular métricas
            mae = np.mean(np.abs(filtered_df['tiempo_espera'] - filtered_df['prediccion_tiempo_espera']))
            mse = np.mean(np.square(filtered_df['tiempo_espera'] - filtered_df['prediccion_tiempo_espera']))
            rmse = np.sqrt(mse)
            
            # Calcular correlación
            correlation = np.corrcoef(filtered_df['tiempo_espera'], filtered_df['prediccion_tiempo_espera'])[0, 1]
            
            # Calcular porcentaje de predicciones dentro de umbrales
            within_10s = np.mean(np.abs(filtered_df['tiempo_espera'] - filtered_df['prediccion_tiempo_espera']) < 10) * 100
            within_30s = np.mean(np.abs(filtered_df['tiempo_espera'] - filtered_df['prediccion_tiempo_espera']) < 30) * 100
            within_60s = np.mean(np.abs(filtered_df['tiempo_espera'] - filtered_df['prediccion_tiempo_espera']) < 60) * 100
            
            # Categorizar el error como alto, medio o bajo
            filtered_df['error_abs'] = np.abs(filtered_df['tiempo_espera'] - filtered_df['prediccion_tiempo_espera'])
            filtered_df['error_category'] = pd.cut(
                filtered_df['error_abs'], 
                bins=[0, 10, 30, float('inf')], 
                labels=['Bajo (< 10s)', 'Medio (10-30s)', 'Alto (> 30s)']
            )
            
            # Ver si las predicciones tienden a sobrestimar o subestimar
            overestimation = np.mean(filtered_df['prediccion_tiempo_espera'] > filtered_df['tiempo_espera']) * 100
            underestimation = np.mean(filtered_df['prediccion_tiempo_espera'] < filtered_df['tiempo_espera']) * 100
            
            # Agregar estadísticas al panel de predicción
            prediction_stats = [
                html.H4("Métricas de Predicción", style={"marginTop": "20px"}),
                html.Div([
                    html.Div([
                        html.H5("Error Absoluto Medio:"),
                        html.P(f"{mae:.2f} segundos", className="metric-value")
                    ], className="prediction-metric"),
                    html.Div([
                        html.H5("RMSE:"),
                        html.P(f"{rmse:.2f} segundos", className="metric-value")
                    ], className="prediction-metric"),
                    html.Div([
                        html.H5("Correlación:"),
                        html.P(f"{correlation:.3f}", className="metric-value")
                    ], className="prediction-metric"),
                ], className="metrics-row"),
                
                html.Div([
                    html.Div([
                        html.H5("Precisión:"),
                        html.Div([
                            html.Span(f"± 10s: {within_10s:.1f}%", className="metric-badge", 
                                     style={"backgroundColor": "#4CAF50"}),
                            html.Span(f"± 30s: {within_30s:.1f}%", className="metric-badge", 
                                     style={"backgroundColor": "#FF9800"}),
                            html.Span(f"± 60s: {within_60s:.1f}%", className="metric-badge", 
                                     style={"backgroundColor": "#F44336"})
                        ], className="metric-badges")
                    ], className="prediction-metric wide"),
                ], className="metrics-row"),
                
                html.Div([
                    html.Div([
                        html.H5("Tendencia:"),
                        html.Div([
                            html.Span(f"Sobrestima: {overestimation:.1f}%", className="metric-badge", 
                                     style={"backgroundColor": "#4CAF50"}),
                            html.Span(f"Subestima: {underestimation:.1f}%", className="metric-badge", 
                                     style={"backgroundColor": "#F44336"})
                        ], className="metric-badges")
                    ], className="prediction-metric wide")
                ], className="metrics-row"),
                
                html.Hr(style={"margin": "15px 0"}),
            ]
            
            # Crear gráfico principal de dispersión mejorado
            fig = px.scatter(
                filtered_df,
                x='tiempo_espera',
                y='prediccion_tiempo_espera',
                color='error_category',
                color_discrete_map={
                    'Bajo (< 10s)': '#4CAF50', 
                    'Medio (10-30s)': '#FF9800', 
                    'Alto (> 30s)': '#F44336'
                },
                title='Comparación: Tiempo de Espera Real vs Predicción',
                labels={
                    'tiempo_espera': 'Tiempo Real (segundos)', 
                    'prediccion_tiempo_espera': 'Tiempo Predicho (segundos)',
                    'error_category': 'Categoría de Error'
                },
                opacity=0.7,
                hover_data=['error_abs', 'aircraft_type', 'fecha_despegue', 'hora_despegue']
            )
            
            # Añadir línea de identidad perfecta
            max_value = max(filtered_df['tiempo_espera'].max(), filtered_df['prediccion_tiempo_espera'].max())
            fig.add_trace(
                go.Scatter(
                    x=[0, max_value],
                    y=[0, max_value],
                    mode='lines',
                    name='Predicción Perfecta',
                    line=dict(color='black', width=1, dash='dash')
                )
            )
            
            # Añadir área de confianza de ±30 segundos
            fig.add_trace(
                go.Scatter(
                    x=[0, max_value],
                    y=[30, max_value + 30],
                    mode='lines',
                    name='+30 segundos',
                    line=dict(color='#FF9800', width=1, dash='dot'),
                    opacity=0.7
                )
            )
            
            fig.add_trace(
                go.Scatter(
                    x=[0, max_value],
                    y=[-30, max_value - 30],
                    mode='lines',
                    name='-30 segundos',
                    line=dict(color='#FF9800', width=1, dash='dot'),
                    opacity=0.7,
                    fill='tonexty',
                    fillcolor='rgba(255, 248, 225, 0.2)'  # Light yellow transparent fill
                )
            )
            
            # Añadir área de confianza de ±60 segundos
            fig.add_trace(
                go.Scatter(
                    x=[0, max_value],
                    y=[60, max_value + 60],
                    mode='lines',
                    name='+60 segundos',
                    line=dict(color='#F44336', width=1, dash='dot'),
                    opacity=0.7
                )
            )
            
            fig.add_trace(
                go.Scatter(
                    x=[0, max_value],
                    y=[-60, max_value - 60],
                    mode='lines',
                    name='-60 segundos',
                    line=dict(color='#F44336', width=1, dash='dot'),
                    opacity=0.7
                )
            )
            
            fig.update_layout(
                xaxis_title='Tiempo Real (segundos)',
                yaxis_title='Tiempo Predicho (segundos)',
                height=700,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center",
                    x=0.5
                )
            )
        else:
            # Si no hay datos de predicción, mostrar mensaje
            fig = go.Figure()
            fig.update_layout(
                title='No hay datos de predicción disponibles',
                xaxis_title='Tiempo Real (segundos)',
                yaxis_title='Tiempo Predicho (segundos)',
                height=700
            )
    
    else:
        # Si no hay un gráfico activo, mostrar un gráfico vacío
        fig = go.Figure()
        fig.update_layout(
            title='Selecciona un gráfico para visualizar',
            height=700
        )
    
    # Añadir margen adicional para mejor visualización
    fig.update_layout(
        margin=dict(l=50, r=50, t=80, b=50),
    )
    
    return fig, prediction_stats

# Callback para mostrar análisis adicionales de predicción
@callback(
    Output('additional-analysis-area', 'children'),
    [Input('btn-error-analysis', 'n_clicks'),
     Input('btn-advanced-hide', 'n_clicks'),
     Input('btn-time-analysis', 'n_clicks'),
     Input('btn-residuals', 'n_clicks')],
    [State('modal-aircraft-type-dropdown', 'value'),
     State('modal-holding-point-dropdown', 'value'),
     State('modal-date-range-picker', 'start_date'),
     State('modal-date-range-picker', 'end_date')]
)
def update_additional_analysis(error_clicks, hide_clicks, time_clicks, residuals_clicks, aircraft_type, holding_point, start_date, end_date):
    # Verificar qué botón fue clickeado
    triggered = ctx.triggered_id
    
    if not triggered:
        return []
    
    # Filtrar dataframe
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    filtered_df = filter_dataframe(aircraft_type, holding_point, start_date, end_date)
    
    # Verificar que tenemos datos de predicción
    if 'prediccion_tiempo_espera' not in filtered_df.columns:
        return html.Div("No hay datos de predicción disponibles para análisis adicional", style={"color": "red", "marginTop": "15px"})
    
    if triggered == 'advanced-hide':
        return None
    # Crear análisis según el botón presionado
    if triggered == 'btn-error-analysis':
        # Análisis de error por categoría 
        # (por tipo de aeronave, por holding point, etc.)
        
        # Calcular error por tipo de aeronave
        error_by_aircraft = filtered_df.groupby('aircraft_type').apply(
            lambda x: pd.Series({
                'mae': np.mean(np.abs(x['tiempo_espera'] - x['prediccion_tiempo_espera'])),
                'count': len(x),
            })
        ).reset_index()

        # Ordenar por error (mae) en orden descendente
        error_by_aircraft = error_by_aircraft.sort_values('mae', ascending=False)

        # Calcular error por holding point
        holding_cols = [col for col in filtered_df.columns if col.startswith('holding_point_')]
        error_by_holding = []

        for col in holding_cols:
            point_name = col.replace('holding_point_', '')
            df_subset = filtered_df[filtered_df[col] == 1]
            if len(df_subset) > 0:
                mae = np.mean(np.abs(df_subset['tiempo_espera'] - df_subset['prediccion_tiempo_espera']))
                error_by_holding.append({
                    'holding_point': point_name,
                    'mae': mae,
                    'count': len(df_subset)
                })

        error_by_holding = pd.DataFrame(error_by_holding)

        # Ordenar por error (mae) en orden descendente
        if len(error_by_holding) > 0:
            error_by_holding = error_by_holding.sort_values('mae', ascending=False)
        
        # Crear dos gráficos: error por tipo de aeronave y error por holding point
        fig1 = px.bar(
            error_by_aircraft,
            x='aircraft_type',
            y='mae',
            title='Error Medio por Tipo de Aeronave',
            labels={'aircraft_type': 'Tipo de Aeronave', 'mae': 'Error Absoluto Medio (s)'},
            color='count',
            color_continuous_scale='Viridis',
            text='count'
        )
        
        fig1.update_layout(
            xaxis={'tickangle': -45},
            height=400,  # Aumentar altura
            margin=dict(l=50, r=50, t=80, b=100)
        )
        
        # Crear gráfico de holding points solo si hay datos
        if len(error_by_holding) > 0:
            fig2 = px.bar(
                error_by_holding,
                x='holding_point',
                y='mae',
                title='Error Medio por Punto de Holding',
                labels={'holding_point': 'Punto de Holding', 'mae': 'Error Absoluto Medio (s)'},
                color='count',
                color_continuous_scale='Viridis',
                text='count'
            )
            
            fig2.update_layout(
                xaxis={'tickangle': -45},
                height=400,  # Aumentar altura
                margin=dict(l=50, r=50, t=80, b=50)
            )
            
            return [
                html.Div([
                    html.H4("Análisis de Error por Tipo de Aeronave y Punto de Holding", 
                           style={"textAlign": "center", "marginBottom": "20px", "color": "#4e73df"}),
                    # Envolver los gráficos en contenedores con márgenes más amplios
                    html.Div([
                        dcc.Graph(figure=fig1, style={"height": "400px"})
                    ], style={"marginBottom": "20px"}),
                    html.Div([
                        dcc.Graph(figure=fig2, style={"height": "400px"})
                    ])
                ], className="additional-analysis-panel")
            ]
        else:
            return [
                html.Div([
                    html.H4("Análisis de Error por Tipo de Aeronave", 
                           style={"textAlign": "center", "marginBottom": "20px", "color": "#4e73df"}),
                    html.Div([
                        dcc.Graph(figure=fig1, style={"height": "400px"})
                    ], style={"marginBottom": "20px"}),
                    html.Div("No hay suficientes datos para analizar por punto de holding", 
                            style={"color": "#5a5c69", "textAlign": "center", "padding": "20px"})
                ], className="additional-analysis-panel")
            ]
    
    elif triggered == 'btn-time-analysis':
        # Análisis de error por hora del día
        filtered_df['error'] = filtered_df['prediccion_tiempo_espera'] - filtered_df['tiempo_espera']
        filtered_df['error_abs'] = np.abs(filtered_df['error'])
        
        # Calcular error por hora
        error_by_hour = filtered_df.groupby('hora_despegue').agg(
            mae=('error_abs', 'mean'),
            mse=('error', lambda x: np.mean(np.square(x))),
            count=('error', 'count'),
            bias=('error', 'mean')  # Error medio (positivo = sobrestimación, negativo = subestimación)
        ).reset_index()
        
        # Calcular RMSE
        error_by_hour['rmse'] = np.sqrt(error_by_hour['mse'])
        
        # Crear figura con dos subplots
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=("Error por Hora del Día", "Tendencia de Sesgo por Hora"),
            vertical_spacing=0.25,  # Aumentar espacio entre gráficos
            specs=[[{"secondary_y": True}], [{}]]  # Añadir eje secundario al primer gráfico
        )
        
        # Añadir gráfico de barras para MAE y línea para RMSE
        fig.add_trace(
            go.Bar(
                x=error_by_hour['hora_despegue'],
                y=error_by_hour['mae'],
                name='MAE',
                marker_color='#4C78A8',
                opacity=0.7,
                text=error_by_hour['mae'].round(2),
                textposition='auto',
                hovertemplate='Hora: %{x}<br>MAE: %{y:.2f}s<br>Muestras: %{text}<extra></extra>'
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=error_by_hour['hora_despegue'],
                y=error_by_hour['rmse'],
                mode='lines+markers',
                name='RMSE',
                line=dict(color='#E45756', width=2),
                marker=dict(size=8)
            ),
            row=1, col=1
        )
        
        # Añadir línea de conteo como eje secundario
        fig.add_trace(
            go.Scatter(
                x=error_by_hour['hora_despegue'],
                y=error_by_hour['count'],
                mode='lines',
                name='Cantidad Vuelos',
                line=dict(color='#59A14F', width=1, dash='dot'),
                marker=dict(size=6)
            ),
            row=1, col=1,
            secondary_y=True
        )
        
        # Añadir gráfico de barras para sesgo (bias)
        colors = ['#4CAF50' if x < 0 else '#F44336' for x in error_by_hour['bias']]
        
        fig.add_trace(
            go.Bar(
                x=error_by_hour['hora_despegue'],
                y=error_by_hour['bias'],
                name='Sesgo',
                marker_color=colors,
                opacity=0.7,
                text=error_by_hour['count'],
                textposition='auto',
                hovertemplate='Hora: %{x}<br>Sesgo: %{y:.2f}s<br>Muestras: %{text}<extra></extra>'
            ),
            row=2, col=1
        )
        
        # Añadir línea de referencia en y=0
        fig.add_trace(
            go.Scatter(
                x=[min(error_by_hour['hora_despegue']), max(error_by_hour['hora_despegue'])],
                y=[0, 0],
                mode='lines',
                line=dict(color='black', width=1, dash='dash'),
                showlegend=False
            ),
            row=2, col=1
        )
        
        # Actualizar diseño
        fig.update_layout(
            height=700,  # Aumentar altura total
            margin=dict(l=50, r=50, t=80, b=50),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
            hovermode="x unified"
        )
        
        # Actualizar ejes x
        fig.update_xaxes(title="Hora del Día", tickmode='linear', dtick=1, row=1, col=1)
        fig.update_xaxes(title="Hora del Día", tickmode='linear', dtick=1, row=2, col=1)
        
        # Actualizar ejes y
        fig.update_yaxes(title="Error (segundos)", row=1, col=1)
        fig.update_yaxes(title="Vuelos", row=1, col=1, secondary_y=True)
        fig.update_yaxes(title="Sesgo (segundos)", row=2, col=1)
        
        return [
            html.Div([
                html.H4("Análisis de Error por Hora del Día", 
                       style={"textAlign": "center", "marginBottom": "20px", "color": "#4e73df"}),
                html.P("El sesgo positivo indica sobrestimación, negativo indica subestimación", 
                      style={"textAlign": "center", "color": "#5a5c69", "marginBottom": "15px"}),
                html.Div([
                    dcc.Graph(figure=fig, style={"height": "700px"})
                ])
            ], className="additional-analysis-panel")
        ]
    
    elif triggered == 'btn-residuals':
        # Análisis de residuales
        filtered_df['residual'] = filtered_df['tiempo_espera'] - filtered_df['prediccion_tiempo_espera']
        
        # Crear histograma de residuales
        fig1 = px.histogram(
            filtered_df,
            x='residual',
            title='Distribución de Residuales',
            labels={'residual': 'Residual (Tiempo Real - Predicción)'},
            opacity=0.7,
            nbins=30,
            color_discrete_sequence=['#4C78A8'],
            marginal='box'  # Añadir boxplot en el margen
        )
        
        fig1.add_vline(x=0, line_dash="dash", line_color="red")
        
        fig1.update_layout(
            height=400,  # Aumentar altura
            margin=dict(l=50, r=50, t=80, b=50),
            xaxis_title="Residual (segundos)"
        )
        
        # Crear gráfico de residuales vs valores ajustados
        fig2 = px.scatter(
            filtered_df,
            x='prediccion_tiempo_espera',
            y='residual',
            title='Residuales vs Valores Predichos',
            labels={
                'prediccion_tiempo_espera': 'Valor Predicho (segundos)',
                'residual': 'Residual (segundos)'
            },
            opacity=0.7,
            color='aircraft_type' if aircraft_type == 'all' else None,
            trendline='lowess',  # Añadir línea de tendencia
            trendline_color_override='red'
        )
        
        fig2.add_hline(y=0, line_dash="dash", line_color="red")
        
        fig2.update_layout(
            height=400,  # Aumentar altura
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        # Calcular algunas estadísticas de residuales
        residual_mean = filtered_df['residual'].mean()
        residual_std = filtered_df['residual'].std()
        residual_min = filtered_df['residual'].min()
        residual_max = filtered_df['residual'].max()
        
        # Calcular porcentaje de residuales dentro de ciertos rangos
        within_10s = np.mean(np.abs(filtered_df['residual']) < 10) * 100
        within_30s = np.mean(np.abs(filtered_df['residual']) < 30) * 100
        within_60s = np.mean(np.abs(filtered_df['residual']) < 60) * 100
        
        # Determinar si hay sesgo sistemático
        residual_skew = filtered_df['residual'].skew()
        bias_text = "Sesgo hacia subestimación (predicciones menores que valores reales)" if residual_mean > 0 else "Sesgo hacia sobrestimación (predicciones mayores que valores reales)"
        
        return [
            html.Div([
                html.H4("Análisis de Residuales", 
                       style={"textAlign": "center", "marginBottom": "20px", "color": "#4e73df"}),
                
                # Añadir un panel de resumen de residuales
                html.Div([
                    html.Div([
                        html.Div([
                            html.H5("Resumen de Residuales"),
                            html.P(f"Media: {residual_mean:.2f}s"),
                            html.P(f"Desviación: {residual_std:.2f}s"),
                            html.P(f"Mín/Máx: {residual_min:.2f}s / {residual_max:.2f}s"),
                            html.P(bias_text, style={"fontWeight": "bold"})
                        ], style={"flex": "1"}),
                        html.Div([
                            html.H5("Precisión de Residuales"),
                            html.Div([
                                html.Span(f"±10s: {within_10s:.1f}%", className="metric-badge", 
                                         style={"backgroundColor": "#4CAF50", "margin": "5px"}),
                                html.Span(f"±30s: {within_30s:.1f}%", className="metric-badge", 
                                         style={"backgroundColor": "#2196F3", "margin": "5px"}),
                                html.Span(f"±60s: {within_60s:.1f}%", className="metric-badge", 
                                         style={"backgroundColor": "#FF9800", "margin": "5px"})
                            ])
                        ], style={"flex": "1"})
                    ], style={"display": "flex", "margin": "10px 0 20px 0", "padding": "10px", 
                             "backgroundColor": "#f8f9fc", "borderRadius": "8px"})
                ]),
                
                # Contenedores para gráficos con mayor altura
                html.Div([
                    dcc.Graph(figure=fig1, style={"height": "400px"})
                ], style={"marginBottom": "20px"}),
                html.Div([
                    dcc.Graph(figure=fig2, style={"height": "400px"})
                ])
            ], className="additional-analysis-panel")
        ]
    
    return []

# Callbacks existentes para actualizar los gráficos normales
@callback(
    Output('stats-container', 'children'),
    [Input('aircraft-type-dropdown', 'value'),
     Input('holding-point-dropdown', 'value'),
     Input('date-range-picker', 'start_date'),
     Input('date-range-picker', 'end_date')]
)
def update_stats(aircraft_type, holding_point, start_date, end_date):
    # Convertir fechas a formato datetime
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    # Filtrar el dataframe
    filtered_df = filter_dataframe(aircraft_type, holding_point, start_date, end_date)
    
    # Calcular estadísticas
    avg_tiempo_espera = filtered_df['tiempo_espera'].mean()
    median_tiempo_espera = filtered_df['tiempo_espera'].median()
    max_tiempo_espera = filtered_df['tiempo_espera'].max()
    min_tiempo_espera = filtered_df['tiempo_espera'].min()
    total_vuelos = len(filtered_df)
    
    # Error medio entre predicción y valor real
    if 'prediccion_tiempo_espera' in filtered_df.columns:
        error_medio = np.mean(np.abs(filtered_df['tiempo_espera'] - filtered_df['prediccion_tiempo_espera']))
    else:
        error_medio = None
    
    # Crear componentes de estadísticas
    stats_boxes = [
        html.Div([
            html.H4("Total Vuelos"),
            html.P(f"{total_vuelos:,}")
        ], className='stat-box'),
        
        html.Div([
            html.H4("Tiempo Espera Promedio"),
            html.P(f"{avg_tiempo_espera:.2f} segundos")
        ], className='stat-box'),
        
        html.Div([
            html.H4("Tiempo Espera Mediano"),
            html.P(f"{median_tiempo_espera:.2f} segundos")
        ], className='stat-box'),
        
        html.Div([
            html.H4("Tiempo Espera Máximo"),
            html.P(f"{max_tiempo_espera:.2f} segundos")
        ], className='stat-box'),
        
        html.Div([
            html.H4("Tiempo Espera Mínimo"),
            html.P(f"{min_tiempo_espera:.2f} segundos")
        ], className='stat-box')
    ]
    
    # Agregar el error medio si está disponible
    if error_medio is not None:
        stats_boxes.append(
            html.Div([
                html.H4("Error Medio Predicción"),
                html.P(f"{error_medio:.2f} segundos")
            ], className='stat-box')
        )
    
    return html.Div(stats_boxes, style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'space-between'})

# Callback para el histograma de tiempos de espera
@callback(
    Output('tiempo-espera-histogram', 'figure'),
    [Input('aircraft-type-dropdown', 'value'),
     Input('holding-point-dropdown', 'value'),
     Input('date-range-picker', 'start_date'),
     Input('date-range-picker', 'end_date')]
)
def update_histogram(aircraft_type, holding_point, start_date, end_date):
    # Convertir fechas a formato datetime
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    # Filtrar el dataframe
    filtered_df = filter_dataframe(aircraft_type, holding_point, start_date, end_date)
    
    # Crear histograma
    fig = px.histogram(
        filtered_df, 
        x='tiempo_espera',
        nbins=30,
        title='Distribución de Tiempos de Espera',
        labels={'tiempo_espera': 'Tiempo de Espera (segundos)', 'count': 'Frecuencia'},
        color_discrete_sequence=['#4C78A8']
    )
    
    fig.update_layout(
        xaxis_title='Tiempo de Espera (segundos)',
        yaxis_title='Frecuencia',
        bargap=0.1
    )
    
    return fig

# Callback para el boxplot por tipo de aeronave
@callback(
    Output('boxplot-aircraft-type', 'figure'),
    [Input('aircraft-type-dropdown', 'value'),
     Input('holding-point-dropdown', 'value'),
     Input('date-range-picker', 'start_date'),
     Input('date-range-picker', 'end_date')]
)
def update_boxplot(aircraft_type, holding_point, start_date, end_date):
    # Convertir fechas a formato datetime
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    # Filtrar el dataframe
    filtered_df = filter_dataframe(aircraft_type, holding_point, start_date, end_date)
    
    # Si hay un solo tipo de aeronave seleccionado, mostrar boxplot por holding point
    if aircraft_type != 'all':
        # Identificar los holding points activos
        holding_cols = [col for col in filtered_df.columns if col.startswith('holding_point_') and filtered_df[col].sum() > 0]
        
        # Crear un dataframe con el holding point como columna categórica
        plot_df = filtered_df.copy()
        plot_df['holding_point'] = 'Ninguno'
        
        for col in holding_cols:
            point_name = col.replace('holding_point_', '')
            plot_df.loc[plot_df[col] == 1, 'holding_point'] = point_name
        
        # Filtrar solo las filas con un holding point asignado
        plot_df = plot_df[plot_df['holding_point'] != 'Ninguno']
        
        # Crear boxplot
        fig = px.box(
            plot_df,
            x='holding_point',
            y='tiempo_espera',
            title=f'Tiempos de Espera por Punto de Holding para {aircraft_type}',
            labels={'holding_point': 'Punto de Holding', 'tiempo_espera': 'Tiempo de Espera (segundos)'},
            color='holding_point'
        )
    else:
        # Mostrar boxplot por tipo de aeronave
        fig = px.box(
            filtered_df,
            x='aircraft_type',
            y='tiempo_espera',
            title='Tiempos de Espera por Tipo de Aeronave',
            labels={'aircraft_type': 'Tipo de Aeronave', 'tiempo_espera': 'Tiempo de Espera (segundos)'},
            color='aircraft_type'
        )
    
    fig.update_layout(
        xaxis={'tickangle': -45},
        margin={'b': 100}
    )
    
    return fig

# Callback para el mapa de calor por hora y fecha
@callback(
    Output('heatmap-hora-fecha', 'figure'),
    [Input('aircraft-type-dropdown', 'value'),
     Input('holding-point-dropdown', 'value'),
     Input('date-range-picker', 'start_date'),
     Input('date-range-picker', 'end_date')]
)
def update_heatmap(aircraft_type, holding_point, start_date, end_date):
    # Convertir fechas a formato datetime
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    # Filtrar el dataframe
    filtered_df = filter_dataframe(aircraft_type, holding_point, start_date, end_date)
    
    # Asegurarse de que tenemos columnas de hora y fecha
    if not pd.api.types.is_datetime64_dtype(filtered_df['fecha_despegue']):
        filtered_df['fecha_despegue'] = pd.to_datetime(filtered_df['fecha_despegue'])
    
    # Crear una tabla pivote con los tiempos de espera promedio por hora y fecha
    pivot_df = filtered_df.pivot_table(
        index='fecha_despegue',
        columns='hora_despegue',
        values='tiempo_espera',
        aggfunc='mean'
    ).fillna(0)
    
    # Crear mapa de calor
    fig = px.imshow(
        pivot_df,
        labels=dict(x='Hora del Día', y='Fecha', color='Tiempo de Espera (segundos)'),
        title='Tiempo de Espera Promedio por Hora y Fecha',
        color_continuous_scale='viridis'
    )
    
    fig.update_layout(
        xaxis_title='Hora del Día',
        yaxis_title='Fecha',
        coloraxis_colorbar=dict(title='Tiempo (s)')
    )
    
    return fig

# Callback para el gráfico de barras de holding points
@callback(
    Output('barplot-holding-point', 'figure'),
    [Input('aircraft-type-dropdown', 'value'),
     Input('holding-point-dropdown', 'value'),
     Input('date-range-picker', 'start_date'),
     Input('date-range-picker', 'end_date')]
)
def update_holding_barplot(aircraft_type, holding_point, start_date, end_date):
    # Convertir fechas a formato datetime
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    # Filtrar el dataframe
    filtered_df = filter_dataframe(aircraft_type, holding_point, start_date, end_date)
    
    # Identificar los holding points activos
    holding_cols = [col for col in filtered_df.columns if col.startswith('holding_point_')]
    
    # Calcular el tiempo promedio por holding point
    holding_times = []
    for col in holding_cols:
        point_name = col.replace('holding_point_', '')
        avg_time = filtered_df[filtered_df[col] == 1]['tiempo_espera'].mean()
        if not pd.isna(avg_time):
            holding_times.append({'holding_point': point_name, 'avg_tiempo': avg_time, 'count': filtered_df[col].sum()})
    
    # Crear un dataframe con los resultados
    holding_df = pd.DataFrame(holding_times)
    
    if len(holding_df) > 0:
        # Ordenar por tiempo promedio
        holding_df = holding_df.sort_values('avg_tiempo', ascending=False)
        
        # Usar go.Figure en lugar de px.bar para evitar el error de template
        fig = go.Figure()
        
        # Añadir barras con colores basados en la cuenta
        max_count = holding_df['count'].max()
        min_count = holding_df['count'].min()
        
        # Normalizar los valores de conteo para el color
        normalized_counts = (holding_df['count'] - min_count) / (max_count - min_count) if max_count > min_count else [0.5] * len(holding_df)
        colorscale = px.colors.sequential.Viridis
        
        # Añadir barras con texto
        for i, row in holding_df.iterrows():
            # Calcular el color basado en la cuenta normalizada
            color_idx = int(normalized_counts.iloc[i] * (len(colorscale) - 1))
            color = colorscale[color_idx]
            
            fig.add_trace(go.Bar(
                x=[row['holding_point']],
                y=[row['avg_tiempo']],
                name=row['holding_point'],
                marker_color=color,
                text=f"Vuelos: {int(row['count'])}",
                textposition='auto',
                hoverinfo='text',
                hovertext=f"Punto: {row['holding_point']}<br>Promedio: {row['avg_tiempo']:.2f}s<br>Vuelos: {int(row['count'])}"
            ))
        
        fig.update_layout(
            title='Tiempo de Espera Promedio por Punto de Holding',
            xaxis={'title': 'Punto de Holding', 'tickangle': -45},
            yaxis={'title': 'Tiempo Promedio (segundos)'},
            showlegend=False  # Ocultar leyenda ya que cada barra tiene su propio nombre
        )
        
        # Añadir una barra de color como referencia
        fig.update_layout(
            coloraxis=dict(
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(
                    title='Cantidad de Vuelos',
                    x=1.02,
                    y=0.5
                )
            )
        )
    else:
        # Si no hay datos, mostrar un gráfico vacío
        fig = go.Figure()
        fig.update_layout(
            title='No hay datos suficientes para mostrar',
            xaxis_title='Punto de Holding',
            yaxis_title='Tiempo Promedio (segundos)'
        )
    
    return fig

# Callback para la serie temporal
@callback(
    Output('time-series-plot', 'figure'),
    [Input('aircraft-type-dropdown', 'value'),
     Input('holding-point-dropdown', 'value'),
     Input('date-range-picker', 'start_date'),
     Input('date-range-picker', 'end_date')]
)
def update_time_series(aircraft_type, holding_point, start_date, end_date):
    # Convertir fechas a formato datetime
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    # Filtrar el dataframe
    filtered_df = filter_dataframe(aircraft_type, holding_point, start_date, end_date)
    
    # Asegurarse de que tenemos columnas de hora y fecha
    if not pd.api.types.is_datetime64_dtype(filtered_df['fecha_despegue']):
        filtered_df['fecha_despegue'] = pd.to_datetime(filtered_df['fecha_despegue'])
    
    # Crear una columna de fecha-hora combinada
    filtered_df['datetime'] = pd.to_datetime(filtered_df['despegue'])
    
    # Ordenar por fecha-hora
    filtered_df = filtered_df.sort_values('datetime')
    
    # Agregar por día y calcular estadísticas
    daily_stats = filtered_df.groupby('fecha_despegue').agg(
        avg_tiempo=('tiempo_espera', 'mean'),
        max_tiempo=('tiempo_espera', 'max'),
        min_tiempo=('tiempo_espera', 'min'),
        count=('tiempo_espera', 'count')
    ).reset_index()
    
    # Crear gráfico de línea
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=daily_stats['fecha_despegue'],
        y=daily_stats['avg_tiempo'],
        mode='lines+markers',
        name='Promedio',
        line=dict(color='blue', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=daily_stats['fecha_despegue'],
        y=daily_stats['max_tiempo'],
        mode='lines',
        name='Máximo',
        line=dict(color='red', width=1, dash='dash')
    ))
    
    fig.add_trace(go.Scatter(
        x=daily_stats['fecha_despegue'],
        y=daily_stats['min_tiempo'],
        mode='lines',
        name='Mínimo',
        line=dict(color='green', width=1, dash='dash')
    ))
    
    # Añadir tamaño de muestra como texto
    for i, row in daily_stats.iterrows():
        fig.add_annotation(
            x=row['fecha_despegue'],
            y=row['avg_tiempo'],
            text=f"n={int(row['count'])}",
            showarrow=False,
            yshift=10
        )
    
    fig.update_layout(
        title='Evolución del Tiempo de Espera por Día',
        xaxis_title='Fecha',
        yaxis_title='Tiempo de Espera (segundos)',
        hovermode='closest'
    )
    
    return fig

# Callback para comparación entre predicción y valor real
@callback(
    Output('prediccion-vs-real', 'figure'),
    [Input('aircraft-type-dropdown', 'value'),
     Input('holding-point-dropdown', 'value'),
     Input('date-range-picker', 'start_date'),
     Input('date-range-picker', 'end_date')]
)
def update_prediction_comparison(aircraft_type, holding_point, start_date, end_date):
    # Convertir fechas a formato datetime
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    # Filtrar el dataframe
    filtered_df = filter_dataframe(aircraft_type, holding_point, start_date, end_date)
    
    # Verificar si tenemos columnas de predicción
    if 'prediccion_tiempo_espera' in filtered_df.columns:
        # Calcular el error absoluto
        filtered_df['error_abs'] = np.abs(filtered_df['tiempo_espera'] - filtered_df['prediccion_tiempo_espera'])
        
        # Categorizar el error como alto, medio o bajo
        filtered_df['error_category'] = pd.cut(
            filtered_df['error_abs'], 
            bins=[0, 10, 30, float('inf')], 
            labels=['Bajo (< 10s)', 'Medio (10-30s)', 'Alto (> 30s)']
        )
        
        # Crear scatter plot
        fig = px.scatter(
            filtered_df,
            x='tiempo_espera',
            y='prediccion_tiempo_espera',
            title='Comparación: Tiempo de Espera Real vs Predicción',
            labels={'tiempo_espera': 'Tiempo Real (segundos)', 'prediccion_tiempo_espera': 'Tiempo Predicho (segundos)'},
            color='error_category',
            color_discrete_map={
                'Bajo (< 10s)': '#4CAF50', 
                'Medio (10-30s)': '#FF9800', 
                'Alto (> 30s)': '#F44336'
            },
            opacity=0.7
        )
        
        # Añadir línea de identidad perfecta
        max_value = max(filtered_df['tiempo_espera'].max(), filtered_df['prediccion_tiempo_espera'].max())
        fig.add_trace(
            go.Scatter(
                x=[0, max_value],
                y=[0, max_value],
                mode='lines',
                name='Predicción Perfecta',
                line=dict(color='black', width=1, dash='dash')
            )
        )
        
        # Añadir área de confianza de ±30 segundos
        fig.add_trace(
            go.Scatter(
                x=[0, max_value],
                y=[30, max_value + 30],
                mode='lines',
                name='+30 segundos',
                line=dict(color='#FF9800', width=1, dash='dot'),
                opacity=0.7
            )
        )
        
        fig.add_trace(
            go.Scatter(
                x=[0, max_value],
                y=[-30, max_value - 30],
                mode='lines',
                name='-30 segundos',
                line=dict(color='#FF9800', width=1, dash='dot'),
                opacity=0.7,
                fill='tonexty',
                fillcolor='rgba(255, 248, 225, 0.2)'  # Light yellow transparent fill
            )
        )
        
        # Añadir área de confianza de ±60 segundos
        fig.add_trace(
            go.Scatter(
                x=[0, max_value],
                y=[60, max_value + 60],
                mode='lines',
                name='+60 segundos',
                line=dict(color='#F44336', width=1, dash='dot'),
                opacity=0.7
            )
        )
        
        fig.add_trace(
            go.Scatter(
                x=[0, max_value],
                y=[-60, max_value - 60],
                mode='lines',
                name='-60 segundos',
                line=dict(color='#F44336', width=1, dash='dot'),
                opacity=0.7
            )
        )
        
        fig.update_layout(
            xaxis_title='Tiempo Real (segundos)',
            yaxis_title='Tiempo Predicho (segundos)',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
        )
    else:
        # Si no hay datos de predicción, mostrar mensaje
        fig = go.Figure()
        fig.update_layout(
            title='No hay datos de predicción disponibles',
            xaxis_title='Tiempo Real (segundos)',
            yaxis_title='Tiempo Predicho (segundos)'
        )
    
    return fig

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run_server(debug=False) 