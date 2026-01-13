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

# --- MEMÓRIA DO SISTEMA (CLASSE SEGURA) ---
class SistemaVigia:
    def __init__(self):
        self.ultimo_sinal = time.time()
        self.ssid = "Aguardando 1º Sinal..."
        self.alerta_enviado = False
        self.lock = threading.Lock() # Evita conflito de dados

    def atualizar(self, novo_ssid):
        with self.lock:
            self.ultimo_sinal = time.time()
            self.ssid = novo_ssid
            # Se recebeu sinal, reseta o status de alerta
            # (O monitor vai tratar o envio de 'Voltou' se precisar)
    
    def ler_status(self):
        with self.lock:
            diff = time.time() - self.ultimo_sinal
            return diff, self.ssid, self.alerta_enviado

    def marcar_alerta_como_enviado(self, estado):
        with self.lock:
            self.alerta_enviado = estado

# Cria o vigia na memória
vigia = SistemaVigia()

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data, timeout=5)
        return True
    except Exception as e:
        print(f"Erro Telegram: {e}")
        return False

def loop_monitoramento():
    print("👀 Monitor Iniciado...")
    while True:
        diff, ssid, alerta_ja_foi = vigia.ler_status()
        
        # LOG PARA VOCÊ ACOMPANHAR NO RENDER
        if int(diff) % 5 == 0:
            print(f"STATUS: {int(diff)}s sem sinal | SSID: {ssid}")

        # --- LÓGICA DE QUEDA (60s) ---
        if diff > 60:
            if not alerta_ja_foi:
                if ssid == "Aguardando 1º Sinal...":
                    pass # Não alerta se nunca funcionou
                else:
                    print("🚨 DISPARANDO ALERTA...")
                    msg = (f"🚨 *ALERTA: INTERNET CAIU* 🚨\n\n"
                           f"{PESSOA_PARA_MARCAR}\n"
                           f"⏱️ Sem sinal há {int(diff)} segundos.\n"
                           f"📡 Rede: `{ssid}`")
                    if enviar_telegram(msg):
                        vigia.marcar_alerta_como_enviado(True)
        
        # --- LÓGICA DE RETORNO ---
        else:
            if alerta_ja_foi:
                print("✅ SINAL VOLTOU!")
                msg = (f"✅ *CONEXÃO RESTABELECIDA*\n\n"
                       f"{PESSOA_PARA_MARCAR}\nInternet normalizada.")
                enviar_telegram(msg)
                vigia.marcar_alerta_como_enviado(False)
        
        time.sleep(5)

# Inicia thread
t = threading.Thread(target=loop_monitoramento)
t.start()

# --- ROTAS ---
@app.route('/')
def home():
    diff, ssid, alerta = vigia.ler_status()
    cor = "green" if diff < 60 else "red"
    return (f"<h1>Monitor de Rede</h1>"
            f"<h2 style='color:{cor}'>Tempo sem sinal: {int(diff)} segundos</h2>"
            f"<p>SSID Atual: <b>{ssid}</b></p>"
            f"<p>Alerta Enviado? {alerta}</p>"
            f"<br><a href='/testar'>Testar Telegram</a>"), 200

@app.route('/ping/<ssid>')
def ping(ssid):
    vigia.atualizar(ssid)
    return "Recebido", 200

@app.route('/testar')
def testar():
    enviar_telegram(f"Teste solicitado por {PESSOA_PARA_MARCAR}")
    return "Enviado", 200
