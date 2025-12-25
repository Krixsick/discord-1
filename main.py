import os
import certifi

# 1. FORCE SSL PATH BEFORE ANYTHING ELSE
os.environ['SSL_CERT_FILE'] = certifi.where()

import discord
from discord.ext import commands, tasks
import aiohttp
import os
from dotenv import load_dotenv
import json
# Load your token
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1453528662891696128 

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

previous_territories = {}
API_URL = "https://api.wynncraft.com/v3/guild/list/territory"
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    if not monitor_territories.is_running():
        monitor_territories.start()

@tasks.loop(seconds=10)
async def monitor_territories():
    global previous_territories
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL) as response:
            territory_data = await response.json()
            with open("data.json", "w") as f:
                json.dump(territory_data, f, indent=4)
            # Create a simplified dictionary: { "Territory Name": "Guild Name" }
            current_territories = {}
            for territory_name, data in territory_data.items():
                guild_data = data.get("guild", {})
                guild_name = guild_data.get("name", "None")
                current_territories[territory_name] = guild_name
            if not previous_territories:
                previous_territories = current_territories
                print("Initialized territory data.")
                return
            # Compare current vs previous
            for territory, new_owner in current_territories.items():
                old_owner = previous_territories.get(territory)
                # If owner changed AND it wasn't just "None"
                if old_owner and new_owner != old_owner:
                    #Calculate how many territories the new guild has
                    total_count = list(current_territories.values()).count(new_owner)
                    #The message
                    channel = bot.get_channel(CHANNEL_ID)
                    if channel:
                        await channel.send(
                            f" **Territory Update!**\n"
                            f"**{territory}** has been taken over by **{new_owner}**! (Previously: {old_owner})\n"
                            f" {new_owner} now controls **{total_count}** territories."
                        )
                        print(f"Alerted: {territory} -> {new_owner}")
            # Update the "previous" state for the next loop
            previous_territories = current_territories


bot.run(TOKEN)