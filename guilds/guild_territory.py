import discord
from discord.ext import commands, tasks
import aiohttp
import json
from datetime import datetime, timezone
from dotenv import load_dotenv
import os

load_dotenv()
API_URL = os.getenv("API_URL")


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

    @tasks.loop(seconds=60)
    async def monitor_territories(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL) as response:
                territory_data = await response.json()

                now = datetime.now(timezone.utc)
                current_territories = {}
                
                for territory_name, data in territory_data.items():
                    guild_data = data.get("guild", {})
                    guild_name = guild_data.get("name")
                    guild_acquired_time = data.get("acquired")
                    if guild_acquired_time:
                        try:
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

                if not self.previous_territories:
                    self.previous_territories = current_territories.copy()
                    print(f"Initialized {len(self.previous_territories)} territories.")
                    return

                all_changes = []

                for territory, new_owner in current_territories.items():
                    old_territory = self.previous_territories.get(territory)
                    if not old_territory:
                        continue
                    old_owner = old_territory.get("guild")
                    new_owner_name = new_owner["guild"]
                    if new_owner_name != old_owner:
                        acquired_time = old_territory.get("acquired", now)
                        held_duration = format_duration(now - acquired_time)
                        new_owner_count = sum(1 for t in current_territories.values() if t["guild"] == new_owner_name)
                        old_owner_count = sum(1 for t in current_territories.values() if t["guild"] == old_owner)

                        all_changes.append({
                            "territory": territory,
                            "new_owner": new_owner_name,
                            "old_owner": old_owner,
                            "held_duration": held_duration,
                            "new_owner_count": new_owner_count,
                            "old_owner_count": old_owner_count,
                            "timestamp": now
                        })

                        self.previous_territories[territory] = {
                            "guild": new_owner_name,
                            "acquired": now
                        }

                print(f"Found {len(all_changes)} changes this cycle")

                if all_changes:
                    for discord_guild in self.bot.guilds:
                        # Find all channels ending with "-territory"
                        for channel in discord_guild.text_channels:
                            if channel.name.endswith("-territory"):
                                # Extract guild name from channel (e.g., "sequoia-territory" -> "sequoia")
                                guild_filter = channel.name.replace("-territory", "").replace("-", " ")
                                
                                for change in all_changes:
                                    # Case-insensitive match for guild name
                                    new_owner_match = change["new_owner"] and guild_filter.lower() == change["new_owner"].lower()
                                    old_owner_match = change["old_owner"] and guild_filter.lower() == change["old_owner"].lower()
                                    
                                    if new_owner_match or old_owner_match:
                                        embed = discord.Embed(
                                            title="Territory Captured!",
                                            description=f"**{change['territory']}**",
                                            color=discord.Color.green() if new_owner_match else discord.Color.red(),
                                            timestamp=change["timestamp"]
                                        )
                                        embed.add_field(
                                            name="New Owner",
                                            value=f"**{change['new_owner']}**\n{change['new_owner_count']} territories",
                                            inline=True
                                        )
                                        embed.add_field(
                                            name="Lost By",
                                            value=f"**{change['old_owner']}**\n{change['old_owner_count']} territories",
                                            inline=True
                                        )
                                        embed.add_field(
                                            name="Time Held",
                                            value=change["held_duration"],
                                            inline=True
                                        )
                                        embed.set_footer(text="Wynncraft Territory Tracker")

                                        try:
                                            await channel.send(embed=embed)
                                            print(f"Alerted {channel.name}: {change['territory']} -> {change['new_owner']}")
                                        except discord.Forbidden:
                                            print(f"No permission to send in {channel.name}")
                                        except Exception as e:
                                            print(f"Error sending to {channel.name}: {e}")

                self.previous_territories = current_territories.copy()


async def setup(bot):
    await bot.add_cog(TerritoryTracker(bot))