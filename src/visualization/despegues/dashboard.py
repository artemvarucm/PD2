import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import plotly.express as px
import matplotlib
matplotlib.use('Agg')

df = pd.read_csv('data/ex1/eventos_espera_semana_nuevo.csv')

df['ultimo_parado'] = pd.to_datetime(df['ultimo_parado'])
df['despegue'] = pd.to_datetime(df['despegue'])
df['fecha_despegue'] = pd.to_datetime(df['fecha_despegue'])
df['hora_despegue'] = df['hora_despegue'].astype(int)

df = df[df["tiempo_espera"] < 1500]
df = df.dropna(subset=['runway'])

def clean_data(df):
    """Elimina registros duplicados cuando hay un despegue con el mismo ICAO en menos de 5 minutos."""
    
    indices_a_eliminar = []
    last_index = None
    lastIcao = None
    lastDespegue = None

    # Iteramos sobre el DataFrame usando iterrows() para obtener el índice de cada fila
    for idx, row in df.iterrows():
        if (lastIcao == row['ICAO']) and ((row['despegue'] - lastDespegue) < pd.Timedelta(minutes=5)):
            # Marcamos la fila anterior para eliminarla
            indices_a_eliminar.append(last_index)

        # Actualizamos las variables para la siguiente iteración
        lastIcao = row['ICAO']
        lastDespegue = row['despegue']
        last_index = idx

    # Eliminamos todas las filas marcadas de una sola vez
    df = df.drop(indices_a_eliminar).reset_index(drop=True)  # Reset index tras la eliminación
    return df

df = clean_data(df)


app = dash.Dash(__name__)


def generate_boxplot():
    fig = px.box(
        df, 
        x='aircraft_type', 
        y='tiempo_espera', 
        title='Boxplot de Tiempos de Espera por Tipo de Avión',
        labels={'aircraft_type': 'Tipo de Avión', 'tiempo_espera': 'Tiempo de Espera (segundos)'},
        color='aircraft_type',
    )

    fig.update_layout(
        xaxis=dict(title="Tipo de Avión", tickangle=-45),  # Rotar etiquetas del eje X
        yaxis=dict(title="Tiempo de Espera (segundos)"),
        showlegend=False  # No mostrar la leyenda de colores
    )

    return fig

def generate_heatmap(df):
    # Definir el orden de los días de la semana
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    # Convertir el día de la semana en una categoría ordenada
    df['dia_semana'] = pd.Categorical(df['fecha_despegue'].dt.day_name(), categories=day_order, ordered=True)

    # Crear la tabla pivot con el número de despegues
    pivot_table = df.pivot_table(
        index='dia_semana', 
        columns='hora_despegue', 
        values='tiempo_espera', 
        aggfunc='count', 
        fill_value=0, 
        observed=False
    )

    # Crear el heatmap con Plotly
    fig = px.imshow(
        pivot_table,
        labels={'x': 'Hora del Despegue', 'y': 'Día de la Semana', 'color': 'Cantidad de Despegues'},
        title="Mapa de Calor de Despegues por Día y Hora",
        color_continuous_scale="cividis"
    )

    fig.update_layout(
        xaxis=dict(title="Hora del Despegue", tickmode="linear", dtick=1),
        yaxis=dict(title="Día de la Semana"),
        coloraxis_colorbar=dict(title="Cantidad de Despegues"),
    )

    return fig

def generate_heatmap_for_type(df, tipo):
    # Definir el orden de los días de la semana
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    # Filtrar por tipo de aeronave
    df_filtrado = df[df['aircraft_type'] == tipo].copy()
    df_filtrado['dia_semana'] = pd.Categorical(df_filtrado['fecha_despegue'].dt.day_name(), categories=day_order, ordered=True)

    # Crear tabla pivot
    pivot_table = df_filtrado.pivot_table(
        index='dia_semana', 
        columns='hora_despegue', 
        values='tiempo_espera', 
        aggfunc='count', 
        fill_value=0, 
        observed=False
    )

    # Convertir a formato largo
    pivot_long = pivot_table.reset_index().melt(id_vars='dia_semana', var_name='hora_despegue', value_name='count')

    # Crear heatmap interactivo con Plotly
    fig = px.imshow(
        pivot_table,
        labels={'x': 'Hora del Despegue', 'y': 'Día de la Semana', 'color': 'Cantidad de Despegues'},
        title=f'Mapa de Calor de Despegues por Día y Hora para {tipo}',
        color_continuous_scale="cividis"
    )

    fig.update_layout(
        xaxis=dict(title="Hora del Despegue", tickmode="linear", dtick=1),
        yaxis=dict(title="Día de la Semana"),
        coloraxis_colorbar=dict(title="Cantidad de Despegues"),
    )

    return fig


