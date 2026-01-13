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

# Arquivo onde guardaremos o tempo (Funciona melhor que variável global)
ARQUIVO_TEMPO = "/tmp/last_seen.txt"
ARQUIVO_SSID = "/tmp/last_ssid.txt"

def salvar_dados(ssid):
    """Escreve o horário atual e o SSID em arquivos"""
    with open(ARQUIVO_TEMPO, "w") as f:
        f.write(str(time.time()))
    with open(ARQUIVO_SSID, "w") as f:
        f.write(ssid)

def ler_dados():
    """Lê o horário salvo. Se não existir, retorna agora."""
    try:
        if os.path.exists(ARQUIVO_TEMPO):
            with open(ARQUIVO_TEMPO, "r") as f:
                return float(f.read())
        return time.time()
    except:
        return time.time()

def ler_ssid():
    try:
        if os.path.exists(ARQUIVO_SSID):
            with open(ARQUIVO_SSID, "r") as f:
                return f.read()
        return "Desconhecido"
    except:
        return "Erro Leitura"

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    try:
        print(f"Tentando enviar msg para: {PESSOA_PARA_MARCAR}")
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            print("✅ Telegram enviado!")
            return True
        else:
            print(f"❌ Erro Telegram: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro Conexão: {e}")
        return False

# Variável de controle para não spamar alerta
alerta_ja_enviado = False

def monitor_loop():
    global alerta_ja_enviado
    print("👀 Vigia iniciado (Modo Arquivo)...")
    
    while True:
        # Pega o último horário salvo no arquivo
        ultimo_sinal = ler_dados()
        now = time.time()
        diff = now - ultimo_sinal
        
        # Log para debug nos logs do Render
        if int(diff) % 10 == 0: # Imprime a cada 10s pra não poluir
            print(f"DEBUG: Tempo sem sinal: {int(diff)}s")

        # --- LÓGICA DE ALERTA (60 SEGUNDOS) ---
        if diff > 60:
            if not alerta_ja_enviado:
                print("🚨 TEMPO ESTOUROU! Enviando alerta...")
                ssid = ler_ssid()
                msg = (f"🚨 *ALERTA: INTERNET CAIU* 🚨\n\n"
                       f"{PESSOA_PARA_MARCAR}\n"
                       f"⚠️ Sem sinal há {int(diff)} segundos.\n"
                       f"📡 Última rede: `{ssid}`")
                
                if enviar_telegram(msg):
                    alerta_ja_enviado = True
        
        # --- LÓGICA DE VOLTA ---
        else:
            if alerta_ja_enviado:
                print("✅ Sinal voltou! Resetando...")
                msg = (f"✅ *CONEXÃO RESTABELECIDA*\n\n"
                       f"{PESSOA_PARA_MARCAR}\n"
                       f"A internet voltou! Tudo normal.")
                enviar_telegram(msg)
                alerta_ja_enviado = False
        
        time.sleep(5)

# Inicia thread
t = threading.Thread(target=monitor_loop)
t.start()

# --- ROTAS ---
@app.route('/')
def home():
    diff = int(time.time() - ler_dados())
    cor = "green" if diff < 60 else "red"
    return (f"<h1>Monitor de Rede</h1>"
            f"<h2 style='color:{cor}'>Tempo sem sinal: {diff} segundos</h2>"
            f"<p>Alerta enviado: {alerta_ja_enviado}</p>"
            f"<p>SSID: {ler_ssid()}</p>"
            f"<br><a href='/testar'>Testar Envio Telegram</a>"), 200

@app.route('/ping/<ssid>')
def ping(ssid):
    salvar_dados(ssid)
    return "Recebido", 200

@app.route('/testar')
def testar():
    enviar_telegram(f"Teste manual solicitada por {PESSOA_PARA_MARCAR}")
    return "Enviado. Verifique o Telegram.", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
