import discord
from discord.ext import commands, tasks
import asyncio
import os

TOKEN = os.getenv("TOKEN")  # Il token lo metti nelle Secrets, non qui!
VOICE_CHANNEL_ID = 1575378302913216552
LOG_CHANNEL_ID = 1570934757657804914
STAFF_ROLE_ID = 1574914867939516517

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="/", intents=intents)

async def entra_nel_vocale():
    channel = bot.get_channel(VOICE_CHANNEL_ID)
    if channel is None:
        return
    vc = discord.utils.get(bot.voice_clients, guild=channel.guild)
    if vc is None or not vc.is_connected():
        try:
            await channel.connect(reconnect=True, timeout=60)
            print(f"Entrato in {channel.name}")
        except Exception as e:
            print(f"Errore entrata: {e}")
    elif vc.channel.id != VOICE_CHANNEL_ID:
        await vc.move_to(channel)

@bot.event
async def on_ready():
    print(f"Online: {bot.user}")
    await bot.tree.sync()
    await entra_nel_vocale()
    controlla_vocale.start()

@tasks.loop(seconds=10)
async def controlla_vocale():
    await entra_nel_vocale()

@bot.event
async def on_voice_state_update(member, before, after):
    if member.id == bot.user.id:
        if after.channel is None:
            print("Mi hanno buttato fuori, rientro...")
            await asyncio.sleep(2)
            await entra_nel_vocale()
        return

    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel is None:
        return

    # ENTRATO
    if before.channel is None and after.channel is not None and after.channel.id == VOICE_CHANNEL_ID:
        await log_channel.send(
            f"<@&{STAFF_ROLE_ID}> 🔔 **{member.mention} è entrato!**\n"
            f"La persona è in attesa **Assistenza** e vi aspetta!"
        )
        return

    # BUTTATO FUORI
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

bot.run(TOKEN)
