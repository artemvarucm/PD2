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

df = pd.read_csv('../../data/ex1/eventos_espera_semana.csv')

df['ultimo_parado'] = pd.to_datetime(df['ultimo_parado'])
df['despegue'] = pd.to_datetime(df['despegue'])
df['fecha_despegue'] = pd.to_datetime(df['fecha_despegue'])
df['hora_despegue'] = df['hora_despegue'].astype(int)


app = dash.Dash(__name__)

# Función para crear un plot y convertirlo a imagen para mostrar en Dash
def plot_to_html_img(plt):
    buf = BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    src = "data:image/png;base64,{}".format(data)
    return html.Img(src=src)  # Retornamos un componente HTML de imagen


# Crea un boxplot con Matplotlib y lo convierte a imagen HTML
def generate_boxplot():
    plt.figure(figsize=(12, 6))
    sns.boxplot(x='aircraft_type', y='tiempo_espera', data=df)
    plt.title('Boxplot de Tiempos de Espera por Tipo de Avión')
    plt.xlabel('Tipo de Avión')
    plt.ylabel('Tiempo de Espera (segundos)')
    plt.xticks(rotation=45)
    return plot_to_html_img(plt)

# Función para generar el mapa de calor
def generate_heatmap(df):
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    df['dia_semana'] = pd.Categorical(df['fecha_despegue'].dt.day_name(), categories=day_order, ordered=True)
    
    pivot_table = df.pivot_table(index='dia_semana', columns='hora_despegue', values='tiempo_espera', aggfunc='count', fill_value=0)
    
    plt.figure(figsize=(12, 7))
    sns.heatmap(pivot_table, annot=True, fmt="d", cmap="cividis")
    plt.title('Mapa de Calor de Tiempo de Espera por Día de la Semana y Hora')
    plt.xlabel('Hora del Despegue')
    plt.ylabel('Día de la Semana')
    
    return plot_to_html_img(plt)

def generate_heatmap_for_type(df, tipo):
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    df_filtrado = df[df['aircraft_type'] == tipo]
    df_filtrado['dia_semana'] = pd.Categorical(df_filtrado['fecha_despegue'].dt.day_name(), categories=day_order, ordered=True)

    pivot_table = df_filtrado.pivot_table(index='dia_semana', columns='hora_despegue', values='tiempo_espera', aggfunc='count', fill_value=0)

    plt.figure(figsize=(12, 7))
    sns.heatmap(pivot_table, annot=True, fmt="d", cmap="cividis")
    plt.title(f'Mapa de Calor de Tiempo de Espera por Día de la Semana y Hora para {tipo}')
    plt.xlabel('Hora del Despegue')
    plt.ylabel('Día de la Semana')

    return plot_to_html_img(plt)

def generate_average_heatmap():
    pivot_data = df.pivot_table(values='tiempo_espera', index='aircraft_type', columns='hora_despegue', aggfunc='mean')

    plt.figure(figsize=(15, 10))
    sns.heatmap(pivot_data, cmap="cividis", annot=True, fmt=".0f", annot_kws={"size": 8})
    plt.title("Promedio de Tiempo de Espera por Tipo de Aeronave y Hora de Despegue")
    plt.xlabel("Hora del Despegue")
    plt.ylabel("Tipo de Aeronave")
    
    return plot_to_html_img(plt)



# Define el layout de la aplicación con una pestaña de inicio y un menú desplegable
# Al construir el layout, asegúrate de añadir opciones de forma dinámica basadas en los tipos de avión.
app.layout = html.Div([
    html.H1("Dashboard de Análisis de Tiempos de Espera"),
    dcc.Tabs([
        dcc.Tab(label='Inicio', children=[
            html.Div([
                html.Label("Selecciona un Gráfico:"),
                dcc.Dropdown(
                    id='graph-selector',
                    options=[
                        {'label': 'Boxplot de Tiempos de Espera', 'value': 'boxplot'},
                        {'label': 'Mapa de Calor de Tiempos de Espera por Día', 'value': 'heatmap'},
                        {'label': 'Promedio de Tiempo de Espera por Tipo de Aeronave y Hora', 'value': 'average_heatmap'},
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
        return generate_boxplot()
    elif selected_value == 'heatmap':
        return generate_heatmap(df)
    elif selected_value == 'average_heatmap':  # Nueva opción añadida
        return generate_average_heatmap()
    elif selected_value and selected_value.startswith('heatmap_'):
        tipo = selected_value.split('heatmap_')[1]
        return generate_heatmap_for_type(df, tipo)
    return html.Div('Seleccione una opción para visualizar los datos.')

# Corre la aplicación
if __name__ == '__main__':
    app.run_server(debug=True)