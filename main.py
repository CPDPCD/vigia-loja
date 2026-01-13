import time
import threading
import requests
import os
from flask import Flask

# --- CONFIGURAÇÕES ---
TOKEN_BOT_VIGIA = "8558127430:AAGDw91s59P2KRCGG59QM4SX0ABJBmEBYvY"
CHAT_ID_ALERTA = "-1003598153908"
PESSOA_PARA_MARCAR = "@harrysonsm42"
NOME_DA_LOJA = "GM Fast" # Nome que vai aparecer na mensagem

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
        print(f"Erro envio Telegram: {e}")

def notificar_inicio():
    print("📢 Sistema Iniciado.")
    msg = (f"🤖 *VIGIA ATIVO*\n"
           f"Monitorando o status da {NOME_DA_LOJA}.\n"
           f"Aguardando primeiro sinal...")
    enviar_alerta_telegram(msg)

def loop_vigia():
    print("👀 Vigia rodando...")
    notificar_inicio()
    
    while True:
        now = time.time()
        diff = now - dados["ultimo_sinal"]
        
        # 1. DEFINE O STATUS (A Lógica que você pediu)
        # Se o tempo for menor que 60s, é ONLINE. Se passar, é OFFLINE.
        if diff < 60:
            status_atual = "ONLINE"
        else:
            status_atual = "OFFLINE"

        # 2. DECISÃO BASEADA NO STATUS
        # Só começa a monitorar se a loja já deu o primeiro sinal de vida
        if dados["sistema_iniciado"]:
            
            # SE O STATUS FOR OFFLINE
            if status_atual == "OFFLINE":
                # Se o alerta ainda não foi enviado, ENVIA AGORA OBRIGATORIAMENTE
                if not dados["alerta_ativo"]:
                    print("🚨 STATUS VIROU OFFLINE! ENVIANDO ALERTA...")
                    
                    msg = (f"🚨 *ALERTA: INTERNET CAIU* 🚨\n\n"
                           f"{PESSOA_PARA_MARCAR}\n"
                           f"A internet na *{NOME_DA_LOJA}* caiu!\n"
                           f"⚠️ Status: *OFFLINE*\n"
                           f"⏱️ Tempo sem sinal: {int(diff)} segundos\n"
                           f"📡 Última rede: `{dados['ssid']}`")
                    
                    enviar_alerta_telegram(msg)
                    dados["alerta_ativo"] = True
            
            # SE O STATUS FOR ONLINE (Voltou)
            elif status_atual == "ONLINE":
                # Se estava em alerta antes, avisa que voltou
                if dados["alerta_ativo"]:
                    print("✅ STATUS VIROU ONLINE!")
                    msg = (f"✅ *CONEXÃO RESTABELECIDA*\n\n"
                           f"{PESSOA_PARA_MARCAR}\n"
                           f"A internet da {NOME_DA_LOJA} voltou.\n"
                           f"Status agora: *ONLINE*")
                    enviar_alerta_telegram(msg)
                    dados["alerta_ativo"] = False
        
        time.sleep(5)

t = threading.Thread(target=loop_vigia)
t.start()

# --- SITE (MOSTRA O MESMO STATUS DO ROBÔ) ---
@app.route('/')
def home():
    diff = int(time.time() - dados["ultimo_sinal"])
    
    # Lógica visual idêntica à do robô
    if diff < 60:
        status_visual = "ONLINE"
        cor = "green"
    else:
        status_visual = "OFFLINE"
        cor = "red"

    msg_detalhe = f"{diff}s sem sinal" if dados["sistema_iniciado"] else "Aguardando script da loja..."

    return (f"<h1>Monitor {NOME_DA_LOJA}</h1>"
            f"<h2 style='color:{cor}'>Status: {status_visual}</h2>"
            f"<p>Detalhe: {msg_detalhe}</p>"
            f"<p>SSID: {dados['ssid']}</p>"
            f"<br><a href='/testar'>Testar Telegram Manualmente</a>"), 200

@app.route('/ping/<ssid>')
def ping(ssid):
    dados["ultimo_sinal"] = time.time()
    dados["ssid"] = ssid
    dados["sistema_iniciado"] = True
    return "Recebido", 200

@app.route('/testar')
def testar():
    enviar_alerta_telegram(f"Teste solicitado por {PESSOA_PARA_MARCAR}")
    return "Enviado", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
