import sys
import os
import base64
import requests
import time

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

from shared.config import settings

def get_qr_code():
    instance_name = "tiktrend-whatsapp"
    print(f"🔄 Buscando QR Code para instância '{instance_name}'...")
    
    url = f"{settings.EVOLUTION_API_URL}/instance/connect/{instance_name}"
    headers = {"apikey": settings.EVOLUTION_API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            base64_code = data.get('base64')
            if base64_code:
                # Remove header if present
                if "base64," in base64_code:
                    base64_code = base64_code.split("base64,")[1]
                
                # Save to file
                with open("whatsapp_qr.png", "wb") as f:
                    f.write(base64.b64decode(base64_code))
                print("✅ QR Code salvo como 'whatsapp_qr.png'. Abra este arquivo para escanear.")
                
                # Also print code for terminal if supported (optional, usually too big)
                print("ℹ️  Escaneie o QR Code gerado com seu WhatsApp.")
            else:
                print("⚠️  Não foi possível obter o base64 do QR Code. A instância pode já estar conectada ou erro na resposta.")
                print(f"Resposta: {data}")
        else:
            print(f"❌ Erro ao buscar QR Code: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Erro de conexão: {str(e)}")

if __name__ == "__main__":
    get_qr_code()
