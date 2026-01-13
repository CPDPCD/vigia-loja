import time
import threading
import requests
import os
from flask import Flask

# --- SUAS CONFIGURAÇÕES ---
TOKEN_BOT_VIGIA = "8558127430:AAGDw91s59P2KRCGG59QM4SX0ABJBmEBYvY" # Bot 2 (Vigia)
CHAT_ID_ALERTA = "-1003598153908" # Grupo ou seu ID Pessoal
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
        response = requests.post(url, data=data, timeout=5)
        # Debug para log do Render
        if response.status_code != 200:
            print(f"Erro Telegram: {response.text}")
    except Exception as e:
        print(f"Erro envio: {e}")

# --- NOVA FUNÇÃO: AVISO DE INÍCIO ---
def notificar_inicio():
    print("📢 Enviando aviso de inicialização...")
    msg = (f"🤖 *VIGIA DO RENDER INICIADO*\n"
           f"O sistema está online e aguardando o sinal da loja.\n"
           f"Versão: Híbrida (Monitoramento via Ping)")
    enviar_alerta_telegram(msg)

def loop_vigia():
    print("👀 Vigia Híbrido Iniciado...")
    
    # Chama o aviso assim que o vigia começa a rodar
    notificar_inicio()
    
    while True:
        now = time.time()
        diff = now - dados["ultimo_sinal"]
        
        # Só vigia se o sistema já tiver recebido o primeiro sinal da loja
        if dados["sistema_iniciado"]:
            
            # --- Cenario: QUEDA (>60s) ---
            if diff > 60:
                if not dados["alerta_ativo"]:
                    print("🚨 QUEDA DETECTADA!")
                    msg = (f"🚨 *ALERTA: INTERNET CAIU* 🚨\n\n"
                           f"{PESSOA_PARA_MARCAR}\n"
                           f"⏱️ Sem sinal do PC da loja há {int(diff)} segundos.\n"
                           f"📡 Última rede: `{dados['ssid']}`")
                    enviar_alerta_telegram(msg)
                    dados["alerta_ativo"] = True
            
            # --- Cenario: VOLTA ---
            else:
                if dados["alerta_ativo"]:
                    print("✅ VOLTOU!")
                    msg = (f"✅ *CONEXÃO RESTABELECIDA*\n\n"
                           f"{PESSOA_PARA_MARCAR}\nInternet normalizada.")
                    enviar_alerta_telegram(msg)
                    dados["alerta_ativo"] = False
        
        time.sleep(5)

# Inicia a thread do vigia
t = threading.Thread(target=loop_vigia)
t.start()

# --- ROTAS ---
@app.route('/')
def home():
    diff = int(time.time() - dados["ultimo_sinal"])
    status = "ONLINE" if diff < 60 else "OFFLINE"
    cor = "green" if status == "ONLINE" else "red"
    msg_inicio = "Aguardando 1º contato da loja..." if not dados["sistema_iniciado"] else f"{diff}s sem sinal"
    
    return (f"<h1>Monitor Loja</h1>"
            f"<h2 style='color:{cor}'>Status: {status}</h2>"
            f"<p>Detalhe: {msg_inicio}</p>"
            f"<p>SSID: {dados['ssid']}</p>"
            f"<br><a href='/testar'>Testar Telegram Manualmente</a>"), 200

# ROTA QUE RECEBE O SINAL DA LOJA
@app.route('/ping/<ssid>')
def ping(ssid):
    dados["ultimo_sinal"] = time.time()
    dados["ssid"] = ssid
    dados["sistema_iniciado"] = True
    return "Recebido", 200

@app.route('/testar')
def testar():
    enviar_alerta_telegram(f"Teste manual solicitado por {PESSOA_PARA_MARCAR}")
    return "Enviado", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
