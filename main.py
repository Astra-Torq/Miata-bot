import discord
import os
import json
import requests
from discord.ext import commands

# Load Miata's persona from the persona.txt file
try:
    with open("persona.txt", "r", encoding="utf-8") as f:
        persona_prompt = f.read()
    print("✅ Miata persona loaded successfully!")
except Exception as e:
    print("❌ Failed to load Miata persona:", e)

# Load secrets
TOKEN = os.getenv("DISCORD_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OWNER_ID = 763772604984328245
PASSWORD = "MSAP"

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

active_channels = {}
bot_enabled = True

if os.path.exists("active_channels.json"):
    with open("active_channels.json", "r") as f:
        active_channels = json.load(f)

def save_channels():
    with open("active_channels.json", "w") as f:
        json.dump(active_channels, f)

def is_owner(user_id):
    return user_id == OWNER_ID

async def request_password(interaction):
    await interaction.user.send("🛑 Access denied. Reply with the password to proceed.")

    def check(m):
        return m.author.id == interaction.user.id and isinstance(m.channel, discord.DMChannel)

    try:
        msg = await bot.wait_for("message", check=check, timeout=30)
        return msg.content.strip() == PASSWORD
    except:
        return False

@bot.event
async def on_ready():
    print(f"🚗 Miata is online as {bot.user}")
    await tree.sync()
    for guild in bot.guilds:
        member = guild.get_member(bot.user.id)
        if member:
            try:
                await member.edit(nick="Miata")
            except:
                print(f"Nickname set failed in {guild.name}")

@tree.command(name="activate", description="Activate Miata in this channel.")
async def activate(interaction: discord.Interaction):
    if not is_owner(interaction.user.id):
        if not await request_password(interaction):
            await interaction.response.send_message("❌ Wrong password!", ephemeral=True)
            return

    active_channels[str(interaction.guild.id)] = interaction.channel.id
    save_channels()
    await interaction.response.send_message("💖 Miata is VROOM VROOM in this channel!")

@tree.command(name="deactivate", description="Completely shut off Miata in this server.")
async def deactivate(interaction: discord.Interaction):
    if not is_owner(interaction.user.id):
        if not await request_password(interaction):
            await interaction.response.send_message("❌ Wrong password!", ephemeral=True)
            return

    active_channels.pop(str(interaction.guild.id), None)
    save_channels()
    await interaction.response.send_message("🔌 Miata is now offline for this server.")

@tree.command(name="botoff", description="Temporarily pause Miata's replies.")
async def botoff(interaction: discord.Interaction):
    global bot_enabled
    if not is_owner(interaction.user.id):
        if not await request_password(interaction):
            await interaction.response.send_message("❌ Wrong password!", ephemeral=True)
            return

    bot_enabled = False
    await interaction.response.send_message("🛑 Miata has been paused.")

@tree.command(name="boton", description="Resume Miata's responses.")
async def boton(interaction: discord.Interaction):
    global bot_enabled
    if not is_owner(interaction.user.id):
        if not await request_password(interaction):
            await interaction.response.send_message("❌ Wrong password!", ephemeral=True)
            return

    bot_enabled = True
    await interaction.response.send_message("✅ Miata is back online!")

@tree.command(name="persona", description="Change Miata's personality.")
async def persona(interaction: discord.Interaction, *, new_persona: str):
    if not is_owner(interaction.user.id):
        if not await request_password(interaction):
            await interaction.response.send_message("❌ Wrong password!", ephemeral=True)
            return

    with open("persona.txt", "w") as f:
        f.write(new_persona)

    await interaction.response.send_message("🧠 Persona updated!")

# 💬 ASK OPENROUTER FUNCTION
def ask_openrouter(system_prompt, user_input):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "openchat/openchat-7b",
        "messages": [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_input.strip()}
        ],
        "temperature": 1.0,
        "max_tokens": 300
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

# 🧠 MIATA CHAT HANDLER
@bot.event
async def on_message(message):
    global bot_enabled
    if message.author.bot or not bot_enabled:
        return

    guild_id = str(message.guild.id)
    if guild_id not in active_channels or message.channel.id != active_channels[guild_id]:
        return

    try:
        with open("persona.txt", "r") as f:
            system_prompt = f.read()
    except:
        await message.channel.send("⚠️ Oops! My personality file is missing!! My whole sparkly brain is gone 😭")
        return

    user_input = message.content.strip()

    try:
        reply = ask_openrouter(system_prompt, user_input)

        reply_lines = reply.strip().splitlines()
        clean_lines = [line for line in reply_lines if line.strip() != ""]
        num_lines = len(clean_lines)

        if num_lines <= 5:
            trimmed_text = "\n".join(clean_lines)
        else:
            trimmed_lines = clean_lines[:8]
            trimmed_text = "\n".join(trimmed_lines)
            if len(clean_lines) > 8:
                trimmed_text += "\n🛞 *Miata ran outta gas mid-sentence... brb vrooming again~*"

        if len(trimmed_text) > 600:
            trimmed_text = trimmed_text[:600].rsplit(" ", 1)[0] + "..."
            if not trimmed_text.endswith("again~*"):
                trimmed_text += "\n🛞 *Miata ran outta gas mid-sentence... brb vrooming again~*"

        await message.channel.send(trimmed_text)

    except Exception as e:
        await message.channel.send(f"💥 My engine coughed up a lug nut! `{str(e)}`")
        
bot.run(TOKEN)






