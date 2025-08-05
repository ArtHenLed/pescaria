from datetime import datetime, timedelta
import os
import requests

LATITUDE = -24.7300
LONGITUDE = -47.5500
API_KEY = os.getenv("STORMGLASS_API_KEY")

# Obter a data atual em UTC
hoje = datetime.utcnow()

# Calcular os dias até o próximo sábado e domingo
dias_ate_sabado = (5 - hoje.weekday()) % 7
dias_ate_domingo = (6 - hoje.weekday()) % 7

# Formatar as datas para as requisições da API
data_sabado = (hoje + timedelta(days=dias_ate_sabado)).strftime("%Y-%m-%d")
data_domingo = (hoje + timedelta(days=dias_ate_domingo)).strftime("%Y-%m-%d")

# --- Requisições à API Stormglass ---

# Requisição para dados de clima
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

# Requisição para dados astronômicos (inclui fase da lua)
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

# Requisição para dados de marés
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

# Converter as respostas para JSON
weather_json = weather_response.json()
astro_json = astro_response.json()
tide_json = tide_response.json()

# Verificar se os dados essenciais foram obtidos
if "hours" not in weather_json or "data" not in astro_json or "data" not in tide_json:
    print("Erro ao obter dados da API. Verifique a chave da API ou os parâmetros.")
    exit(1)

dados = weather_json["hours"]

# --- Funções de processamento de dados ---

def icone_clima(prec, cloud):
    """Retorna o nome do arquivo de ícone de clima com base na precipitação e cobertura de nuvens."""
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

def icone_lua(data_str, astro_data):
    """
    Retorna o nome do arquivo de ícone da lua com base na fase da lua obtida da API.
    A API Stormglass retorna: newMoon, waxingCrescent, firstQuarter, waxingGibbous,
    fullMoon, waningGibbous, lastQuarter, waningCrescent.
    """
    moon_phase_value = None
    # Percorre os dados astronômicos para encontrar a fase da lua para a data específica
    for day_data in astro_data["data"]:
        if day_data["time"].startswith(data_str):
            moon_phase_value = day_data["moonPhase"]["value"]
            break

    # Mapeia os valores da API para os nomes dos seus arquivos de imagem
    mapping = {
        "newMoon": "lua nova.png",
        "waxingCrescent": "lua crescente.png",
        "firstQuarter": "lua quarto crescente.png",
        "waxingGibbous": "lua gibosa crescente.png",
        "fullMoon": "lua cheia.png",
        "waningGibbous": "lua gibosa minguante.png",
        "lastQuarter": "lua quarto minguante.png",
        "waningCrescent": "lua minguante.png"
    }
    # Retorna o ícone correspondente ou um ícone padrão se a fase não for encontrada
    return mapping.get(moon_phase_value, "lua desconhecida.png")

def seta_vento(angulo):
    """Retorna um emoji de seta direcional com base no ângulo do vento."""
    if angulo is None:
        return ""
    direcoes = [(0, "⬇️"), (45, "↙️"), (90, "⬅️"), (135, "↖️"), (180, "⬆️"),
                (225, "↗️"), (270, "➡️"), (315, "↘️"), (360, "⬇️")]
    for i in range(len(direcoes) - 1):
        if direcoes[i][0] <= angulo < direcoes[i + 1][0]:
            return direcoes[i][1]
    return ""

def media_por_dia(dados, campo, data_alvo):
    """Calcula a média de um campo específico para uma dada data."""
    valores = [hora[campo]['noaa'] for hora in dados if hora['time'].startswith(data_alvo)]
    return round(sum(valores) / len(valores), 1) if valores else 0

def minimo_por_dia(dados, campo, data_alvo):
    """Encontra o valor mínimo de um campo específico para uma dada data."""
    valores = [hora[campo]['noaa'] for hora in dados if hora['time'].startswith(data_alvo)]
    return round(min(valores), 1) if valores else 0

def maximo_por_dia(dados, campo, data_alvo):
    """Encontra o valor máximo de um campo específico para uma dada data."""
    valores = [hora[campo]['noaa'] for hora in dados if hora['time'].startswith(data_alvo)]
    return round(max(valores), 1) if valores else 0

def pegar_mares_com_icone(data_iso):
    """Formata os horários das marés com seus respectivos ícones."""
    eventos = [e for e in tide_json["data"] if e["time"].startswith(data_iso)]
    mares_formatados = []
    # Limita a 4 eventos de maré para exibir
    for evento in eventos[:4]:
        hora = datetime.strptime(evento["time"], "%Y-%m-%dT%H:%M:%S+00:00")
        icone = "seta cima.png" if evento["type"] == "high" else "seta baixo.png"
        mares_formatados.append((icone, hora.strftime("%H:%M")))
    # Preenche com valores vazios se houver menos de 4 eventos
    while len(mares_formatados) < 4:
        mares_formatados.append(("seta baixo.png", "--:--"))
    return mares_formatados

