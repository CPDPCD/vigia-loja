import time
import threading
import requests
import os
from flask import Flask

# --- CONFIGURAÇÕES ---
TELEGRAM_TOKEN = "8326718609:AAGaruZ6c0jg8UDFJBjnR4C8F5K0pdzuUds"
CHAT_ID = "-1003598153908"
PESSOA_PARA_MARCAR = "@harrysonsm42" 

app = Flask(__name__)

# --- CÉREBRO (MEMÓRIA) ---
dados_monitor = {
    "ultimo_sinal": time.time(),
    "ssid": "Aguardando conexão...",
    "alerta_enviado": False,
    "sistema_iniciado": False
}

def enviar_telegram(mensagem):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
        requests.post(url, data=data, timeout=5)
    except:
        pass

def vigia_background():
    print("👀 Vigia iniciado...")
    while True:
        now = time.time()
        diff = now - dados_monitor["ultimo_sinal"]
        
        if dados_monitor["sistema_iniciado"]:
            # CAIU (>60s)
            if diff > 60:
                if not dados_monitor["alerta_enviado"]:
                    print("🚨 QUEDA DETECTADA!")
                    msg = (f"🚨 *ALERTA: INTERNET CAIU* 🚨\n\n"
                           f"{PESSOA_PARA_MARCAR}\n"
                           f"⏱️ Sem sinal há {int(diff)} segundos.\n"
                           f"📡 Última rede: `{dados_monitor['ssid']}`")
                    enviar_telegram(msg)
                    dados_monitor["alerta_enviado"] = True
            
            # VOLTOU
            else:
                if dados_monitor["alerta_enviado"]:
                    print("✅ VOLTOU!")
                    msg = (f"✅ *CONEXÃO RESTABELECIDA*\n\n"
                           f"{PESSOA_PARA_MARCAR}\nInternet normalizada.")
                    enviar_telegram(msg)
                    dados_monitor["alerta_enviado"] = False
        
        time.sleep(5)

t = threading.Thread(target=vigia_background)
t.start()

# --- AQUI ESTÁ A MÁGICA VISUAL ---
@app.route('/')
def home():
    diff = int(time.time() - dados_monitor["ultimo_sinal"])
    
    # Define as cores e textos baseado no estado
    if not dados_monitor["sistema_iniciado"]:
        cor_fundo = "#f39c12" # Laranja
        status_texto = "AGUARDANDO 1º SINAL..."
        subtexto = "Ligue o script na loja"
    elif diff > 60:
        cor_fundo = "#c0392b" # Vermelho
        status_texto = "🚨 INTERNET CAIU 🚨"
        subtexto = f"Sem sinal há {diff} segundos"
    else:
        cor_fundo = "#27ae60" # Verde
        status_texto = "ONLINE ✅"
        subtexto = f"Último sinal há {diff} segundos"

    # HTML BONITO COM REFRESH AUTOMÁTICO
    html = f"""
    <html>
    <head>
        <title>Monitor Loja</title>
        <meta http-equiv="refresh" content="5"> <style>
            body {{ font-family: sans-serif; text-align: center; background-color: {cor_fundo}; color: white; padding-top: 50px; transition: background-color 0.5s; }}
            h1 {{ font-size: 60px; margin: 0; }}
            p {{ font-size: 24px; }}
            .box {{ background: rgba(0,0,0,0.2); display: inline-block; padding: 20px; border-radius: 10px; }}
        </style>
    </head>
    <body>
        <div class="box">
            <h1>{status_texto}</h1>
            <p>{subtexto}</p>
            <p>Rede: <b>{dados_monitor['ssid']}</b></p>
            <p><small>Status do Alerta Telegram: {dados_monitor['alerta_enviado']}</small></p>
        </div>
    </body>
    </html>
    """
    return html

@app.route('/ping/<ssid>')
def ping(ssid):
    dados_monitor["ultimo_sinal"] = time.time()
    dados_monitor["ssid"] = ssid
    dados_monitor["sistema_iniciado"] = True
    return "Recebido", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
