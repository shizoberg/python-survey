import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.graph_objects as go
import io
import base64

# Veriyi temizleme ve sütunlara ayırma
def clean_and_split_data(df):
    # Sütunları ayır
    df = df.iloc[:, 0].str.split(";", expand=True)
    # Sütun isimlerini otomatik oluştur
    df.columns = [f"Column{i+1}" for i in range(df.shape[1])]
    # Tüm sütunları sayısal değerlere dönüştür
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

# Cronbach's Alfa Hesaplama Fonksiyonu
def calculate_cronbach_alpha(df):
    n_items = df.shape[1]
    item_variances = df.var(axis=0, ddof=1)
    total_variance = df.sum(axis=1).var(ddof=1)
    if total_variance == 0:
        return "Varyans sıfır olduğu için Cronbach's Alfa hesaplanamıyor."
    alpha = (n_items / (n_items - 1)) * (1 - item_variances.sum() / total_variance)
    return alpha

# Frekans Tablosu Oluşturma
def create_frequency_table(column):
    counts = column.value_counts().sort_index()
    total = counts.sum()
    percent = (counts / total) * 100
    cumulative_percent = percent.cumsum()

    freq_table = pd.DataFrame({
        "Response": counts.index,
        "Frequency": counts.values,
        "Percent": percent.round(1),
        "Valid Percent": percent.round(1),
        "Cumulative Percent": cumulative_percent.round(1)
    })
    return freq_table

# Dash uygulaması
app = dash.Dash(__name__)

# Uygulama düzeni
app.layout = html.Div([
    html.H1("Anket Güvenilirlik Analizi ve İstatistikler", style={"textAlign": "center"}),

    dcc.Upload(
        id="upload-data",
        children=html.Div([
            "Dosyayı Sürükleyip Bırakın veya ",
            html.A("Bir Dosya Seçin")
        ]),
        style={
            "width": "100%",
            "height": "60px",
            "lineHeight": "60px",
            "borderWidth": "1px",
            "borderStyle": "dashed",
            "borderRadius": "5px",
            "textAlign": "center",
            "margin": "10px"
        },
        multiple=False
    ),
    html.Div(id="output-content"),
])

@app.callback(
    Output("output-content", "children"),
    Input("upload-data", "contents"),
    State("upload-data", "filename")
)
def update_output(contents, filename):
    if contents is None:
        return html.Div(["Bir dosya yükleyin ve analiz başlasın."])
    
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif filename.endswith('.xlsx'):
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            return html.Div(["Desteklenmeyen dosya formatı. Lütfen bir CSV veya Excel dosyası yükleyin."])
    except Exception as e:
        return html.Div([f"Dosya işlenirken bir hata oluştu: {str(e)}"])

    # Veriyi temizle ve sütunlara ayır
    df = clean_and_split_data(df)

    # NaN değerleri sadece analiz için doldur
    df_filled = df.fillna(df.mean())

    # Cronbach's Alfa hesaplama
    alpha = calculate_cronbach_alpha(df_filled)

    # Histogram ve pie chart grafikleri (sadece orijinal verilerle)
    charts = []
    for column in df.columns:
        # Sadece orijinal verileri kullan (NaN değerler hariç)
        valid_data = df[column].dropna()

        # Histogram
        response_counts = valid_data.value_counts().sort_index()
        percentages = response_counts / response_counts.sum() * 100

        fig_hist = go.Figure()
        fig_hist.add_trace(go.Bar(
            x=response_counts.index,
            y=response_counts.values,
            name="Frequency",
            marker_color="blue"
        ))
        fig_hist.add_trace(go.Scatter(
            x=percentages.index,
            y=percentages.values,
            name="Percent",
            mode="lines+markers",
            line=dict(color="red", width=2)
        ))
        fig_hist.update_layout(
            title=f"{column} - Histogram and Percent Change",
            xaxis_title="Responses",
            yaxis_title="Frequency and Percent",
            height=400
        )

        # Pie chart
        fig_pie = go.Figure(data=[go.Pie(
            labels=response_counts.index,
            values=response_counts.values,
            hole=0.4
        )])
        fig_pie.update_layout(title=f"{column} - Pie Chart")

        charts.append(html.Div([
            dcc.Graph(figure=fig_hist),
            dcc.Graph(figure=fig_pie)
        ], style={"display": "flex", "flexWrap": "wrap", "gap": "20px"}))

    # Frekans Tabloları
    frequency_tables = []
    for column in df.columns:
        freq_table = create_frequency_table(df[column])
        freq_table_div = dash_table.DataTable(
            columns=[{"name": i, "id": i} for i in freq_table.columns],
            data=freq_table.to_dict('records'),
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "center", "padding": "5px"},
            style_header={"fontWeight": "bold"}
        )
        frequency_tables.append(html.Div([
            html.H4(f"{column} Frequency Table"),
            freq_table_div
        ], style={"marginBottom": "20px"}))

    # Line Chart for Column Averages
    column_averages = df_filled.mean()
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(
        x=column_averages.index,
        y=column_averages.values,
        mode='lines+markers',
        name='Averages'
    ))
    fig_line.update_layout(
        title="Sütun Ortalamaları",
        xaxis_title="Columns",
        yaxis_title="Average Values",
        height=400
    )

    return html.Div([
        html.H3(f"Cronbach's Alpha: {alpha if isinstance(alpha, str) else round(alpha, 3)}", style={"marginTop": "20px"}),
        html.H3("Grafikler", style={"marginTop": "20px"}),
        html.Div(charts, style={"display": "flex", "flexWrap": "wrap", "gap": "20px"}),
        html.H3("Frekans Tabloları", style={"marginTop": "20px"}),
        html.Div(frequency_tables, style={"marginTop": "20px"}),
        html.H3("Sütun Ortalamaları", style={"marginTop": "20px"}),
        dcc.Graph(figure=fig_line)
    ])

if __name__ == "__main__":
    app.run_server(debug=True, port=8050)