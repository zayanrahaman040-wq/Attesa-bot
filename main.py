import discord
import os
import asyncio
from discord.ext import commands

intents = discord.Intents.default()
intents.voice_states = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

GUILD_ID = 1561473688476327956
VOICE_CHANNEL_ID = 1575378302913216552  # attesa-assistenza
TEXT_CHANNEL_ID = 1570934757657804914  # dove avvisa
RUOLO_STAFF = 1574914867939516517

@bot.event
async def on_ready():
    print(f"Online: {bot.user}", flush=True)
    # Bot entra e resta in VC
    guild = bot.get_guild(GUILD_ID)
    if guild:
        channel = guild.get_channel(VOICE_CHANNEL_ID)
        if channel:
            try:
                # Se è già connesso, non riconnettere
                if guild.voice_client is None:
                    await channel.connect(timeout=15, reconnect=True)
                    print(f"Bot in VC: {channel.name}", flush=True)
            except Exception as e:
                print(f"Errore entrata VC: {e}", flush=True)

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    text_channel = bot.get_channel(TEXT_CHANNEL_ID)
    if text_channel is None:
        return

    # 1. UNO ENTRA in attesa-assistenza
    if before.channel is None and after.channel and after.channel.id == VOICE_CHANNEL_ID:
        await text_channel.send(
            f"<@&{RUOLO_STAFF}>\n**{member.display_name}** è entrata, dice: la persona è in attesa Assistenza e vi aspetta voi!"
        )
        print(f"Entrato: {member.display_name}", flush=True)

    # 2. UNO VIENE BUTTATO FUORI / ESCE da attesa-assistenza
    if before.channel and before.channel.id == VOICE_CHANNEL_ID and after.channel is None:
        # Controlla audit log per vedere chi l'ha buttato fuori
        chi_ha_buttato = "un admin"
        try:
            guild = bot.get_guild(GUILD_ID)
            async for entry in guild.audit_logs(limit=3, action=discord.AuditLogAction.member_disconnect):
                # Se l'entry è di ora e riguarda questa persona
                if entry.target and entry.target.id == member.id:
                    chi_ha_buttato = entry.user.display_name
                    break
            async for entry in guild.audit_logs(limit=3, action=discord.AuditLogAction.member_move):
                if entry.target and entry.target.id == member.id:
                    chi_ha_buttato = entry.user.display_name
                    break
        except Exception:
            pass

        await text_channel.send(
            f"<@&{RUOLO_STAFF}>\n⚠️ **{member.display_name} è stato buttato fuori dal VC da {chi_ha_buttato}!**"
        )
        print(f"Buttato fuori: {member.display_name} da {chi_ha_buttato}", flush=True)

bot.run(os.getenv("TOKEN"))
