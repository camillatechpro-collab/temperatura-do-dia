"""
Bot de Clima
Consulta a previsão do tempo de uma cidade (API Open-Meteo, sem chave)
e envia um resumo para o Telegram e/ou Discord.

Uso:
    python bot.py                 # envia para os canais configurados
    python bot.py --dry-run       # apenas mostra a mensagem no terminal
    python bot.py --cidade "Recife"
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT = 15
USER_AGENT = "bot-clima/1.0"


def http_get(url: str, params: dict) -> dict:
    """GET que devolve o JSON da resposta (só biblioteca padrão)."""
    req = urllib.request.Request(
        f"{url}?{urllib.parse.urlencode(params)}", headers={"User-Agent": USER_AGENT}
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.load(resp)


def http_post_json(url: str, payload: dict) -> None:
    """POST com corpo JSON; levanta erro se o status não for 2xx."""
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT):
        pass

# Códigos de tempo da OMM usados pela Open-Meteo
CONDICOES = {
    0: ("☀️", "Céu limpo"),
    1: ("🌤️", "Predominantemente limpo"),
    2: ("⛅", "Parcialmente nublado"),
    3: ("☁️", "Nublado"),
    45: ("🌫️", "Neblina"),
    48: ("🌫️", "Neblina com geada"),
    51: ("🌦️", "Garoa fraca"),
    53: ("🌦️", "Garoa moderada"),
    55: ("🌦️", "Garoa forte"),
    61: ("🌧️", "Chuva fraca"),
    63: ("🌧️", "Chuva moderada"),
    65: ("🌧️", "Chuva forte"),
    80: ("🌦️", "Pancadas de chuva fracas"),
    81: ("🌧️", "Pancadas de chuva moderadas"),
    82: ("⛈️", "Pancadas de chuva fortes"),
    95: ("⛈️", "Trovoadas"),
    96: ("⛈️", "Trovoadas com granizo"),
    99: ("⛈️", "Trovoadas fortes com granizo"),
}


def buscar_coordenadas(cidade: str) -> dict:
    """Converte o nome da cidade em latitude/longitude."""
    dados = http_get(
        GEOCODING_URL,
        {"name": cidade, "count": 1, "language": "pt", "format": "json"},
    )
    resultados = dados.get("results")
    if not resultados:
        raise ValueError(f"Cidade não encontrada: {cidade}")
    return resultados[0]


def buscar_previsao(lat: float, lon: float) -> dict:
    """Busca o tempo atual e a previsão do dia."""
    return http_get(
        FORECAST_URL,
        {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,apparent_temperature,weather_code",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,"
            "precipitation_probability_max",
            "timezone": "auto",
            "forecast_days": 1,
        },
    )


def descrever(codigo: int) -> str:
    emoji, texto = CONDICOES.get(codigo, ("🌡️", "Condição desconhecida"))
    return f"{emoji} {texto}"


def montar_mensagem(local: dict, dados: dict) -> str:
    atual = dados["current"]
    dia = dados["daily"]
    chuva = dia["precipitation_probability_max"][0] or 0

    linhas = [
        f"📍 Previsão para {local['name']}, {local.get('admin1', '')}".rstrip(", "),
        "",
        f"Agora: {atual['temperature_2m']:.0f}°C "
        f"(sensação de {atual['apparent_temperature']:.0f}°C)",
        f"Hoje: {descrever(dia['weather_code'][0])}",
        f"🌡️ Mín {dia['temperature_2m_min'][0]:.0f}°C / "
        f"Máx {dia['temperature_2m_max'][0]:.0f}°C",
        f"💧 Chance de chuva: {chuva}%",
    ]
    if chuva >= 60:
        linhas += ["", "☂️ Não esqueça o guarda-chuva!"]
    return "\n".join(linhas)


def enviar_telegram(texto: str, token: str, chat_id: str) -> None:
    http_post_json(
        f"https://api.telegram.org/bot{token}/sendMessage",
        {"chat_id": chat_id, "text": texto},
    )


def enviar_discord(texto: str, webhook_url: str) -> None:
    http_post_json(webhook_url, {"content": texto})


def mostrar_chat_ids(token: str) -> int:
    """Lista os chats que mandaram mensagem ao bot, para achar o TELEGRAM_CHAT_ID."""
    dados = http_get(f"https://api.telegram.org/bot{token}/getUpdates", {})
    chats = {}
    for update in dados.get("result", []):
        msg = update.get("message") or update.get("channel_post") or {}
        chat = msg.get("chat")
        if chat:
            nome = chat.get("title") or chat.get("first_name") or chat.get("username")
            chats[chat["id"]] = nome
    if not chats:
        print("Nenhuma conversa encontrada. Mande um 'oi' para o seu bot e tente de novo.")
        return 1
    for chat_id, nome in chats.items():
        print(f"TELEGRAM_CHAT_ID={chat_id}   ({nome})")
    return 0


def main() -> int:
    # Garante que emojis e acentos apareçam bem no terminal do Windows
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    try:
        return executar()
    except urllib.error.HTTPError as erro:
        if erro.code in (401, 404) and "telegram" in erro.url:
            print("❌ Token do Telegram inválido. Confira o TELEGRAM_TOKEN.", file=sys.stderr)
        elif erro.code == 400 and "telegram" in erro.url:
            print(
                "❌ Chat ID inválido, ou você ainda não mandou mensagem para o bot.",
                file=sys.stderr,
            )
        else:
            print(f"❌ Erro HTTP {erro.code} ao acessar {erro.url.split('?')[0]}", file=sys.stderr)
        return 1
    except urllib.error.URLError as erro:
        print(f"❌ Falha de conexão: {erro.reason}", file=sys.stderr)
        return 1


def executar() -> int:
    parser = argparse.ArgumentParser(description="Bot de previsão do tempo")
    parser.add_argument("--cidade", default=os.getenv("CIDADE") or "São Paulo")
    parser.add_argument(
        "--dry-run", action="store_true", help="Só mostra a mensagem, sem enviar"
    )
    parser.add_argument(
        "--chat-id",
        action="store_true",
        help="Mostra o chat ID do Telegram (precisa do TELEGRAM_TOKEN)",
    )
    args = parser.parse_args()

    if args.chat_id:
        token = os.getenv("TELEGRAM_TOKEN")
        if not token:
            print("❌ Defina a variável TELEGRAM_TOKEN primeiro.", file=sys.stderr)
            return 1
        return mostrar_chat_ids(token)

    try:
        local = buscar_coordenadas(args.cidade)
    except ValueError as erro:
        print(f"❌ {erro}", file=sys.stderr)
        return 1
    dados = buscar_previsao(local["latitude"], local["longitude"])
    mensagem = montar_mensagem(local, dados)

    print(mensagem)
    if args.dry_run:
        return 0

    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    webhook = os.getenv("DISCORD_WEBHOOK_URL")

    enviados = 0
    if token and chat_id:
        enviar_telegram(mensagem, token, chat_id)
        print("\n✅ Enviado para o Telegram")
        enviados += 1
    if webhook:
        enviar_discord(mensagem, webhook)
        print("\n✅ Enviado para o Discord")
        enviados += 1

    if enviados == 0:
        print(
            "\n⚠️ Nenhum canal configurado. Defina TELEGRAM_TOKEN + TELEGRAM_CHAT_ID "
            "e/ou DISCORD_WEBHOOK_URL.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
