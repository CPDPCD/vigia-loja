import time
import threading
import requests
import os
from flask import Flask

# --- CONFIGURAÇÕES ---
TOKEN_BOT_VIGIA = "8558127430:AAGDw91s59P2KRCGG59QM4SX0ABJBmEBYvY"
CHAT_ID_GRUPO_MONITORADO = "-1003598153908" # O Grupo onde o Bot 1 fala
ID_BOT_LOJA = 8326718609 # <--- COLOQUE O ID NUMÉRICO DO BOT 1 AQUI
ID_DESTINO_ALERTA = "-1003598153908" 

app = Flask(__name__)

# Controle de Estado
estado = {
    "ultimo_sinal": 0,
    "alerta_ativo": False
}

def enviar_alerta(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN_BOT_VIGIA}/sendMessage"
    data = {"chat_id": ID_DESTINO_ALERTA, "text": mensagem}
    try:
        requests.post(url, data=data)
    except:
        pass

def buscar_ultimo_sinal():
    """Lê o histórico do chat procurando o Bot da Loja"""
    url = f"https://api.telegram.org/bot{TOKEN_BOT_VIGIA}/getUpdates"
    try:
        # Pega as ultimas atualizações
        response = requests.get(url, timeout=10).json()
        mensagens = response.get('result', [])
        
        # Varre de trás para frente (mais recente primeiro)
        for item in reversed(mensagens):
            msg = item.get('message', {})
            
            # Verifica se é no grupo certo
            chat_id = str(msg.get('chat', {}).get('id'))
            if chat_id == str(CHAT_ID_GRUPO_MONITORADO):
                
                # Verifica se quem mandou foi o BOT DA LOJA
                user_id = msg.get('from', {}).get('id')
                if user_id == int(ID_BOT_LOJA):
                    return msg.get('date') # Retorna a hora da mensagem
        return 0
    except Exception as e:
        print(f"Erro Telegram: {e}")
        return 0

def vigia_loop():
    print("🕵️ Bot Vigia iniciado em background...")
    while True:
        # Tenta achar a ultima vez que o Bot 1 falou
        timestamp_msg = buscar_ultimo_sinal()
        agora = time.time()
        
        # Se achou alguma mensagem recente
        if timestamp_msg > 0:
            diff = agora - timestamp_msg
            estado["ultimo_sinal"] = diff
            
            # --- LÓGICA DE QUEDA (40s) ---
            # Damos 40s de margem porque o getUpdates as vezes tem delay
            if diff > 40:
                if not estado["alerta_ativo"]:
                    print("🚨 SILÊNCIO DETECTADO!")
                    enviar_alerta(f"🚨 *ALERTA: LOJA MUDO*\n\nO Bot da loja parou de falar há {int(diff)} segundos!")
                    estado["alerta_ativo"] = True
            else:
                if estado["alerta_ativo"]:
                    enviar_alerta("✅ O Bot da loja voltou a falar.")
                    estado["alerta_ativo"] = False
        
        time.sleep(10) # Verifica a cada 10 segundos

# Inicia o Loop do Vigia
t = threading.Thread(target=vigia_loop)
t.start()

# --- SITE FALSO PARA O RENDER NÃO DORMIR ---
@app.route('/')
def home():
    cor = "red" if estado["alerta_ativo"] else "green"
    msg = "CRÍTICO" if estado["alerta_ativo"] else "NORMAL"
    return (f"<h1>Painel do Bot Vigia</h1>"
            f"<h2 style='color:{cor}'>Status: {msg}</h2>"
            f"<p>Tempo desde a última msg do Bot Loja: {int(estado['ultimo_sinal'])}s</p>")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
