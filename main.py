import discord
from discord.ext import commands
import os
import asyncio
import yt_dlp

TOKEN = os.getenv("TOKEN")

# ID TUOI
VOICE_CHANNEL_ID = 1575378302913216552
LOG_CHANNEL_ID = 1575421052402020493
STAFF_ROLE_ID = 1574914867939516517

# Musica di sottofondo - puoi cambiare link
MUSIC_URL = "https://www.youtube.com/watch?v=5qap5aO4i9A"  # lofi 24/7

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="/", intents=intents)

# Config yt-dlp
ydl_opts = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'noplaylist': True,
}

def get_audio_url(url):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info['url']

async def play_music(vc):
    while True:
        try:
            if not vc.is_connected():
                return
            loop = asyncio.get_event_loop()
            audio_url = await loop.run_in_executor(None, get_audio_url, MUSIC_URL)
            source = await discord.FFmpegOpusAudio.from_probe(audio_url, method='fallback')
            vc.play(source)
            print("Musica partita", flush=True)
            while vc.is_playing() or vc.is_paused():
                await asyncio.sleep(1)
            await asyncio.sleep(1)
        except Exception as e:
            print(f"Errore musica: {e}", flush=True)
            await asyncio.sleep(5)

@bot.event
async def on_ready():
    print(f"Online: {bot.user}", flush=True)
    try:
        await bot.tree.sync()
        print("Comandi sincronizzati", flush=True)
    except Exception as e:
        print(f"Errore sync: {e}", flush=True)

    channel = bot.get_channel(VOICE_CHANNEL_ID)
    if channel:
        try:
            vc = await channel.connect()
            print(f"Entrato in {channel.name}", flush=True)
            bot.loop.create_task(play_music(vc))
        except Exception as e:
            print(f"Errore VC: {e}", flush=True)

@bot.event
async def on_voice_state_update(member, before, after):
    # Ignora il bot stesso
    if member.bot:
        return

    # Qualcuno ENTRA nel canale assistenza
    if after.channel and after.channel.id == VOICE_CHANNEL_ID:
        if before.channel != after.channel:
            log_channel = bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                try:
                    await log_channel.send(
                        f"<@&{STAFF_ROLE_ID}> 🔔 **{member.mention} è entrato!**\n"
                        f"La persona è in attesa **Assistenza** e vi aspetta!"
                    )
                    print(f"Avvisato staff per {member.name}", flush=True)
                except Exception as e:
                    print(f"Errore invio log: {e}", flush=True)

    # Qualcuno ESCE
    if before.channel and before.channel.id == VOICE_CHANNEL_ID:
        if after.channel != before.channel:
            log_channel = bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                try:
                    await log_channel.send(
                        f"👋 **{member.mention} è uscito** dal canale Assistenza."
                    )
                except Exception as e:
                    print(f"Errore invio log uscita: {e}", flush=True)

@bot.tree.command(name="join", description="Fa entrare il bot in VC")
async def join_cmd(interaction: discord.Interaction):
    await interaction.response.send_message("Sono dentro!", ephemeral=True)
    channel = bot.get_channel(VOICE_CHANNEL_ID)
    if channel:
        if interaction.guild.voice_client:
            return
        vc = await channel.connect()
        bot.loop.create_task(play_music(vc))

@bot.tree.command(name="stop", description="Ferma la musica")
async def stop_cmd(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        interaction.guild.voice_client.stop()
        await interaction.response.send_message("Musica stoppata", ephemeral=True)

bot.run(TOKEN)
