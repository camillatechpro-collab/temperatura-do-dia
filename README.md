# 🌦️ Temperatura do Dia

Bot em Python que consulta a previsão do tempo da sua cidade e envia um resumo diário para o **Telegram** e/ou **Discord**, rodando sozinho todo dia com **GitHub Actions**.

```
📍 Previsão para São Paulo

Agora: 22°C (sensação de 23°C)
Hoje: 🌧️ Chuva moderada
🌡️ Mín 17°C / Máx 26°C
💧 Chance de chuva: 80%

☂️ Não esqueça o guarda-chuva!
```

## ✨ Funcionalidades

- Busca a cidade pelo nome (geocodificação automática)
- Temperatura atual, sensação térmica, mínima e máxima
- Chance de chuva com alerta de guarda-chuva
- Envio para Telegram, Discord ou ambos
- Execução diária automática via GitHub Actions
- Usa a API gratuita [Open-Meteo](https://open-meteo.com/), que não precisa de chave

## 🛠️ Tecnologias

- Python 3 (só biblioteca padrão, sem dependências)
- Open-Meteo API
- Telegram Bot API / Discord Webhooks
- GitHub Actions

## 🚀 Como rodar localmente

```bash
# Só ver a mensagem, sem enviar:
python bot.py --dry-run --cidade "Recife"
```

Para enviar de verdade, defina as variáveis de ambiente (veja `.env.example`):

| Variável | Descrição |
|---|---|
| `CIDADE` | Nome da cidade (padrão: São Paulo) |
| `TELEGRAM_TOKEN` | Token do bot, criado no [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_CHAT_ID` | ID do chat que vai receber a mensagem |
| `DISCORD_WEBHOOK_URL` | URL do webhook do canal do Discord |

## 🤖 Criando o bot no Telegram

1. No Telegram, abra o [@BotFather](https://t.me/BotFather) e envie `/newbot`
2. Escolha um nome e um usuário terminado em `bot` (ex.: `meu_clima_bot`)
3. Copie o **token** que ele te enviar. Esse é o `TELEGRAM_TOKEN` (não compartilhe!)
4. Abra a conversa com o seu bot e mande qualquer mensagem (ex.: "oi")
5. Descubra o seu chat ID:

```bash
TELEGRAM_TOKEN="seu-token" python bot.py --chat-id
```

6. Teste o envio:

```bash
TELEGRAM_TOKEN="seu-token" TELEGRAM_CHAT_ID="seu-chat-id" python bot.py
```

## ⏰ Automação com GitHub Actions

O workflow em `.github/workflows/clima.yml` roda todo dia às 5h (horário de Brasília).

1. No repositório, vá em **Settings > Secrets and variables > Actions**
2. Em **Secrets**, adicione `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID` e/ou `DISCORD_WEBHOOK_URL`
3. Em **Variables**, adicione `CIDADE` (opcional)
4. Para testar, vá na aba **Actions** e clique em **Run workflow**

## 📄 Licença

MIT
