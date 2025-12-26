
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
                    guild_data = data.get("guild", {})
                    guild_name = guild_data.get("name")
                    guild_acquired_time = data.get("acquired")
                    if guild_acquired_time:
                        try:
                            # Wynncraft API format: "2024-01-15T10:30:00.000Z"
                            acquired_time = datetime.fromisoformat(guild_acquired_time.replace("Z", "+00:00"))
                        except Exception as e:
                            print(e)
                            acquired_time = now
                    else:
                        acquired_time = now
                    current_territories[territory_name] = {
                        "guild": guild_name,
                        "acquired": acquired_time
                    }
                #First Run
                
                if not self.previous_territories:
                    self.previous_territories = current_territories.copy()
                    print(f"Initialized {len(self.previous_territories)} territories.")
                    return
                embeds_to_send = []
                
                # Compare current vs previous
                for territory, new_owner in current_territories.items():
                    old_territory = self.previous_territories.get(territory)
                    old_owner = old_territory.get("guild")
                    new_owner = new_owner["guild"]
                    if old_owner and new_owner != old_owner:
                        acquired_time = old_territory.get("acquired", now)
                        held_duration = format_duration(now - acquired_time)
                        new_owner_count = sum(1 for t in current_territories.values() if t["guild"] == new_owner)
                        old_owner_count = sum(1 for t in current_territories.values() if t["guild"] == old_owner)
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
                        embeds_to_send.append(embed)
                        # Update this territory with new owner and reset timer
                        self.previous_territories[territory] = {
                            "guild": new_owner,
                            "acquired": now
                        }
                #only writes in a discord channel territory-alerts
                if embeds_to_send:
                    for guild in self.bot.guilds:
                        channel = discord.utils.get(guild.text_channels, name="territory-alerts")
                        if channel:
                            for embed in embeds_to_send:
                                await channel.send(embed=embed)
                                print(f"Alerted: {territory} -> {new_owner}")
                # Updates our territories
                self.previous_territories = current_territories.copy()

                

async def setup(bot):
    await bot.add_cog(TerritoryTracker(bot))