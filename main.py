import discord
from discord.ext import commands, tasks
import asyncio
import os
import yt_dlp

TOKEN = os.getenv("TOKEN")
VOICE_CHANNEL_ID = 1575378302913216552
LOG_CHANNEL_ID = 1570934757657804914
STAFF_ROLE_ID = 1574914867939516517
CANZONE = "Interlinked Ambient"  # Cerca su YouTube

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="/", intents=intents)

# Config per prendere l'audio da YouTube
ydl_opts = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
}

async def entra_e_canta():
    channel = bot.get_channel(VOICE_CHANNEL_ID)
    if channel is None:
        return
    vc = discord.utils.get(bot.voice_clients, guild=channel.guild)
    if vc is None or not vc.is_connected():
        try:
            vc = await channel.connect(reconnect=True, timeout=60)
            print(f"Entrato in {channel.name}")
        except Exception as e:
            print(f"Errore entrata: {e}")
            return
    elif vc.channel.id != VOICE_CHANNEL_ID:
        await vc.move_to(channel)

    # Se non sta già cantando, parte la canzone
    if not vc.is_playing() and not vc.is_paused():
        await suona(vc)

async def suona(vc):
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(CANZONE, download=False)
            if 'entries' in info:
                info = info['entries'][0]
            url = info['url']
            print(f"Suono: {info.get('title')}")

        # FFmpeg - con reconnect per non farla fermare
        source = discord.FFmpegPCMAudio(
            url,
            before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            options="-vn"
        )
        # Quando finisce, riparte da sola in loop
        vc.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(suona(vc), bot.loop))
    except Exception as e:
        print(f"Errore musica: {e}")
        await asyncio.sleep(5)
        await suona(vc)

@bot.event
async def on_ready():
    print(f"Online: {bot.user}")
    await bot.tree.sync()
    await entra_e_canta()
    controlla_vocale.start()

@tasks.loop(seconds=10)
async def controlla_vocale():
    await entra_e_canta()

@bot.event
async def on_voice_state_update(member, before, after):
    if member.id == bot.user.id:
        if after.channel is None:
            print("Mi hanno buttato fuori, rientro...")
            await asyncio.sleep(2)
            await entra_e_canta()
        return

    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel is None:
        return

    if before.channel is None and after.channel is not None and after.channel.id == VOICE_CHANNEL_ID:
        await log_channel.send(
            f"<@&{STAFF_ROLE_ID}> 🔔 **{member.mention} è entrato!**\n"
            f"La persona è in attesa **Assistenza** e vi aspetta!"
        )
        return

    if before.channel is not None and before.channel.id == VOICE_CHANNEL_ID and after.channel is None:
        kicker = None
        try:
            async for entry in member.guild.audit_logs(limit=3, action=discord.AuditLogAction.member_disconnect):
                if entry.target and entry.target.id == member.id:
                    diff = (discord.utils.utcnow() - entry.created_at).total_seconds()
                    if diff < 10:
                        kicker = entry.user
                        break
        except Exception as e:
            print(f"Errore audit log: {e}")

        if kicker:
            await log_channel.send(
                f"⚠️ **WARN** <@&{STAFF_ROLE_ID}>\n"
                f"{kicker.mention} ha buttato fuori dal VC **{member.mention}** ({member.name})!"
            )
        else:
            await log_channel.send(f"👋 **{member.mention}** è uscito dal canale voce.")

@bot.tree.command(name="join", description="Entra in VC e canta Interlinked Ambient")
async def join(interaction: discord.Interaction):
    await interaction.response.send_message("Entro e canto 🎵", ephemeral=True)
    await entra_e_canta()

bot.run(TOKEN)
