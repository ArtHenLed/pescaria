import os
import requests
from datetime import datetime, timedelta

LATITUDE = -24.7300
LONGITUDE = -47.5500
API_KEY = os.getenv("STORMGLASS_API_KEY")

hoje = datetime.utcnow()
dias_ate_sabado = (5 - hoje.weekday()) % 7
dias_ate_domingo = (6 - hoje.weekday()) % 7

data_sabado = (hoje + timedelta(days=dias_ate_sabado)).strftime("%Y-%m-%d")
data_domingo = (hoje + timedelta(days=dias_ate_domingo)).strftime("%Y-%m-%d")

weather_response = requests.get(
    "https://api.stormglass.io/v2/weather/point",
    params={
        "lat": LATITUDE,
        "lng": LONGITUDE,
        "params": "waterTemperature,windSpeed,windDirection,pressure,cloudCover,precipitation",
        "start": f"{data_sabado}T00:00:00+00:00",
        "end": f"{data_domingo}T23:59:59+00:00",
        "source": "noaa"
    },
    headers={"Authorization": API_KEY}
)

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

weather_json = weather_response.json()
astro_json = astro_response.json()

if "hours" not in weather_json or "data" not in astro_json:
    print("Erro ao obter dados da API")
    exit(1)

dados = weather_json["hours"]
dados_lua = astro_json["data"]

def seta_vento(angulo):
    if angulo is None:
        return "â“"
    direcoes = [
        (0, "â¬‡ï¸"), (45, "â†™ï¸"), (90, "â¬…ï¸"), (135, "â†–ï¸"),
        (180, "â¬†ï¸"), (225, "â†—ï¸"), (270, "âž¡ï¸"), (315, "â†˜ï¸"), (360, "â¬‡ï¸")
    ]
    for i in range(len(direcoes) - 1):
        if direcoes[i][0] <= angulo < direcoes[i + 1][0]:
            return direcoes[i][1]
    return "â“"

def icone_clima(nuvens, chuva):
    if chuva > 2.0:
        return "<img src='chuva_forte.png' width='18' height='18'/>"
    elif chuva > 1.0:
        return "<img src='chuva_moderada.png' width='18' height='18'/>"
    elif chuva > 0.1:
        return "<img src='chuva_leve.png' width='18' height='18'/>"
    elif nuvens > 70:
        return "<img src='nublado.png' width='18' height='18'/>"
    elif nuvens > 30:
        return "<img src='chuva_com_trovoada.png' width='18' height='18'/>"
    else:
        return "<img src='sol.png' width='18' height='18'/>"

def icone_lua(fase):
    fases_disponiveis = [0, 3, 6, 10, 13, 17, 20, 24, 27, 30, 34, 37, 41, 44, 48,
                         51, 55, 58, 62, 65, 68, 72, 75, 79, 82, 86, 89, 93, 96]
    fase_mais_proxima = min(fases_disponiveis, key=lambda x: abs(x - round(fase * 100)))
    return f"<img src='lua_{fase_mais_proxima:02d}.png' width='18' height='18'/>"

def media_por_dia(dados, campo, data_alvo):
    valores = [hora[campo]['noaa'] for hora in dados if hora['time'].startswith(data_alvo)]
    return round(sum(valores) / len(valores), 1) if valores else 0

def minimo_por_dia(dados, campo, data_alvo):
    valores = [hora[campo]['noaa'] for hora in dados if hora['time'].startswith(data_alvo)]
    return round(min(valores), 1) if valores else 0

def maximo_por_dia(dados, campo, data_alvo):
    valores = [hora[campo]['noaa'] for hora in dados if hora['time'].startswith(data_alvo)]
    return round(max(valores), 1) if valores else 0

def montar_previsao(data_iso):
    dia = datetime.strptime(data_iso, "%Y-%m-%d")
    vento_val = media_por_dia(dados, "windSpeed", data_iso)
    direcao = next((hora["windDirection"]["noaa"] for hora in dados if hora["time"].startswith(data_iso)), None)
    chuva = media_por_dia(dados, "precipitation", data_iso)
    nuvens = media_por_dia(dados, "cloudCover", data_iso)
    lua_valor = next((d["moonPhase"] for d in dados_lua if d["time"].startswith(data_iso)), None)
    if isinstance(lua_valor, dict):
        lua_valor = lua_valor.get("noaa", 0)

    return {
        "data": dia.strftime("%d/%m"),
        "icone": icone_clima(nuvens, chuva),
        "lua": icone_lua(lua_valor),
        "vento": f"<span class='arrow'>{seta_vento(direcao)}</span><span class='value'> {vento_val}</span><span class='unit'> km/h</span>",
        "temp_linha": (
            "<img src='seta_vermelha.png' width='17' height='17' style='vertical-align:middle;'/>"
            f"<span class='value'>{maximo_por_dia(dados, 'waterTemperature', data_iso)}</span>"
            "<span class='unit'>Â°C</span><br>"
            "<img src='seta_azul.png' width='17' height='17' style='vertical-align:middle;'/>"
            f"<span class='value'>{minimo_por_dia(dados, 'waterTemperature', data_iso)}</span>"
            "<span class='unit'>Â°C</span>"
        ),
        "pressao_linha": (
            "<img src='seta_vermelha.png' width='17' height='17' style='vertical-align:middle;'/>"
            f"<span class='value'>{maximo_por_dia(dados, 'pressure', data_iso)}</span>"
            "<span class='unit'>hPa</span><br>"
            "<img src='seta_azul.png' width='17' height='17' style='vertical-align:middle;'/>"
            f"<span class='value'>{minimo_por_dia(dados, 'pressure', data_iso)}</span>"
            "<span class='unit'>hPa</span>"
        )
    }

previsao = {
    "sabado": montar_previsao(data_sabado),
    "domingo": montar_previsao(data_domingo)
}

def gerar_card(dia, dados):
    return f"""<div class="card">
        <h2>{dia.upper()}<br>{dados['data']}</h2>
        <div class="icon-row">{dados['icone']} {dados['lua']}</div>
        <div class="info-grid">
            <div class="info-box" style="grid-column: span 2;">{dados['vento']}</div>
            <div class="info-box" style="grid-column: span 2;">{dados['temp_linha']}</div>
            <div class="info-box" style="grid-column: span 2;">{dados['pressao_linha']}</div>
        </div>
    </div>"""

with open("index_base.html", "r", encoding="utf-8") as base:
    html_base = base.read()

html_cards = gerar_card("SÃ¡bado", previsao["sabado"]) + gerar_card("Domingo", previsao["domingo"])
html_final = html_base.replace("{{PREVISAO_PESCARIA}}", html_cards)

with open("index.html", "w", encoding="utf-8") as saida:
    saida.write(html_final)