def generate_average_heatmap():
    # Crear tabla pivot con el promedio de tiempo de espera
    pivot_table = df.pivot_table(
        values='tiempo_espera', 
        index='aircraft_type', 
        columns='hora_despegue', 
        aggfunc='mean', 
        observed=False
    )

    # Crear heatmap interactivo con Plotly
    fig = px.imshow(
        pivot_table,
        labels={'x': 'Hora del Despegue', 'y': 'Tipo de Aeronave', 'color': 'Tiempo de Espera (s)'},
        title="Promedio de Tiempo de Espera por Tipo de Aeronave y Hora de Despegue",
        color_continuous_scale="cividis"
    )

    fig.update_layout(
        xaxis=dict(title="Hora del Despegue", tickmode="linear", dtick=1),
        yaxis=dict(title="Tipo de Aeronave"),
        coloraxis_colorbar=dict(title="Tiempo de Espera (s)"),
    )

    return fig



def generate_average_wait_heatmap():
    # Definir el orden de los días de la semana
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    # Crear la columna de día de la semana con un orden específico
    df['dia_semana'] = pd.Categorical(df['fecha_despegue'].dt.day_name(), categories=day_order, ordered=True)

    # Crear la tabla pivot con el promedio de tiempo de espera
    pivot_table = df.pivot_table(
        index='dia_semana', 
        columns='hora_despegue', 
        values='tiempo_espera', 
        aggfunc='mean',  # 🔹 Promedio
        fill_value=0, 
        observed=False
    )

    # Convertir la tabla pivot en formato largo para Plotly
    pivot_table = pivot_table.reset_index().melt(id_vars='dia_semana', var_name='hora_despegue', value_name='tiempo_espera')

    # Crear el heatmap con Plotly
    fig = px.imshow(
        pivot_table.pivot(index='dia_semana', columns='hora_despegue', values='tiempo_espera'),
        labels={'x': 'Hora del Despegue', 'y': 'Día de la Semana', 'color': 'Tiempo de Espera (s)'},
        title='Mapa de Calor del Tiempo de Espera Medio por Día y Hora',
        color_continuous_scale="cividis"
    )

    fig.update_layout(
        xaxis=dict(title="Hora del Despegue", tickmode="linear", dtick=1),
        yaxis=dict(title="Día de la Semana"),
        coloraxis_colorbar=dict(title="Tiempo de Espera (s)"),
    )

    return fig


def generate_runaway_heatmap(df):
    # Asegurar que los días de la semana estén ordenados correctamente
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    df['dia_semana'] = pd.Categorical(df['fecha_despegue'].dt.day_name(), categories=day_order, ordered=True)

    # Crear tabla pivotante con el conteo de despegues
    pivot_table = df.pivot_table(index='dia_semana', columns='runway', values='despegue', aggfunc='count', fill_value=0)

    # Crear el heatmap interactivo con Plotly
    fig = px.imshow(
        pivot_table.values,
        labels=dict(x="Pista de Despegue", y="Día de la Semana", color="Número de Despegues"),
        x=pivot_table.columns,
        y=pivot_table.index,
        color_continuous_scale="cividis"
    )

    fig.update_layout(
        title="Número de Despegues por Día de la Semana y Pista de Despegue",
        xaxis_title="Pista de Despegue",
        yaxis_title="Día de la Semana",
        xaxis=dict(side="top"),  # Poner etiquetas arriba
        yaxis=dict(tickmode="array", tickvals=list(range(len(day_order))), ticktext=day_order)  # Asegurar orden
    )

    return fig

def generate_runway_hourly_heatmap(df):
    # Crear la tabla pivotante con el conteo de despegues
    pivot_table = df.pivot_table(index='runway', columns='hora_despegue', values='ICAO', aggfunc='count', fill_value=0)

    # Crear el heatmap con Plotly
    fig = px.imshow(
        pivot_table,
        labels={"x": "Hora del Día", "y": "Pista", "color": "Cantidad de Despegues"},
        color_continuous_scale="cividis",
        title="Número de Despegues por Hora y Pista"
    )

    # Ajustar el diseño del gráfico
    fig.update_layout(
        xaxis_title="Hora del Día",
        yaxis_title="Pista",
        xaxis=dict(tickmode="linear", dtick=1),
        yaxis=dict(tickmode="linear"),
        coloraxis_colorbar=dict(title="Despegues")
    )

    return fig

def generate_runway_waiting_time_heatmap(df):

    # Definir orden de días de la semana
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    df['dia_semana'] = pd.Categorical(df['fecha_despegue'].dt.day_name(), categories=day_order, ordered=True)

    # Crear la tabla pivotante
    pivot_table = df.pivot_table(index='runway', columns='dia_semana', values='tiempo_espera', aggfunc='mean', fill_value=0)

    # Crear el heatmap con Plotly
    fig = px.imshow(
        pivot_table,
        labels={"x": "Día de la Semana", "y": "Pista", "color": "Tiempo Medio de Espera (seg)"},
        color_continuous_scale="cividis",
        title="Tiempo Medio de Espera por Pista y Día de la Semana"
    )

    # Ajustar el diseño del gráfico
    fig.update_layout(
        xaxis_title="Día de la Semana",
        yaxis_title="Pista",
        xaxis=dict(tickmode="array", tickvals=list(range(7)), ticktext=day_order),
        yaxis=dict(tickmode="linear"),
        coloraxis_colorbar=dict(title="Segundos")
    )

    return fig

