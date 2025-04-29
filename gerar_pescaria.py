import requests
import datetime
import os

def obter_previsao(dia):
    latitude = -24.7300
    longitude = -47.5500
    api_key = os.environ["STORMGLASS_API_KEY"]

    data_inicio = dia.isoformat()
    data_fim = (dia + datetime.timedelta(days=1)).isoformat()

    parametros = ['waterTemperature', 'windSpeed', 'moonPhase', 'pressure']

    url = f'https://api.stormglass.io/v2/weather/point'
    headers = {'Authorization': api_key}
    params = {
        'lat': latitude,
        'lng': longitude,
        'params': ','.join(parametros),
        'start': data_inicio,
        'end': data_fim,
        'source': 'noaa'
    }

    response = requests.get(url, headers=headers, params=params)
    response_json = response.json()

    if "hours" not in response_json:
        print("Erro: resposta sem campo 'hours'")
        print("Resposta completa:", response_json)
        exit(1)

    dados = response_json["hours"]

    hora_alvo = 12  # meio-dia UTC
    for hora in dados:
        timestamp = hora["time"]
        hora_dt = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if hora_dt.hour == hora_alvo:
            vento = hora.get("windSpeed", {}).get("noaa", 0)
            agua = hora.get("waterTemperature", {}).get("noaa", 0)
            pressao = hora.get("pressure", {}).get("noaa", 0)
            lua_valor = hora.get("moonPhase", {}).get("noaa", 0)

            return {
                "data": hora_dt.strftime("%d/%m"),
                "icone": "☀️",
                "vento": f"{vento:.1f} km/h",
                "temp_agua": f"{agua:.1f} °C",
                "pressao": f"{pressao:.1f} hPa",
                "lua": fase_lua_por_valor(lua_valor)
            }

    return {
        "data": dia.strftime("%d/%m"),
        "icone": "❓",
        "vento": "--",
        "temp_agua": "--",
        "pressao": "--",
        "lua": "--"
    }

def fase_lua_por_valor(valor):
    if valor < 0.1 or valor > 0.9:
        return "Lua Nova"
    elif 0.1 <= valor < 0.25:
        return "Crescente"
    elif 0.25 <= valor < 0.45:
        return "Quarto Crescente"
    elif 0.45 <= valor < 0.55:
        return "Lua Cheia"
    elif 0.55 <= valor < 0.75:
        return "Minguante"
    elif 0.75 <= valor <= 0.9:
        return "Quarto Minguante"
    else:
        return "Desconhecida"

def gerar_card(dia_semana, dados):
    return f"""
    <div class="card">
      <h2>{dia_semana.upper()}</h2>
      <div class="date">{dados['data']}</div>
      <div class="icon">{dados['icone']}</div>
      <div class="grid">
        <div>🌀 {dados['vento']}</div>
        <div>🌡️ {dados['temp_agua']}</div>
        <div>⚖️ {dados['pressao']}</div>
        <div>🌕 {dados['lua']}</div>
      </div>
    </div>
    """

# Calcular sábado e domingo mais próximos
hoje = datetime.date.today()
dias_ate_sabado = (5 - hoje.weekday()) % 7
dias_ate_domingo = (6 - hoje.weekday()) % 7
sabado = hoje + datetime.timedelta(days=dias_ate_sabado)
domingo = hoje + datetime.timedelta(days=dias_ate_domingo)

previsao = {
    "sabado": obter_previsao(sabado),
    "domingo": obter_previsao(domingo)
}

html_cards = f"""
<div class="container">
  {gerar_card("Sábado", previsao['sabado'])}
  {gerar_card("Domingo", previsao['domingo'])}
</div>
"""

with open("index_base.html", "r", encoding="utf-8") as base:
    html_base = base.read()

html_final = html_base.replace("{{PREVISAO_PESCARIA}}", html_cards)

with open("index.html", "w", encoding="utf-8") as saida:
    saida.write(html_final)
