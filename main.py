import time
import threading
import requests
import os
from flask import Flask

# --- CONFIGURAÇÕES DO VIGIA ---
TELEGRAM_TOKEN = "8326718609:AAGaruZ6c0jg8UDFJBjnR4C8F5K0pdzuUds"
CHAT_ID = "-1003598153908"
PESSOAS_PARA_MARCAR = "@harrysonsm42" # Mude isso se quiser marcar alguém específico

app = Flask(__name__)

# Variáveis globais
ultimo_sinal = time.time()
alerta_enviado = False
ssid_atual = "Aguardando..."

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            print("✅ Mensagem enviada para o Telegram com sucesso!")
            return True
        else:
            print(f"❌ Erro ao enviar Telegram: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro de conexão Telegram: {e}")
        return False

def monitor_loop():
    global alerta_enviado
    print("👀 Vigia iniciado e monitorando...")
    
    while True:
        now = time.time()
        diff = now - ultimo_sinal
        
        # LOG DE DEBUG NO RENDER (Para você ver se está contando)
        # print(f"DEBUG: Tempo sem sinal: {int(diff)}s") 
        
        if diff > 45: # Tolerância de 45 segundos
            if not alerta_enviado:
                print("🚨 TEMPO ESGOTADO! DISPARANDO ALERTA...")
                msg = (f"🚨 *ALERTA CRÍTICO: LOJA OFF-LINE* 🚨\n\n"
                       f"{PESSOAS_PARA_MARCAR}\n\n"
                       f"⏱️ Sem sinal há {int(diff)} segundos.\n"
                       f"📡 Última rede: `{ssid_atual}`\n"
                       f"⚠️ Verifiquem energia e modem!")
                enviar_telegram(msg)
                alerta_enviado = True
        else:
            if alerta_enviado:
                print("✅ Conexão voltou!")
                enviar_telegram("✅ *A conexão da loja foi restabelecida!*")
                alerta_enviado = False
        
        time.sleep(5)

# Inicia o monitoramento
t = threading.Thread(target=monitor_loop)
t.start()

# --- ROTAS ---

@app.route('/')
def home():
    tempo = int(time.time() - ultimo_sinal)
    return f"<h1>Vigia Ativo 👮</h1><p>Último sinal da loja: há {tempo} segundos</p><p>SSID: {ssid_atual}</p><br><a href='/testar'>[CLIQUE AQUI PARA TESTAR O ALERTA AGORA]</a>", 200

@app.route('/ping/<ssid>')
def ping(ssid):
    global ultimo_sinal, ssid_atual
    ultimo_sinal = time.time()
    ssid_atual = ssid
    return "Recebido", 200

# ROTA DE TESTE MANUAL
@app.route('/testar')
def testar():
    msg = "🧪 *TESTE DE ALERTA DO SISTEMA VIGIA* \nSe você recebeu isso, as senhas estão certas!"
    sucesso = enviar_telegram(msg)
    if sucesso:
        return "Mensagem de teste enviada! Confira seu Telegram.", 200
    else:
        return "FALHA ao enviar. Verifique os Logs do Render.", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
