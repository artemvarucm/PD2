# Importación de librerías necesarias
from dash import Dash, html, dash_table, dcc, callback, Output, Input
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import os
import math
import locale
from datetime import datetime  

# Configuración de la localización
locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")

# Cargar el dataset
df = pd.read_csv("../../../data/ex1/datos_aire_tierra.csv")

# Estilo externo para la aplicación
external_stylesheets = ['styles.css']

# Inicialización de la aplicación Dash
app = Dash(__name__, external_stylesheets=external_stylesheets)

# Función para obtener el día de la semana a partir de una fecha
def get_day_of_week(fecha_str):
    fecha = datetime.strptime(fecha_str, "%d/%m/%Y")
    return fecha.strftime("%A").capitalize()

# DataFrame que contiene todas las horas del día y el estado 'OnGround'
all_hours = pd.DataFrame([
    {"hour": h, "OnGround": og} 
    for h in range(24) for og in [0, 1]
])

# Obtener todos los días únicos del DataFrame
days = df["day"].unique()

# Diseño de la interfaz de usuario
app.layout = html.Div([
    html.H1(children='Tráfico aéreo'),
    html.Hr(),
    html.Div([ 
        # Gráfico 1: Tráfico aéreo por hora - Día 1
        html.Div([
            dcc.Dropdown(
                id='dia_1',
                options=[{'label': f"{day} ( {get_day_of_week(day)} )", 'value': day} for day in days],
                value='01/12/2024',
                clearable=False,
                searchable=False,
                style={'width': '50%'}
            ),
            dcc.Graph(id="tipo_obesidad_grafica"),
        ], id="g1"),

        # Gráfico 2: Tráfico aéreo por hora - Día 2
        html.Div([
            dcc.Dropdown(
                id='dia_2',
                options=[{'label': f"{day} ( {get_day_of_week(day)} )", 'value': day} for day in days],
                value='02/12/2024',
                clearable=False,
                searchable=False,
                style={'width': '50%'}
            ),
            dcc.Graph(id="tipo_obesidad_grafica2")
        ], id="g2"),

        # Gráfico 3: Tráfico aéreo por día de la semana
        html.Div([
            dcc.Graph(id="line_plot"),
        ], id="g3", style={'width': '50%', 'margin': 'auto'}),

        # Gráfico 4: Matriz de calor del tráfico aéreo
        html.Div([
            dcc.Graph(id='graph-with-speciality')
        ], id="g4"),
        ## Grafico 5
         html.Div([
            dcc.Graph(id='Cantidad de aviones en tierra por hora')
        ], id="g5"),
         ## Grafico 6
         html.Div([
            dcc.Graph(id='Cantidad de aviones en aire por hora')
        ], id="g6")
        
    ], id="parent")
])

# Función para obtener el valor máximo para el rango del eje Y
def get_max(dia1, dia2):
    max_y = 0  # Variable para el valor máximo en el eje Y
    for day in [dia1, dia2]:  # Iteramos sobre los dos días seleccionados
        df_day = df[df["day"] == day]  # Filtramos los datos por el día
        df_day = df_day.groupby(["hour", "OnGround"])["OnGround"].size().reset_index(name="count")
        df_day = all_hours.merge(df_day, on=["hour", "OnGround"], how="left").fillna(0)
        
        max_y = max(max_y, df_day["count"].max())  # Actualizamos el máximo
    
    return math.ceil(max_y / 10) * 10  # Redondeamos el máximo al siguiente múltiplo de 10

# Callback para actualizar el gráfico 1
@app.callback(
    Output(component_id='tipo_obesidad_grafica', component_property='figure'),
    [Input(component_id='dia_1', component_property='value'),
     Input(component_id='dia_2', component_property='value')]
)
def update_graph_1(dia_1, dia_2):
    maximo = get_max(dia_1, dia_2)

    df_day = df[df["day"] == dia_1]  # Filtramos los datos para el día 1
    df_day = df_day.groupby(["hour", "OnGround"])["OnGround"].size().reset_index(name="count")
    df_day = all_hours.merge(df_day, on=["hour", "OnGround"], how="left").fillna(0)

    # Datos para los aviones en tierra y en aire
    on_ground_count = df_day[df_day["OnGround"] == 1]["count"].values
    flying_count = df_day[df_day["OnGround"] == 0]["count"].values
    hours = df_day[df_day["OnGround"] == 1]["hour"].values  

    # Crear gráfico con Plotly
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hours, y=on_ground_count, mode='lines+markers', name='En Tierra'))
    fig.add_trace(go.Scatter(x=hours, y=flying_count, mode='lines+markers', name='En Aire'))

    fig.update_layout(
        title=f"Tráfico Aéreo por Hora - Día {dia_1}",
        xaxis_title="Hora del Día",
        yaxis_title="Cantidad de Aviones",
        xaxis=dict(tickmode="linear", dtick=1),
        yaxis=dict(range=[0, maximo]),  # Establecer el rango del eje Y
    )

    return fig

