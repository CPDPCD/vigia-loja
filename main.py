import time
import threading
import requests
import os
from flask import Flask

# Configurações
TELEGRAM_TOKEN = os.getenv("8326718609:AAGaruZ6c0jg8UDFJBjnR4C8F5K0pdzuUds")
CHAT_ID = os.getenv("-1003598153908")
PESSOAS_PARA_MARCAR = "@harrysonsm42" 

app = Flask(__name__)

# Variáveis globais
ultimo_sinal = time.time()
alerta_enviado = False
ssid_atual = "Aguardando..."

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data, timeout=5)
    except Exception as e:
        print(f"Erro Telegram: {e}")

def monitor_loop():
    global alerta_enviado
    print("Vigia iniciado...")
    
    while True:
        now = time.time()
        diff = now - ultimo_sinal
        
        # Se passou de 35 segundos sem sinal
        if diff > 35:
            if not alerta_enviado:
                print("TEMPO ESLOTADO! Enviando alerta...")
                msg = (f"🚨 *ALERTA CRÍTICO: LOJA OFF-LINE* 🚨\n\n"
                       f"{PESSOAS_PARA_MARCAR}\n\n"
                       f"⏱️ Sem sinal há {int(diff)} segundos.\n"
                       f"📡 Última rede: `{ssid_atual}`\n"
                       f"⚠️ Verifiquem energia e modem!")
                enviar_telegram(msg)
                alerta_enviado = True
        else:
            # Se a internet voltar e o alerta estava ativo
            if alerta_enviado:
                enviar_telegram("✅ *A conexão da loja foi restabelecida!*")
                alerta_enviado = False
        
        time.sleep(5)

# Thread que roda em paralelo
t = threading.Thread(target=monitor_loop)
t.start()

# --- ROTAS DO SITE ---

@app.route('/')
def home():
    return f"Monitor Ativo. Último sinal há {int(time.time() - ultimo_sinal)}s", 200

# ROTA QUE O PC DA LOJA VAI ACESSAR
@app.route('/ping/<ssid>')
def ping(ssid):
    global ultimo_sinal, ssid_atual
    ultimo_sinal = time.time()
    ssid_atual = ssid
    return "Recebido", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