def generate_runway_hourly_waiting_time_heatmap(df):
    # Crear la tabla pivotante
    pivot_table = df.pivot_table(index='runway', columns='hora_despegue', values='tiempo_espera', aggfunc='mean', fill_value=0)

    # Crear el heatmap con Plotly
    fig = px.imshow(
        pivot_table,
        labels={"x": "Hora del Día", "y": "Pista", "color": "Tiempo Medio de Espera (seg)"},
        color_continuous_scale="cividis",
        title="Tiempo Medio de Espera por Pista y Hora del Día"
    )

    # Ajustar el diseño del gráfico
    fig.update_layout(
        xaxis_title="Hora del Día",
        yaxis_title="Pista",
        xaxis=dict(tickmode="linear", dtick=1),  # Mostrar todas las horas
        yaxis=dict(tickmode="linear"),
        coloraxis_colorbar=dict(title="Segundos")
    )

    return fig




# Define el layout de la aplicación con una pestaña de inicio y un menú desplegable
# Al construir el layout, asegúrate de añadir opciones de forma dinámica basadas en los tipos de avión.
app.layout = html.Div([
    html.H1("Dashboard de Análisis de Tiempos de Espera y Despegues"),
    dcc.Tabs([
        dcc.Tab(label='Inicio', children=[
            html.Div([
                html.Label("Selecciona un Gráfico:"),
                dcc.Dropdown(
                    id='graph-selector',
                    options=[
                        {'label': 'Boxplot de Tiempos de Espera', 'value': 'boxplot'},
                        {'label': 'Mapa de Calor de Despegues por Día', 'value': 'heatmap'},
                        {'label': 'Promedio de Tiempo de Espera por Tipo de Aeronave y Hora', 'value': 'average_heatmap'},
                        {'label': 'Promedio de Tiempo de Espera por Día y Hora', 'value': 'average_wait_heatmap'},
                        {'label': 'Mapa de Calor del Número de Despegues por Día de la Semana y Pista de Despegue', 'value': 'runway_heatmap'},
                        {'label': 'Mapa de Calor del Número de Despegues por Hora y Pista de Despegue', 'value': 'runway_hourly_heatmap'},
                        {'label': 'Tiempo Medio de Espera por Pista y Día de la Semana', 'value': 'runway_week_time'},
                        {'label': 'Tiempo Medio de Espera por Pista y Hora del Día', 'value': 'runway_hourly_time'},
                    ] + [{'label': f'Mapa de Calor por Día para {tipo}', 'value': f'heatmap_{tipo}'} for tipo in df['aircraft_type'].unique()],
                    value=None  # Sin selección predeterminada
                ),
                html.Div(id='graph-container')
            ])
        ])
    ])
])


@app.callback(
    Output('graph-container', 'children'),
    Input('graph-selector', 'value')
)
def update_graph(selected_value):
    if selected_value == 'boxplot':
        return dcc.Graph(figure=generate_boxplot())
    elif selected_value == 'heatmap':
        return dcc.Graph(figure=generate_heatmap(df))
    elif selected_value == 'average_heatmap':
        return dcc.Graph(figure=generate_average_heatmap())
    elif selected_value == 'average_wait_heatmap':  
        return dcc.Graph(figure=generate_average_wait_heatmap())
    elif selected_value == 'runway_heatmap':  
        return html.Div([
            dcc.Graph(figure=generate_runaway_heatmap(df)),
            html.Img(src="/assets/pistas_aeropuerto.jpg", style={"width": "30%", "display": "block", "margin": "auto"})
        ])
    elif selected_value == 'runway_hourly_heatmap':
        return html.Div([
            dcc.Graph(figure=generate_runway_hourly_heatmap(df)),
            html.Img(src="/assets/pistas_aeropuerto.jpg", style={"width": "30%", "display": "block", "margin": "auto"})
        ])
    elif selected_value == 'runway_week_time':
        return html.Div([
            dcc.Graph(figure=generate_runway_waiting_time_heatmap(df)),
            html.Img(src="/assets/pistas_aeropuerto.jpg", style={"width": "30%", "display": "block", "margin": "auto"})
        ])
    elif selected_value == 'runway_hourly_time':
        return html.Div([
            dcc.Graph(figure=generate_runway_hourly_waiting_time_heatmap(df)),
            html.Img(src="/assets/pistas_aeropuerto.jpg", style={"width": "30%", "display": "block", "margin": "auto"})
        ])
    elif selected_value and selected_value.startswith('heatmap_'):
        tipo = selected_value.split('heatmap_')[1]
        return dcc.Graph(figure=generate_heatmap_for_type(df, tipo))
    return html.Div('Seleccione una opción para visualizar los datos.')

# Corre la aplicación
if __name__ == '__main__':
    app.run_server(debug=True)