# Callback para actualizar el gráfico 2
@app.callback(
    Output(component_id='tipo_obesidad_grafica2', component_property='figure'),
    [Input(component_id='dia_1', component_property='value'),
     Input(component_id='dia_2', component_property='value')]
)
def update_graph_2(dia_1, dia_2):
    maximo = get_max(dia_1, dia_2)

    df_day = df[df["day"] == dia_2]  # Filtramos los datos para el día 2
    df_day = df_day.groupby(["hour", "OnGround"])["OnGround"].size().reset_index(name="count")
    df_day = all_hours.merge(df_day, on=["hour", "OnGround"], how="left").fillna(0)

    # Datos para los aviones en tierra y en aire
    on_ground_count = df_day[df_day["OnGround"] == 1]["count"].values
    flying_count = df_day[df_day["OnGround"] == 0]["count"].values
    hours = df_day[df_day["OnGround"] == 1]["hour"].values  

    # Crear gráfico con Plotly
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hours, y=on_ground_count, mode='lines+markers', name='En Tierra'))
    fig.add_trace(go.Scatter(x=hours, y=flying_count, mode='lines+markers', name='En Aire'))

    fig.update_layout(
        title=f"Tráfico Aéreo por Hora - Día {dia_2}",
        xaxis_title="Hora del Día",
        yaxis_title="Cantidad de Aviones",
        xaxis=dict(tickmode="linear", dtick=1),
        yaxis=dict(range=[0, maximo]),  # Establecer el rango del eje Y
    )

    return fig

# Callback para actualizar el gráfico de barras (Tráfico aéreo por día)
@app.callback(
    Output("line_plot", "figure"),
    Input("dia_1", "value")
)
def update_bar_chart(dia):
    df_day = df.groupby(['day', 'OnGround']).size().reset_index(name='count')
    df_day["OnGround"] = df_day["OnGround"].replace({1: "En Tierra", 0: "En Aire"})
    df_day = df_day.sort_values(by="count", ascending=False)

    # Crear gráfico de barras con Plotly
    fig = px.bar(df_day, x="day", y="count", color="OnGround", barmode="stack")

    fig.update_layout(
        xaxis_title="Día de la semana",
        yaxis_title="Cantidad de Aviones",
        title=dict(
            text="Tráfico Aéreo por Día de la Semana",
            x=0.5,
        )
    )

    return fig

# Callback para actualizar el gráfico de la matriz de calor (Heatmap)
@callback(
    Output('graph-with-speciality', 'figure'),
    Input('dia_1', 'value'),
)
def update_heatmap(dia):
    df_heatmap = df.groupby(['day', 'hour']).size().reset_index(name='count')
    fig = px.imshow(df_heatmap.pivot(index='day', columns='hour', values='count').fillna(0), 
                    labels=dict(color="Cantidad de aviones"),
                    title="Matriz de Calor del Tráfico Aéreo por Día y Hora",
                    aspect="auto")

    fig.update_layout(
        xaxis=dict(tickmode="linear", dtick=2),
        title=dict(       
            text="Matriz de Calor del Tráfico Aéreo por Día y Hora",
            x=0.5
        ),
        xaxis_title="Horas",
        yaxis_title="Días",
    )
    return fig 

# Callback para actualizar el gráfico de linea para aviones en tierra
@callback(
    Output('Cantidad de aviones en tierra por hora', 'figure'),
    Input('dia_1', 'value'),
)
def update_ground_line(dia):
    all_days = pd.DataFrame([
    {"day": d, "hour": h} 
    for d in days for h in range(24)
    ])
    df_merged_ground = all_days.merge(df, on=["day","hour"], how="left").fillna(0)
    ground_count = df_merged_ground[df_merged_ground["OnGround"] == 1].groupby(["day", "hour"]).size().reset_index(name="count")
   
    fig_ground = px.line(ground_count, x="hour", y="count", color="day",
                        labels={"hour": "Hora del día", "count": "Cantidad de aeronaves", "day": "Día"})

    fig_ground.update_layout(
        xaxis=dict(tickmode="linear", dtick=1),
        title=dict(       
                text = "Cantidad de aviones en TIERRA por hora",
                x = 0.5,
            ),
        )
    return fig_ground


# Callback para actualizar el gráfico de linea para aviones en tierra
@callback(
    Output('Cantidad de aviones en aire por hora', 'figure'),
    Input('dia_1', 'value'),
)

def update_on_air_line(dia):
        all_days = pd.DataFrame([
        {"day": d, "hour": h} 
        for d in days for h in range(24)
        ])
        df_merged_air = all_days.merge(df, on=["day","hour"], how="left").fillna(0)
        air_count = df_merged_air[df_merged_air["OnGround"] == 0].groupby(["day", "hour"]).size().reset_index(name="count")


        fig_air = px.line(air_count, x="hour", y="count", color="day",
                        labels={"hour": "Hora del día", "count": "Cantidad de aeronaves", "day": "Día"})

        fig_air.update_layout(
            xaxis=dict(tickmode="linear", dtick=1),
            title=dict(       
                    text = "Cantidad de aviones en AIRE por hora",
                    x = 0.5, 
                ),
        )

        
        return fig_air


# Ejecutar la aplicación
if __name__ == '__main__':
    app.run(debug=True)
