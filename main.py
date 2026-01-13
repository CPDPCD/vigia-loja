import time
import threading
import requests
import os
from flask import Flask

# --- CONFIGURAÇÕES ---
TOKEN_BOT_VIGIA = "8558127430:AAGDw91s59P2KRCGG59QM4SX0ABJBmEBYvY"
# Coloque o ID numérico aqui (sem aspas):
ID_BOT_LOJA = 8326718609 
# Coloque o ID do grupo aqui (entre aspas):
CHAT_ID_GRUPO_MONITORADO = "-1003598153908" 
ID_DESTINO_ALERTA = "6114781935"

app = Flask(__name__)

estado = {
    "ultimo_sinal": 0,
    "alerta_ativo": False,
    "debug_info": "Iniciando..."
}

def enviar_alerta(mensagem):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN_BOT_VIGIA}/sendMessage", 
                      data={"chat_id": ID_DESTINO_ALERTA, "text": mensagem})
    except:
        pass

def buscar_ultimo_sinal():
    url = f"https://api.telegram.org/bot{TOKEN_BOT_VIGIA}/getUpdates"
    try:
        response = requests.get(url, timeout=10).json()
        mensagens = response.get('result', [])
        
        # --- DEBUG NOS LOGS DO RENDER ---
        print(f"DEBUG: Encontrei {len(mensagens)} novas atualizações.")
        
        if not mensagens:
            return 0

        # Varre de trás para frente
        for item in reversed(mensagens):
            msg = item.get('message', {})
            chat_id = str(msg.get('chat', {}).get('id'))
            user_id = msg.get('from', {}).get('id')
            texto = msg.get('text', '')
            
            # Printa a última msg que ele viu para sabermos se ele está cego
            print(f"DEBUG: Li msg de ID {user_id} no Grupo {chat_id}: '{texto}'")
            
            # Verifica GRUPO
            if chat_id == str(CHAT_ID_GRUPO_MONITORADO):
                # Verifica USUÁRIO (BOT LOJA)
                if str(user_id) == str(ID_BOT_LOJA):
                    print("--> ACHEI UMA MENSAGEM DO BOT DA LOJA! <--")
                    return msg.get('date')
        
        print("DEBUG: Nenhuma mensagem do Bot da Loja encontrada nesta leva.")
        return 0
    except Exception as e:
        print(f"ERRO CRÍTICO: {e}")
        return 0

def vigia_loop():
    print("🕵️ Vigia Debug iniciado...")
    while True:
        timestamp_msg = buscar_ultimo_sinal()
        agora = time.time()
        
        if timestamp_msg > 0:
            diff = agora - timestamp_msg
            estado["ultimo_sinal"] = diff
            estado["debug_info"] = f"Lendo corretamente. Última há {int(diff)}s"
            
            if diff > 45:
                if not estado["alerta_ativo"]:
                    print("🚨 SILÊNCIO!")
                    enviar_alerta(f"🚨 *ALERTA: LOJA MUDO*\nSem sinal há {int(diff)}s!")
                    estado["alerta_ativo"] = True
            else:
                if estado["alerta_ativo"]:
                    enviar_alerta("✅ Voltou.")
                    estado["alerta_ativo"] = False
        else:
            estado["debug_info"] = "Não estou encontrando mensagens do Bot Loja."
        
        time.sleep(10)

t = threading.Thread(target=vigia_loop)
t.start()

@app.route('/')
def home():
    cor = "red" if estado["ultimo_sinal"] == 0 or estado["ultimo_sinal"] > 45 else "green"
    return (f"<h1>Painel Debug</h1>"
            f"<h2 style='color:{cor}'>Tempo: {int(estado['ultimo_sinal'])}s</h2>"
            f"<p>Status Técnico: <b>{estado['debug_info']}</b></p>"
            f"<p><small>Verifique a aba LOGS no Render para ver o que está acontecendo.</small></p>"), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
