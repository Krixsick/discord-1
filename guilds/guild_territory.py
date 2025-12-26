import discord
from discord.ext import commands, tasks
import aiohttp
import json
from datetime import datetime, timezone
from dotenv import load_dotenv
import os

load_dotenv()
API_URL = os.getenv("API_URL")
# Removed CHANNEL_ID line

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
                
                # Optional: Save to file for debugging
                with open("data.json", "w") as f:
                    json.dump(territory_data, f, indent=4)
                
                now = datetime.now(timezone.utc)
                current_territories = {}
                
                # Parse current data
                for territory_name, data in territory_data.items():
                    guild_data = data.get("guild")
                    guild_name = guild_data.get("name")
                    current_territories[territory_name] = guild_name

                # Initialization (First Run)
                if not self.previous_territories:
                    for t_name, g_name in current_territories.items():
                        raw_acquired = territory_data.get(t_name, {}).get("acquired")
                        if raw_acquired:
                             acquired_val = raw_acquired 
                        else:
                             acquired_val = now

                        self.previous_territories[t_name] = {
                            "guild": g_name,
                            "acquired": acquired_val 
                        }
                    print(f"Initialized {len(self.previous_territories)} territories.")
                    return

                # Detect Changes
                embeds_to_send = []

                for territory, new_owner in current_territories.items():
                    old_data = self.previous_territories.get(territory)
                    old_owner = old_data.get("guild")
                    
                    if old_owner and new_owner != old_owner:
                        # Calculate Duration
                        acquired_str = old_data.get("acquired")
                        if isinstance(acquired_str, str):
                            try:
                                acquired_dt = datetime.strptime(acquired_str, "%Y-%m-%d %H:%M:%S")
                                acquired_dt = acquired_dt.replace(tzinfo=timezone.utc)
                                held_duration = format_duration(now - acquired_dt)
                            except:
                                held_duration = "Unknown"
                        else:
                             held_duration = format_duration(now - acquired_str) if isinstance(acquired_str, datetime) else "Unknown"

                        new_owner_count = list(current_territories.values()).count(new_owner)
                        old_owner_count = list(current_territories.values()).count(old_owner)

                        # Build Embed
                        embed = discord.Embed(
                            title="Territory Captured!",
                            description=f"**{territory}**",
                            color=discord.Color.red(),
                            timestamp=now
                        )
                        embed.add_field(name="New Owner", value=f"**{new_owner}**\n{new_owner_count} territories", inline=True)
                        embed.add_field(name="Lost By", value=f"**{old_owner}**\n{old_owner_count} territories", inline=True)
                        embed.add_field(name="Time Held", value=held_duration, inline=True)
                        embed.set_footer(text="Wynncraft Territory Tracker")
                        
                        embeds_to_send.append(embed)
                        print(f"Alert: {territory} -> {new_owner}")

                        # Update Memory
                        self.previous_territories[territory] = {
                            "guild": new_owner,
                            "acquired": now
                        }

                #Broadcast to all servers
                if embeds_to_send:
                    for guild in self.bot.guilds:
                        # channe search
                        channel = discord.utils.get(guild.text_channels, name="territory-alerts")
                        if channel:
                            try:
                                for embed in embeds_to_send:
                                    await channel.send(embed=embed)
                            except discord.Forbidden:
                                print(f"Missing permissions in {guild.name}")
                       

                #Handles new terr
                for territory, guild_name in current_territories.items():
                    if territory not in self.previous_territories:
                        self.previous_territories[territory] = {
                            "guild": guild_name,
                            "acquired": now
                        }

async def setup(bot):
    await bot.add_cog(TerritoryTracker(bot))