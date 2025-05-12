from datetime import datetime, timedelta
import os
import requests

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

tide_response = requests.get(
    "https://api.stormglass.io/v2/tide/extremes/point",
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
tide_json = tide_response.json()

if "hours" not in weather_json or "data" not in astro_json or "data" not in tide_json:
    print("Erro ao obter dados da API")
    exit(1)

dados = weather_json["hours"]

def icone_clima(prec, cloud):
    if prec > 2 and cloud > 70:
        return "chuva com raio.png"
    elif prec > 1:
        return "chuva.png"
    elif cloud > 70:
        return "nublado.png"
    elif cloud > 50:
        return "sol e nublado.png"
    else:
        return "sol.png"

def icone_lua(data_str):
    fases = [
        "lua nova.png",
        "lua crescente.png",
        "lua quarto crescente.png",
        "lua gibosa crescente.png",
        "lua cheia.png",
        "lua gibosa minguante.png",
        "lua quarto minguante.png",
        "lua minguante.png"
    ]
    data_fase_conhecida = datetime(2025, 4, 29, 6, 0)
    ciclo_lunar_dias = 29 + 12 / 24 + 44 / 1440
    data_alvo = datetime.strptime(data_str, "%Y-%m-%d")
    dias_diferenca = (data_alvo - data_fase_conhecida).total_seconds() / 86400
    dias_diferenca = dias_diferenca % ciclo_lunar_dias
    fase_index = int((dias_diferenca / ciclo_lunar_dias) * 8) % 8
    return fases[fase_index]

def seta_vento(angulo):
    if angulo is None:
        return ""
    direcoes = [(0, "⬇️"), (45, "↙️"), (90, "⬅️"), (135, "↖️"), (180, "⬆️"),
                (225, "↗️"), (270, "➡️"), (315, "↘️"), (360, "⬇️")]
    for i in range(len(direcoes) - 1):
        if direcoes[i][0] <= angulo < direcoes[i + 1][0]:
            return direcoes[i][1]
    return ""

def media_por_dia(dados, campo, data_alvo):
    valores = [hora[campo]['noaa'] for hora in dados if hora['time'].startswith(data_alvo)]
    return round(sum(valores) / len(valores), 1) if valores else 0

def minimo_por_dia(dados, campo, data_alvo):
    valores = [hora[campo]['noaa'] for hora in dados if hora['time'].startswith(data_alvo)]
    return round(min(valores), 1) if valores else 0

def maximo_por_dia(dados, campo, data_alvo):
    valores = [hora[campo]['noaa'] for hora in dados if hora['time'].startswith(data_alvo)]
    return round(max(valores), 1) if valores else 0

def pegar_mares(data_iso, tipo):
    eventos = [e for e in tide_json["data"] if e["type"] == tipo and e["time"].startswith(data_iso)]
    mares = []
    for evento in eventos[:2]:
        hora = datetime.strptime(evento["time"], "%Y-%m-%dT%H:%M:%S+00:00")
       mares.append(f"{hora.hour:02}:{hora.minute:02}")
    while len(mares) < 2:
        mares.append("--:--")
    return mares

def montar_previsao(data_iso):
    dia = datetime.strptime(data_iso, "%Y-%m-%d")
    vento_val = media_por_dia(dados, "windSpeed", data_iso)
    direcao = next((hora["windDirection"]["noaa"] for hora in dados if hora["time"].startswith(data_iso)), None)
    cloud = media_por_dia(dados, "cloudCover", data_iso)
    prec = media_por_dia(dados, "precipitation", data_iso)
    return {
        "data": dia.strftime("%d/%m"),
        "icone": icone_clima(prec, cloud),
        "lua": icone_lua(data_iso),
        "vento": f"<span class='arrow'>{seta_vento(direcao)}</span> <span class='value'>{vento_val}</span> <span class='unit'>km/h</span>",
        "temp_linha": (
            f"<div><img src='seta cima.png' width='14px'/> <span class='value'>{maximo_por_dia(dados, 'waterTemperature', data_iso)}</span> <span class='unit'>°C</span></div>"
            f"<div><img src='seta baixo.png' width='14px'/> <span class='value'>{minimo_por_dia(dados, 'waterTemperature', data_iso)}</span> <span class='unit'>°C</span></div>"
        ),
        "pressao_linha": (
            f"<div><img src='seta cima.png' width='14px'/> <span class='value'>{maximo_por_dia(dados, 'pressure', data_iso)}</span> <span class='unit'>hPa</span></div>"
            f"<div><img src='seta baixo.png' width='14px'/> <span class='value'>{minimo_por_dia(dados, 'pressure', data_iso)}</span> <span class='unit'>hPa</span></div>"
        ),
        "mares_altas": pegar_mares(data_iso, "high"),
        "mares_baixas": pegar_mares(data_iso, "low")
    }

previsao = {
    "sabado": montar_previsao(data_sabado),
    "domingo": montar_previsao(data_domingo)
}

def gerar_card(dia, dados):
    return f"""<div class="card">
        <h2>{dia.upper()}&nbsp;&nbsp;{dados['data']}</h2>
        <div class="card-content">
            <div class="col-esq">
                <div class="icon-line"><img src="{dados['icone']}" width="40px" height="45px"/></div>
                <div class="line">{dados['vento']}</div>
                <div class="line">{dados['temp_linha']}</div>
                <div class="line">{dados['pressao_linha']}</div>
            </div>
            <div class="col-dir">
                <div class="icon-line"><img src="{dados['lua']}" width="35px" height="35px"/></div>
                <div class="mare-linha"><img src='seta cima.png' width='14px' height='14px'/> maré</div>
                <div class="hora-mare-dupla">
                  <span>{dados['mares_altas'][0]}</span>
                  <span>{dados['mares_altas'][1]}</span>
                </div>
                <div class="mare-linha"><img src='seta baixo.png' width='14px' height='14px'/> maré</div>
                <div class="hora-mare-dupla">
                  <span>{dados['mares_baixas'][0]}</span>
                  <span>{dados['mares_baixas'][1]}</span>
                </div>
            </div>
        </div>
    </div>"""

with open("index_base.html", "r", encoding="utf-8") as base:
    html_base = base.read()

html_cards = gerar_card("Sábado", previsao["sabado"]) + gerar_card("Domingo", previsao["domingo"])
html_final = html_base.replace("{{PREVISAO_PESCARIA}}", html_cards)

with open("index.html", "w", encoding="utf-8") as saida:
    saida.write(html_final)
