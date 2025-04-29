import os
import requests
from datetime import datetime, timedelta

# Coordenadas de Ilha Comprida (SP)
LATITUDE = -24.7300
LONGITUDE = -47.5500

# API KEY via variável de ambiente
API_KEY = os.getenv("STORMGLASS_API_KEY")

# Datas de sábado e domingo seguintes
hoje = datetime.utcnow()
dias_ate_sabado = (5 - hoje.weekday()) % 7
dias_ate_domingo = (6 - hoje.weekday()) % 7

data_sabado = (hoje + timedelta(days=dias_ate_sabado)).strftime("%Y-%m-%d")
data_domingo = (hoje + timedelta(days=dias_ate_domingo)).strftime("%Y-%m-%d")

# Chamada para pegar dados dos dois dias
response = requests.get(
    f"https://api.stormglass.io/v2/weather/point",
    params={
        "lat": LATITUDE,
        "lng": LONGITUDE,
        "params": "waterTemperature,windSpeed,windDirection,airTemperature,pressure,moonPhase",
        "start": f"{data_sabado}T00:00:00+00:00",
        "end": f"{data_domingo}T23:59:59+00:00",
        "source": "noaa"
    },
    headers={"Authorization": API_KEY}
)

dados = response.json()["hours"]

# Função auxiliar para encontrar o valor médio de um parâmetro em um dia
def media_por_dia(dados, campo, data_alvo):
    valores = [hora[campo]['noaa'] for hora in dados if hora['time'].startswith(data_alvo)]
    return round(sum(valores) / len(valores), 1) if valores else None

# Função para traduzir fase da lua
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

# Monta os dados para os dois dias
def montar_previsao(data_iso):
    dia = datetime.strptime(data_iso, "%Y-%m-%d")
    dados_dia = {
        "data": dia.strftime("%d/%m"),
        "vento": f"{media_por_dia(dados, 'windSpeed', data_iso)} km/h",
        "temp_agua": f"{media_por_dia(dados, 'waterTemperature', data_iso)} °C",
        "pressao": f"{media_por_dia(dados, 'pressure', data_iso)} hPa",
        "lua": fase_lua(media_por_dia(dados, 'moonPhase', data_iso)),
        "icone": "🌤️"
    }
    return dados_dia

previsao = {
    "sabado": montar_previsao(data_sabado),
    "domingo": montar_previsao(data_domingo)
}

# Gera HTML de cada card
def gerar_card(dia, dados):
    return f"""
    <div class="card">
        <h2>{dia.upper()}<br>{dados['data']}</h2>
        <div class="icon">{dados['icone']}</div>
        <p>Vento<br>{dados['vento']}</p>
        <p>Temperatura da água<br>{dados['temp_agua']}</p>
        <p>Pressão<br>{dados['pressao']}</p>
        <p>Fase da lua<br>{dados['lua']}</p>
    </div>
    """

# Lê HTML base
with open("index_base.html", "r", encoding="utf-8") as base:
    html_base = base.read()

# Monta os dois cards
html_cards = f"""
<div class="container">
  {gerar_card("Sábado", previsao['sabado'])}
  {gerar_card("Domingo", previsao['domingo'])}
</div>
"""

# Gera HTML final
html_final = html_base.replace("{{PREVISAO_PESCARIA}}", html_cards)

# Salva index.html
with open("index.html", "w", encoding="utf-8") as saida:
    saida.write(html_final)
