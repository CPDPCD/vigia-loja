import time
import threading
import requests
import os
from flask import Flask

# --- SUAS CONFIGURAÇÕES ---
TELEGRAM_TOKEN = "8326718609:AAGaruZ6c0jg8UDFJBjnR4C8F5K0pdzuUds"
CHAT_ID = "-1003598153908"
PESSOA_PARA_MARCAR = "@harrysonsm42" 

app = Flask(__name__)

# --- CÉREBRO DO SISTEMA ---
# Armazena o estado na memória RAM
dados_monitor = {
    "ultimo_sinal": time.time(),
    "ssid": "Aguardando conexão...",
    "alerta_enviado": False,
    "sistema_iniciado": False # Só alerta DEPOIS do primeiro contato
}

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data, timeout=5)
    except Exception as e:
        print(f"Erro ao enviar Telegram: {e}")

def vigia_background():
    print("👀 Vigia iniciado...")
    while True:
        now = time.time()
        diff = now - dados_monitor["ultimo_sinal"]
        
        # Só começa a vigiar se a loja já deu oi pelo menos uma vez
        if dados_monitor["sistema_iniciado"]:
            
            # CENÁRIO 1: CAIU A INTERNET (> 60s)
            if diff > 60:
                if not dados_monitor["alerta_enviado"]:
                    print("🚨 TEMPO ESTOUROU! Enviando alerta...")
                    msg = (f"🚨 *ALERTA CRÍTICO: LOJA OFF-LINE* 🚨\n\n"
                           f"{PESSOA_PARA_MARCAR}\n"
                           f"⏱️ Sem sinal há {int(diff)} segundos.\n"
                           f"📡 Última rede: `{dados_monitor['ssid']}`")
                    enviar_telegram(msg)
                    dados_monitor["alerta_enviado"] = True
            
            # CENÁRIO 2: VOLTOU A INTERNET
            else:
                if dados_monitor["alerta_enviado"]:
                    print("✅ SINAL VOLTOU!")
                    msg = (f"✅ *CONEXÃO RESTABELECIDA*\n\n"
                           f"{PESSOA_PARA_MARCAR}\n"
                           f"A internet voltou! Monitorando...")
                    enviar_telegram(msg)
                    dados_monitor["alerta_enviado"] = False
        
        time.sleep(5)

# Inicia o vigia em segundo plano
t = threading.Thread(target=vigia_background)
t.start()

# --- ROTAS (LINKS) ---

@app.route('/')
def home():
    diff = int(time.time() - dados_monitor["ultimo_sinal"])
    status = "ESPERANDO 1º SINAL" if not dados_monitor["sistema_iniciado"] else f"{diff}s sem sinal"
    cor = "red" if diff > 60 and dados_monitor["sistema_iniciado"] else "green"
    
    return (f"<h1>Painel do Vigia</h1>"
            f"<h2 style='color:{cor}'>Status: {status}</h2>"
            f"<p>Rede: {dados_monitor['ssid']}</p>"
            f"<p>Alerta já enviado? {dados_monitor['alerta_enviado']}</p>"
            f"<br><a href='/testar'>Testar Telegram Agora</a>")

@app.route('/ping/<ssid>')
def ping(ssid):
    # O COMPUTADOR DA LOJA ACESSA ISSO AQUI
    dados_monitor["ultimo_sinal"] = time.time()
    dados_monitor["ssid"] = ssid
    dados_monitor["sistema_iniciado"] = True # Agora o vigia começa a valer
    return "Recebido", 200

@app.route('/testar')
def testar():
    enviar_telegram(f"Teste de envio para {PESSOA_PARA_MARCAR}")
    return "Teste enviado! Verifique o Telegram.", 200
