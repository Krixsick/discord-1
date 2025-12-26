
import discord
from discord.ext import commands, tasks
import aiohttp
import json
from datetime import datetime, timezone
from dotenv import load_dotenv
import os

load_dotenv()
API_URL = os.getenv("API_URL")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

def format_duration(delta):
    total_seconds = int(delta.total_seconds())
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    if days > 0:
        return f"{days}d {hours}h"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"

class TerritoryTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.previous_territories = {}
    
    def cog_unload(self):
        self.monitor_territories.cancel()
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("TerritoryTracker cog loaded")
        if not self.monitor_territories.is_running():
            self.monitor_territories.start()
    
    @tasks.loop(seconds=10)
    async def monitor_territories(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL) as response:
                territory_data = await response.json()
                with open("data.json", "w") as f:
                    json.dump(territory_data, f, indent=4)
                now = datetime.now(timezone.utc)
                current_territories = {}
                #fills in current_territories
                for territory_name, data in territory_data.items():
                    guild_data = data.get("guild")
                    guild_name = guild_data.get("name")
                    guild_acquired_time = data.get("acquired")
                    current_territories[territory_name] = guild_name
                if not self.previous_territories:
                    for territory_name, guild_name in current_territories.items():
                        self.previous_territories[territory_name] = {
                            "guild": guild_name,
                            "acquired": guild_acquired_time
                        }
                    print(f"Initialized {len(self.previous_territories)} territories.")
                    return
                # Compare current vs previous
                for territory, new_owner in current_territories.items():
                    old_data = self.previous_territories.get(territory)
                    old_owner = old_data.get("guild")
                    if old_owner and new_owner != old_owner:
                        acquired_time = old_data.get("acquired")
                        held_duration = format_duration(now - acquired_time)
                        new_owner_count = list(current_territories.values()).count(new_owner)
                        old_owner_count = list(current_territories.values()).count(old_owner)
                        # Build embed
                        embed = discord.Embed(
                            title="Territory Captured!",
                            description=f"**{territory}**",
                            color=discord.Color.red(),
                            timestamp=now
                        )
                        embed.add_field(
                            name="New Owner",
                            value=f"**{new_owner}**\n{new_owner_count} territories",
                            inline=True
                        )
                        embed.add_field(
                            name="Lost By",
                            value=f"**{old_owner}**\n{old_owner_count} territories",
                            inline=True
                        )
                        embed.add_field(
                            name="Time Held",
                            value=held_duration,
                            inline=True
                        )
                        embed.set_footer(text="Wynncraft Territory Tracker")
                        channel = self.bot.get_channel(CHANNEL_ID)
                        if channel:
                            await channel.send(embed=embed)
                            print(f"Alerted: {territory} -> {new_owner}")
                        # Update this territory with new owner and reset timer
                        self.previous_territories[territory] = {
                            "guild": new_owner,
                            "acquired": now
                        }
                # Updates our territories
                for territory, guild_name in current_territories.items():
                    if territory not in self.previous_territories:
                        self.previous_territories[territory] = {
                            "guild": guild_name,
                            "acquired": now
                        }


async def setup(bot):
    await bot.add_cog(TerritoryTracker(bot))