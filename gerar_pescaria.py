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

try:
    weather_response = requests.get("https://api.stormglass.io/v2/weather/point", params={"lat": LATITUDE, "lng": LONGITUDE, "params": "waterTemperature,windSpeed,windDirection,pressure,cloudCover,precipitation", "start": f"{data_sabado}T00:00:00+00:00", "end": f"{data_domingo}T23:59:59+00:00", "source": "noaa"}, headers={"Authorization": API_KEY})
    weather_response.raise_for_status()
    astro_response = requests.get("https://api.stormglass.io/v2/astronomy/point", params={"lat": LATITUDE, "lng": LONGITUDE, "start": f"{data_sabado}T00:00:00+00:00", "end": f"{data_domingo}T23:59:59+00:00"}, headers={"Authorization": API_KEY})
    astro_response.raise_for_status()
    tide_response = requests.get("https://api.stormglass.io/v2/tide/extremes/point", params={"lat": LATITUDE, "lng": LONGITUDE, "start": f"{data_sabado}T00:00:00+00:00", "end": f"{data_domingo}T23:59:59+00:00"}, headers={"Authorization": API_KEY})
    tide_response.raise_for_status()
    weather_json = weather_response.json()
    astro_json = astro_response.json()
    tide_json = tide_response.json()
except requests.exceptions.RequestException as e:
    print(f"Erro de conexão com a API: {e}")
    exit(1)

if "hours" not in weather_json or "data" not in astro_json or "data" not in tide_json:
    print("Erro: Resposta da API não contém os dados esperados.")
    exit(1)

dados = weather_json["hours"]

def icone_clima(prec, cloud):
    if prec > 2 and cloud > 70: return "chuva com raio.png"
    elif prec > 1: return "chuva.png"
    elif cloud > 70: return "nublado.png"
    elif cloud > 50: return "sol e nublado.png"
    else: return "sol.png"

def icone_lua(data_str):
    fases = ["lua nova.png", "lua crescente.png", "lua quarto crescente.png", "lua gibosa crescente.png", "lua cheia.png", "lua gibosa minguante.png", "lua quarto minguante.png", "lua minguante.png"]
    data_fase_conhecida = datetime(2025, 4, 29, 6, 0)
    ciclo_lunar_dias = 29.530588853
    data_alvo = datetime.strptime(data_str, "%Y-%m-%d")
    dias_diferenca = (data_alvo - data_fase_conhecida).total_seconds() / 86400
    fase_index = int((dias_diferenca % ciclo_lunar_dias) / ciclo_lunar_dias * 8)
    return fases[fase_index]

def seta_vento(angulo):
    if angulo is None: return " "
    direcoes = {(337.5, 360): "↓", (0, 22.5): "↓", (22.5, 67.5): "↙", (67.5, 112.5): "←", (112.5, 157.5): "↖", (157.5, 202.5): "↑", (202.5, 247.5): "↗", (247.5, 292.5): "→", (292.5, 337.5): "↘"}
    for range_graus, seta in direcoes.items():
        if range_graus[0] <= angulo < range_graus[1]: return seta
    return "↓"

def media_por_dia(dados, campo, data_alvo):
    valores = [hora[campo]['noaa'] for hora in dados if hora['time'].startswith(data_alvo)]
    return round(sum(valores) / len(valores), 1) if valores else 0

def minimo_por_dia(dados, campo, data_alvo):
    valores = [hora[campo]['noaa'] for hora in dados if hora['time'].startswith(data_alvo)]
    return round(min(valores), 1) if valores else 0

def maximo_por_dia(dados, campo, data_alvo):
    valores = [hora[campo]['noaa'] for hora in dados if hora['time'].startswith(data_alvo)]
    return round(max(valores), 1) if valores else 0

def pegar_mares
