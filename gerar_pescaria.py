import requests
import datetime
import os

def fase_lua(valor):
    if valor < 0.1:
        return "Lua Nova"
    elif valor < 0.25:
        return "Crescente"
    elif valor < 0.5:
        return "Quarto Crescente"
    elif valor < 0.6:
        return "Lua Cheia"
    elif valor < 0.75:
        return "Minguante"
    else:
        return "Quarto Minguante"

def gerar_card(dia, dados):
    return f'''
    <div class="container">
        <div class="card">
            <h2>{dia.upper()}</h2>
            <div class="icon">{dados['icone']}</div>
            <p class="info-box">
                <span>Vento<br>{dados['vento']}</span>
                <span>Temp. água<br>{dados['temp_agua']}</span>
                <span>Pressão<br>{dados['pressao']}</span>
                <span>{dados['lua']}</span>
            </p>
        </div>
    </div>
    '''

def montar_previsao(data):
    data_str = data.strftime('%Y-%m-%d')
    url = "https://api.stormglass.io/v2/weather/point"

    params = {
        'lat': -24.730,
        'lng': -47.550,
        'params': ','.join([
            'waterTemperature', 'windSpeed', 'pressure', 'moonPhase'
        ]),
        'start': f"{data_str}T00:00:00+00:00",
        'end': f"{data_str}T23:59:59+00:00",
        'source': 'noaa'
    }

    headers = {
        'Authorization': os.getenv('STORMGLASS_API_KEY')
    }

    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200:
        print(f"Erro na requisição: {response.status_code}")
        print("Resposta:", response.text)
        exit(1)

    response_json = response.json()

    if 'hours' not in response_json or len(response_json['hours']) == 0:
        print("Erro: resposta sem campo 'hours'")
        print("Resposta completa:", response_json)
        exit(1)

    dados = response_json['hours'][0]  # Pega o primeiro horário do dia

    return {
        'data': data.strftime('%d/%m'),
        'icone': '☀️',
        'vento': f"{round(dados['windSpeed']['noaa'], 1)} km/h",
        'temp_agua': f"{round(dados['waterTemperature']['noaa'], 1)} °C",
        'pressao': f"{round(dados['pressure']['noaa'], 1)} hPa",
        'lua': fase_lua(dados['moonPhase']['noaa'])
    }

# Gerar cards para sábado e domingo
hoje = datetime.datetime.now()
sabado = hoje + datetime.timedelta((5 - hoje.weekday()) % 7)
domingo = hoje + datetime.timedelta((6 - hoje.weekday()) % 7)

data_sabado = montar_previsao(sabado)
data_domingo = montar_previsao(domingo)

html_cards = f"""
<div class='card-container'>
    {gerar_card('Sábado', data_sabado)}
    {gerar_card('Domingo', data_domingo)}
</div>
"""

# Carregar HTML base
with open("index_base.html", "r", encoding="utf-8") as base:
    html_base = base.read()

html_final = html_base.replace("{{PREVISAO_PESCARIA}}", html_cards)

# Salvar resultado
with open("index.html", "w", encoding="utf-8") as saida:
    saida.write(html_final)

print("Previsão de pescaria gerada com sucesso!")
