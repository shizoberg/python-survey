import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import pandas as pd
from scipy.stats import shapiro
import io
import base64

# Dash Uygulaması
app = dash.Dash(__name__)

# Uygulama Düzeni
app.layout = html.Div([
    html.H1("Normal Dağılım Kontrolü", style={"textAlign": "center"}),

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
    html.Div(id="column-selector"),
    html.Div(id="normality-test-output", style={"marginTop": "20px"}),
])

# Callback: Sütun Seçici Oluştur
@app.callback(
    Output("column-selector", "children"),
    Input("upload-data", "contents"),
    State("upload-data", "filename")
)
def create_column_selector(contents, filename):
    if contents is None:
        return ""

    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    try:
        if filename.endswith('.csv'):
            # CSV dosyasını oku ve sütunları seç
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), sep=";")
        else:
            return html.Div(["Desteklenmeyen dosya formatı. Lütfen bir CSV dosyası yükleyin."])
        
        # Son iki sütunu çıkar
        df = df.iloc[:, :-2]

        # Sayısal değerlere dönüştür
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        columns = [{"label": col, "value": col} for col in df.columns]
        return html.Div([
            html.Label("Sayı Değerlerine Sahip Sütun:"),
            dcc.Dropdown(id="column", options=columns, placeholder="Bir sütun seçin"),
            html.Button("Normal Dağılım Testini Çalıştır", id="run-test", n_clicks=0, style={"marginTop": "10px"})
        ])
    except Exception as e:
        return html.Div([f"Dosya işlenirken bir hata oluştu: {str(e)}"])

# Callback: Normal Dağılım Test Sonuçları
@app.callback(
    Output("normality-test-output", "children"),
    Input("run-test", "n_clicks"),
    State("upload-data", "contents"),
    State("upload-data", "filename"),
    State("column", "value")
)
def run_normality_test(n_clicks, contents, filename, column):
    if n_clicks == 0 or contents is None or column is None:
        return ""

    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    try:
        if filename.endswith('.csv'):
            # CSV dosyasını oku ve sütunları seç
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), sep=";")
            df = df.iloc[:, :-2]
            df[column] = pd.to_numeric(df[column], errors='coerce')
        else:
            return html.Div(["Desteklenmeyen dosya formatı. Lütfen bir CSV dosyası yükleyin."])
    except Exception as e:
        return html.Div([f"Dosya işlenirken bir hata oluştu: {str(e)}"])

    try:
        # Null değerleri çıkar
        data = df[column].dropna()

        # Normal Dağılım Testi
        stat, p = shapiro(data)
        hypothesis_result = "Normal" if p > 0.05 else "Normal dağılmıyor."
        result_summary = html.Div([
            html.P(f"Shapiro-Wilk Test İstatistiği: {stat:.3f}"),
            html.P(f"p-değeri: {p:.3f}"),
            html.P(hypothesis_result, style={"color": "green" if p > 0.05 else "red"})
        ])

        return html.Div([
            html.H3("Normal Dağılım Test Sonuçları", style={"marginTop": "20px"}),
            result_summary
        ])
    except Exception as e:
        return html.Div([f"Analiz sırasında bir hata oluştu: {str(e)}"])

if __name__ == "__main__":
    app.run_server(debug=True, port=8050)