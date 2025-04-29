import os
import requests
from datetime import datetime, timedelta

# Coordenadas de Ilha Comprida
LATITUDE = -24.7300
LONGITUDE = -47.5500

# Chave da API via variável de ambiente segura
API_KEY = os.getenv("STORMGLASS_API_KEY")

# Cálculo de sábado e domingo seguintes
hoje = datetime.utcnow()
dias_ate_sabado = (5 - hoje.weekday()) % 7
dias_ate_domingo = (6 - hoje.weekday()) % 7

data_sabado = (hoje + timedelta(days=dias_ate_sabado)).strftime("%Y-%m-%d")
data_domingo = (hoje + timedelta(days=dias_ate_domingo)).strftime("%Y-%m-%d")

# Consulta à Stormglass
response = requests.get(
    "https://api.stormglass.io/v2/weather/point",
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

# Verificação de erro
response_json = response.json()

if "hours" not in response_json:
    print("Erro: resposta sem campo 'hours'")
    print("Resposta completa:", response_json)
    exit(1)

dados = response_json["hours"]

# Funções auxiliares
def media_por_dia(dados, campo, data_alvo):
    valores = [hora[campo]['noaa'] for hora in dados if hora['time'].startswith(data_alvo)]
    return round(sum(valores) / len(valores), 1) if valores else None

def fase_lua(valor):
    if valor is None:
        return "Desconhecida"
    elif valor < 0.1 or valor > 0.9:
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

def montar_previsao(data_iso):
    dia = datetime.strptime(data_iso, "%Y-%m-%d")
    return {
        "data": dia.strftime("%d/%m"),
        "vento": f"{media_por_dia(dados, 'windSpeed', data_iso)} km/h",
        "temp_agua": f"{media_por_dia(dados, 'waterTemperature', data_iso)} °C",
        "pressao": f"{media_por_dia(dados, 'pressure', data_iso)} hPa",
        "lua": fase_lua(media_por_dia(dados, 'moonPhase', data_iso)),
        "icone": "🌤️"
    }

previsao = {
    "sabado": montar_previsao(data_sabado),
    "domingo": montar_previsao(data_domingo)
}

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

# Insere cards lado a lado
html_cards = f"""
<div class="container">
  {gerar_card("Sábado", previsao['sabado'])}
  {gerar_card("Domingo", previsao['domingo'])}
</div>
"""

# Substitui marcador no HTML base
html_final = html_base.replace("{{PREVISAO_PESCARIA}}", html_cards)

# Salva HTML final
with open("index.html", "w", encoding="utf-8") as saida:
    saida.write(html_final)
