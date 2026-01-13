import time
import threading
import requests
import os
from flask import Flask

# --- SUAS CONFIGURAÇÕES ---
TELEGRAM_TOKEN = "8326718609:AAGaruZ6c0jg8UDFJBjnR4C8F5K0pdzuUds"
CHAT_ID = "-1003598153908"
# Aqui está a marcação correta:
PESSOA_PARA_MARCAR = "@harrysonsm42" 

app = Flask(__name__)

# Variáveis globais (Onde o tempo fica guardado)
ultimo_sinal = time.time()
alerta_enviado = False
ssid_atual = "Aguardando..."

def enviar_telegram(mensagem):
    """Envia a mensagem e retorna True se deu certo"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"} # Markdown permite links e negrito
    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            print("✅ Telegram enviado com sucesso!")
            return True
        else:
            print(f"❌ Erro Telegram: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return False

def monitor_loop():
    global alerta_enviado
    print("👀 Vigia iniciado na thread de monitoramento...")
    
    while True:
        now = time.time()
        diff = now - ultimo_sinal
        
        # LOG PARA VOCÊ ACOMPANHAR NO RENDER
        # print(f"DEBUG: Tempo sem sinal: {int(diff)}s | Alerta já foi enviado? {alerta_enviado}")

        # LÓGICA DOS 60 SEGUNDOS
        if diff > 60:
            if not alerta_enviado:
                print("🚨 60s passaram! Preparando alerta...")
                
                msg = (f"🚨 *ALERTA: INTERNET CAIU* 🚨\n\n"
                       f"{PESSOA_PARA_MARCAR}\n"  # Aqui ele te marca
                       f"⚠️ A loja está sem comunicação há {int(diff)} segundos.\n"
                       f"📡 Última rede: `{ssid_atual}`")
                
                # Tenta enviar. Se conseguir, marca que enviou.
                if enviar_telegram(msg):
                    alerta_enviado = True
        
        # LÓGICA DE QUANDO A INTERNET VOLTA
        else:
            # Se o tempo está baixo (<60) MAS o alerta estava marcado como enviado (True)
            if alerta_enviado:
                print("✅ Internet voltou! Avisando...")
                msg = (f"✅ *CONEXÃO RESTABELECIDA*\n\n"
                       f"{PESSOA_PARA_MARCAR}\n"
                       f"A internet da loja voltou a responder!")
                
                if enviar_telegram(msg):
                    alerta_enviado = False # Reseta o sistema para o próximo alerta
        
        time.sleep(5)

# Inicia o monitoramento
t = threading.Thread(target=monitor_loop)
t.start()

# --- ROTAS DO SITE ---

@app.route('/')
def home():
    tempo = int(time.time() - ultimo_sinal)
    status_msg = "ALERTA ENVIADO 🚨" if alerta_enviado else "Tudo Normal ✅"
    return (f"<h1>Vigia Ativo 👮</h1>"
            f"<p>Status: <b>{status_msg}</b></p>"
            f"<p>Último sinal da loja: há {tempo} segundos</p>"
            f"<p>Rede: {ssid_atual}</p>"
            f"<br><a href='/testar'>[TESTAR MARCAÇÃO]</a>"), 200

@app.route('/ping/<ssid>')
def ping(ssid):
    global ultimo_sinal, ssid_atual
    ultimo_sinal = time.time()
    ssid_atual = ssid
    # Se a internet voltou, o monitor_loop vai perceber na próxima checagem
    return "Recebido", 200

@app.route('/testar')
def testar():
    msg = f"🧪 Teste de marcação: {PESSOA_PARA_MARCAR} (Se ficou azul, funcionou!)"
    enviar_telegram(msg)
    return "Teste enviado.", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
