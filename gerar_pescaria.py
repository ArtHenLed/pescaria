import os
import requests
from datetime import datetime, timedelta

# Coordenadas de Ilha Comprida
LATITUDE = -24.7300
LONGITUDE = -47.5500

# API Key (armazenada como segredo no GitHub)
API_KEY = os.getenv("STORMGLASS_API_KEY")

# Cálculo das datas do próximo sábado e domingo
hoje = datetime.utcnow()
dias_ate_sabado = (5 - hoje.weekday()) % 7
dias_ate_domingo = (6 - hoje.weekday()) % 7

data_sabado = (hoje + timedelta(days=dias_ate_sabado)).strftime("%Y-%m-%d")
data_domingo = (hoje + timedelta(days=dias_ate_domingo)).strftime("%Y-%m-%d")

# Consulta aos dados climáticos
weather_response = requests.get(
    "https://api.stormglass.io/v2/weather/point",
    params={
        "lat": LATITUDE,
        "lng": LONGITUDE,
        "params": "waterTemperature,windSpeed,windDirection,pressure",
        "start": f"{data_sabado}T00:00:00+00:00",
        "end": f"{data_domingo}T23:59:59+00:00",
        "source": "noaa"
    },
    headers={"Authorization": API_KEY}
)

# Consulta da fase da lua
astro_response = requests.get(
    "https://api.stormglass.io/v2/astronomy/point",
    params={
        "lat": LATITUDE,
        "lng": LONGITUDE,
        "start": f"{data_sabado}T00:00:00+00:00",
        "end": f"{data_domingo}T23:59:59+00:00"
    },
    headers={"Authorization": API_KEY}
)

# Tratamento das respostas
weather_json = weather_response.json()
astro_json = astro_response.json()

if "hours" not in weather_json or "data" not in astro_json:
    print("Erro ao obter dados da API")
    print("Weather JSON:", weather_json)
    print("Astro JSON:", astro_json)
    exit(1)

dados = weather_json["hours"]
dados_lua = astro_json["data"]

# Funções auxiliares
def media_por_dia(dados, campo, data_alvo):
    valores = [hora[campo]['noaa'] for hora in dados if hora['time'].startswith(data_alvo)]
    return round(sum(valores) / len(valores), 1) if valores else 0

def fase_lua(valor):
    if valor < 0.1 or valor > 0.9:
        return "Lua Nova"
    elif 0.1 <= valor < 0.25:
        return "Crescente"
    elif 0.25 <= valor < 0.5:
        return "Quarto Crescente"
    elif 0.5 <= valor < 0.75:
        return "Lua Cheia"
    elif 0.75 <= valor <= 0.9:
        return "Minguante"
    else:
        return "Quarto Minguante"

def fase_lua_por_data(data_alvo):
    for d in dados_lua:
        if d["time"].startswith(data_alvo):
            valor = d["moonPhase"]
            if isinstance(valor, dict):
                valor = valor.get("noaa", 0)
            return fase_lua(valor)
    return "Desconhecida"

def montar_previsao(data_iso):
    dia = datetime.strptime(data_iso, "%Y-%m-%d")
    return {
        "data": dia.strftime("%d/%m"),
        "vento": f"{media_por_dia(dados, 'windSpeed', data_iso)} km/h",
        "temp_agua": f"{media_por_dia(dados, 'waterTemperature', data_iso)} °C",
        "pressao": f"{media_por_dia(dados, 'pressure', data_iso)} hPa",
        "lua": fase_lua_por_data(data_iso),
        "icone": "☀️"  # Sol como placeholder
    }

previsao = {
    "sabado": montar_previsao(data_sabado),
    "domingo": montar_previsao(data_domingo)
}

# Novo layout dos cards com 4 quadrantes (2x2)
def gerar_card(dia, dados):
    return f"""
    <div class="card">
        <h2>{dia.upper()}<br>{dados['data']}</h2>
        <div class="icon">{dados['icone']}</div>
        <div class="info-grid">
            <div>Vento<br>{dados['vento']}</div>
            <div>Temp. água<br>{dados['temp_agua']}</div>
            <div>Pressão<br>{dados['pressao']}</div>
            <div>{dados['lua']}</div>
        </div>
    </div>
    """

# Monta HTML final
with open("index_base.html", "r", encoding="utf-8") as base:
    html_base = base.read()

html_cards = f"""
<div class="container">
  {gerar_card("Sábado", previsao['sabado'])}
  {gerar_card("Domingo", previsao['domingo'])}
</div>
"""

html_final = html_base.replace("{{PREVISAO_PESCARIA}}", html_cards)

# Salva
with open("index.html", "w", encoding="utf-8") as saida:
    saida.write(html_final)
