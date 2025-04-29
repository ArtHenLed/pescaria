from datetime import datetime, timedelta

# Dados fictícios simulados para sábado e domingo
previsao = {
    "sabado": {
        "data": (datetime.now() + timedelta(days=(5 - datetime.now().weekday()) % 7)).strftime("%d/%m"),
        "vento": "12 km/h NE",
        "temp_agua": "22,5 °C",
        "pressao": "1013 hPa",
        "lua": "Quarto crescente",
        "icone": "☀️"
    },
    "domingo": {
        "data": (datetime.now() + timedelta(days=(6 - datetime.now().weekday()) % 7)).strftime("%d/%m"),
        "vento": "14 km/h NO",
        "temp_agua": "22,8 °C",
        "pressao": "1016 hPa",
        "lua": "Quarto crescente",
        "icone": "🌥️"
    }
}

# Gera HTML para cada card
def gerar_card(dia, dados):
    return f"""
    <div class="container">
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

# Monta cards lado a lado
html_cards = f"""
<div class="container">
  <div class="card">{gerar_card("Sábado", previsao['sabado'])}</div>
  <div class="card">{gerar_card("Domingo", previsao['domingo'])}</div>
</div>
"""

# Substitui e salva final
html_final = html_base.replace("{{PREVISAO_PESCARIA}}", html_cards)

with open("index.html", "w", encoding="utf-8") as saida:
    saida.write(html_final)
