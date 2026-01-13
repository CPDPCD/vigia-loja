import time
import threading
import requests
import os
from flask import Flask

# --- CONFIGURAÇÕES ---
TOKEN_BOT_VIGIA = "8558127430:AAGDw91s59P2KRCGG59QM4SX0ABJBmEBYvY" # Bot que avisa
CHAT_ID_ALERTA = "6114781935" # Ou ID do grupo para o alerta
PESSOA_PARA_MARCAR = "@harrysonsm42" 

app = Flask(__name__)

# Memória do Sistema
dados = {
    "ultimo_sinal": time.time(),
    "ssid": "Aguardando conexão...",
    "alerta_ativo": False,
    "sistema_iniciado": False
}

def enviar_alerta_telegram(mensagem):
    try:
        url = f"https://api.telegram.org/bot{TOKEN_BOT_VIGIA}/sendMessage"
        data = {"chat_id": CHAT_ID_ALERTA, "text": mensagem, "parse_mode": "Markdown"}
        requests.post(url, data=data, timeout=5)
    except Exception as e:
        print(f"Erro envio: {e}")

def loop_vigia():
    print("👀 Vigia Híbrido Iniciado...")
    while True:
        now = time.time()
        diff = now - dados["ultimo_sinal"]
        
        # Só vigia se o sistema já tiver recebido o primeiro sinal
        if dados["sistema_iniciado"]:
            
            # --- QUEDA (>60s) ---
            if diff > 60:
                if not dados["alerta_ativo"]:
                    print("🚨 QUEDA DETECTADA!")
                    msg = (f"🚨 *ALERTA: INTERNET CAIU* 🚨\n\n"
                           f"{PESSOA_PARA_MARCAR}\n"
                           f"⏱️ Sem sinal do PC da loja há {int(diff)} segundos.\n"
                           f"📡 Última rede: `{dados['ssid']}`")
                    enviar_alerta_telegram(msg)
                    dados["alerta_ativo"] = True
            
            # --- VOLTA ---
            else:
                if dados["alerta_ativo"]:
                    print("✅ VOLTOU!")
                    msg = (f"✅ *CONEXÃO RESTABELECIDA*\n\n"
                           f"{PESSOA_PARA_MARCAR}\nInternet normalizada.")
                    enviar_alerta_telegram(msg)
                    dados["alerta_ativo"] = False
        
        time.sleep(5)

t = threading.Thread(target=loop_vigia)
t.start()

# --- ROTAS ---
@app.route('/')
def home():
    diff = int(time.time() - dados["ultimo_sinal"])
    status = "ONLINE" if diff < 60 else "OFFLINE"
    cor = "green" if status == "ONLINE" else "red"
    
    return (f"<h1>Monitor Loja</h1>"
            f"<h2 style='color:{cor}'>Status: {status} ({diff}s)</h2>"
            f"<p>SSID: {dados['ssid']}</p>"
            f"<p>Alerta Ativo: {dados['alerta_ativo']}</p>")

# ROTA QUE RECEBE O SINAL DA LOJA
@app.route('/ping/<ssid>')
def ping(ssid):
    dados["ultimo_sinal"] = time.time()
    dados["ssid"] = ssid
    dados["sistema_iniciado"] = True
    return "Recebido", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
