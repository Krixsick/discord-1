import os
import certifi

os.environ['SSL_CERT_FILE'] = certifi.where()
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

async def main():
    await bot.load_extension("guilds.guild_territory")
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
