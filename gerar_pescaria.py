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
    # CORREÇÃO: Usando os símbolos de seta corretos (Unicode)
    direcoes = {
        (337.5, 360): "↓", (0, 22.5): "↓",
        (22.5, 67.5): "↙",
        (67.5, 112.5): "←",
        (112.5, 157.5): "↖",
        (157.5, 202.5): "↑",
        (202.5, 247.5): "↗",
        (247.5, 292.5): "→",
        (292.5, 337.5): "↘",
    }
    for range_graus, seta in direcoes.items():
        if range_graus[0] <= angulo < range_graus[1]:
            return seta
    return "↓" # Retorna um padrão caso não encontre

def media_por_dia(dados, campo, data_alvo):
    valores = [hora[campo]['noaa'] for hora in dados if hora['time'].startswith(data_alvo)]
    return round(sum(valores) / len(valores), 1) if valores else 0

def minimo_por_dia(dados, campo, data_alvo):
    valores = [hora[campo]['noaa'] for hora in dados if hora['time'].startswith(data_alvo)]
    return round(min(valores), 1) if valores else 0

def maximo_por_dia(dados, campo, data_alvo):
    valores = [hora[campo]['noaa'] for hora in dados if hora['time'].startswith(data_alvo)]
    return round(max(valores), 1) if valores else 0

def pegar_mares_com_icone(data_iso):
    eventos = [e for e in tide_json["data"] if e["time"].startswith(data_iso)]
    mares_formatados = []
    for evento in eventos[:4]:
        hora = datetime.strptime(evento["time"], "%Y-%m-%dT%H:%M:%S+00:00")
        icone = "seta cima.png" if evento["type"] == "high" else "seta baixo.png"
        mares_formatados.append((icone, hora.strftime("%H:%M")))
    while len(mares_formatados) < 4:
        mares_formatados.append(("seta baixo.png", "--:--"))
    return mares_formatados

def avaliar_condicao_pescaria(data_iso, dados, media_por_dia):
    fases = ["nova", "crescente", "crescente", "crescente", "cheia", "minguante", "minguante", "minguante"]
    data_fase_conhecida = datetime(2025, 4, 29, 6, 0)
    ciclo_lunar_dias = 29 + 12 / 24 + 44 / 1440
    data_alvo = datetime.strptime(data_iso, "%Y-%m-%d")
    dias_diferenca = (data_alvo - data_fase_conhecida).total_seconds() / 86400
    dias_diferenca = dias_diferenca % ciclo_lunar_dias
    fase_index = int((dias_diferenca / ciclo_lunar_dias) * 8) % 8
    fase = fases[fase_index]

    temp = media_por_dia(dados, "waterTemperature", data_iso)
    pressao = media_por_dia(dados, "pressure", data_iso)

    if fase == "cheia" and 22 <= temp <= 26 and 1012 <= pressao <= 1018:
        return "pesca1 otima.png"
    if fase == "crescente" and (temp < 18 or temp > 30) and (pressao < 1005 or pressao > 1025):
        return "pesca5 pessima.png"

    nota = 0
    if fase == "nova": nota += 3
    elif fase == "minguante": nota += 2
    elif fase == "crescente": nota += 1

    if 20 <= temp < 22 or 26 < temp <= 28: nota += 3
    elif 18 <= temp < 20 or 28 < temp <= 30: nota += 2
    elif 16 <= temp < 18 or 30 < temp <= 32: nota += 1

    if 1008 <= pressao < 1012 or 1018 < pressao <= 1022: nota += 3
    elif 1005 <= pressao < 1008 or 1022 < pressao <= 1025: nota += 2
    elif 995 <= pressao < 1005 or 1025 < pressao <= 1030: nota += 1

    if nota >= 8: return "pesca2 boa.png"
    elif nota >= 5: return "pesca3 media.png"
    else: return "pesca4 ruim.png"

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
            # CORREÇÃO: Trocado 'Â°C' por '°C'
            f"<div><img src='seta cima.png' width='14px'/> <span class='value'>{maximo_por_dia(dados, 'waterTemperature', data_iso)}</span> <span class='unit'>°C</span></div>"
            f"<div><img src='seta baixo.png' width='14px'/> <span class='value'>{minimo_por_dia(dados, 'waterTemperature', data_iso)}</span> <span class='unit'>°C</span></div>"
        ),
        "pressao_linha": (
            f"<div><img src='seta cima.png' width='14px'/> <span class='value'>{maximo_por_dia(dados, 'pressure', data_iso)}</span> <span class='unit'>hPa</span></div>"
            f"<div><img src='seta baixo.png' width='14px'/> <span class='value'>{minimo_por_dia(dados, 'pressure', data_iso)}</span> <span class='unit'>hPa</span></div>"
        ),
        "mares": pegar_mares_com_icone(data_iso),
        "nota_geral": avaliar_condicao_pescaria(data_iso, dados, media_por_dia)
    }

previsao = {
    "sabado": montar_previsao(data_sabado),
    "domingo": montar_previsao(data_domingo)
}

def gerar_card(dia, dados):
    # CORREÇÃO: Trocado 'marÃ©s' por 'Marés' e corrigido o título do dia
    dia_corrigido = "SÁBADO" if "sabado" in dia.lower() else dia.upper()
    return f"""<div class="card">
        <h2>{dia_corrigido}&nbsp;&nbsp;{dados['data']}</h2>
        <div class="card-content">
            <div class="col-esq">
                <div class="icon-line"><img src="{dados['icone']}" width="40px" height="45px"/></div>
                <div class="line">{dados['vento']}</div>
                <div class="line">{dados['temp_linha']}</div>
                <div class="line">{dados['pressao_linha']}</div>
            </div>
            <div class="col-dir">
                <div class="icon-line"><img src="{dados['lua']}" width="35px" height="35px"/></div>
                <div class="mare-linha" style="font-size: 18px; margin-bottom: 4px;">Marés</div>
                <div class="hora-mare-dupla">
                    <span><img src="{dados['mares'][0][0]}" width="14px"/> {dados['mares'][0][1]}</span>
                    <span><img src="{dados['mares'][1][0]}" width="14px"/> {dados['mares'][1][1]}</span>
                </div>
                <div class="hora-mare-dupla">
                    <span><img src="{dados['mares'][2][0]}" width="14px"/> {dados['mares'][2][1]}</span>
                    <span><img src="{dados['mares'][3][0]}" width="14px"/> {dados['mares'][3][1]}</span>
                </div>
                <div class="icon-line" style="margin-top: 8px;">
                    <img src="{dados['nota_geral']}" width="80px" height="90px"/>
                </div>
            </div>
        </div>
    </div>"""

with open("index_base.html", "r", encoding="utf-8") as base:
    html_base = base.read()

html_cards = gerar_card("SÃ¡bado", previsao["sabado"]) + gerar_card("Domingo", previsao["domingo"])
html_final = html_base.replace("{{PREVISAO_PESCARIA}}", html_cards)

with open("index.html", "w", encoding="utf-8") as saida:
    saida.write(html_final)