def avaliar_condicao_pescaria(data_iso, dados, media_por_dia, astro_data):
    """
    Avalia a condição de pescaria com base na fase da lua (obtida da API),
    temperatura da água e pressão atmosférica.
    """
    moon_phase_value = None
    # Obtém a fase da lua da resposta da API de astronomia
    for day_data in astro_data["data"]:
        if day_data["time"].startswith(data_iso):
            moon_phase_value = day_data["moonPhase"]["value"]
            break

    if moon_phase_value is None:
        return "pesca4 ruim.png" # Retorna ruim se a fase da lua não for encontrada

    # Simplifica as fases da lua para a lógica de avaliação
    fase = ""
    if moon_phase_value == "newMoon":
        fase = "nova"
    elif moon_phase_value in ["waxingCrescent", "firstQuarter", "waxingGibbous"]:
        fase = "crescente"
    elif moon_phase_value == "fullMoon":
        fase = "cheia"
    elif moon_phase_value in ["waningGibbous", "lastQuarter", "waningCrescent"]:
        fase = "minguante"

    temp = media_por_dia(dados, "waterTemperature", data_iso)
    pressao = media_por_dia(dados, "pressure", data_iso)

    # Lógica de avaliação da pescaria
    if fase == "cheia" and 22 <= temp <= 26 and 1012 <= pressao <= 1018:
        return "pesca1 otima.png"
    if fase == "crescente" and (temp < 18 or temp > 30) and (pressao < 1005 or pressao > 1025):
        return "pesca5 pessima.png"

    nota = 0
    if fase == "nova": nota += 3
    elif fase == "minguante": nota += 2
    elif fase == "crescente": nota += 1 # Agora inclui todas as fases crescentes

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
    """Monta um dicionário com todos os dados da previsão para um dia específico."""
    dia = datetime.strptime(data_iso, "%Y-%m-%d")
    vento_val = media_por_dia(dados, "windSpeed", data_iso)
    direcao = next((hora["windDirection"]["noaa"] for hora in dados if hora["time"].startswith(data_iso)), None)
    cloud = media_por_dia(dados, "cloudCover", data_iso)
    prec = media_por_dia(dados, "precipitation", data_iso)
    return {
        "data": dia.strftime("%d/%m"),
        "icone": icone_clima(prec, cloud),
        "lua": icone_lua(data_iso, astro_json), # Passa astro_json para a função icone_lua
        "vento": f"<span class='arrow'>{seta_vento(direcao)}</span> <span class='value'>{vento_val}</span> <span class='unit'>km/h</span>",
        "temp_linha": (
            f"<div><img src='seta cima.png' width='14px'/> <span class='value'>{maximo_por_dia(dados, 'waterTemperature', data_iso)}</span> <span class='unit'>°C</span></div>"
            f"<div><img src='seta baixo.png' width='14px'/> <span class='value'>{minimo_por_dia(dados, 'waterTemperature', data_iso)}</span> <span class='unit'>°C</span></div>"
        ),
        "pressao_linha": (
            f"<div><img src='seta cima.png' width='14px'/> <span class='value'>{maximo_por_dia(dados, 'pressure', data_iso)}</span> <span class='unit'>hPa</span></div>"
            f"<div><img src='seta baixo.png' width='14px'/> <span class='value'>{minimo_por_dia(dados, 'pressure', data_iso)}</span> <span class='unit'>hPa</span></div>"
        ),
        "mares": pegar_mares_com_icone(data_iso),
        "nota_geral": avaliar_condicao_pescaria(data_iso, dados, media_por_dia, astro_json) # Passa astro_json para a função avaliar_condicao_pescaria
    }

# Montar as previsões para sábado e domingo
previsao = {
    "sabado": montar_previsao(data_sabado),
    "domingo": montar_previsao(data_domingo)
}

# --- Geração do HTML ---

def gerar_card(dia, dados):
    """Gera o HTML para um card de previsão de pescaria."""
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
                <div class="mare-linha" style="font-size: 18px; margin-bottom: 4px;">marés</div>
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

# Carregar o template HTML base
with open("index_base.html", "r", encoding="utf-8") as base:
    html_base = base.read()

# Gerar os cards de previsão e inserir no HTML base
html_cards = gerar_card("Sábado", previsao["sabado"]) + gerar_card("Domingo", previsao["domingo"])
html_final = html_base.replace("{{PREVISAO_PESCARIA}}", html_cards)

# Salvar o HTML final em um arquivo
with open("index.html", "w", encoding="utf-8") as saida:
    saida.write(html_final)
