
import discord
from discord.ext import commands, tasks
import aiohttp
import json
from dotenv import load_dotenv

load_dotenv()



class GuildList(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="guild")
    async def display_guilds(self, ctx, prefix: str):
        api = f"https://api.wynncraft.com/v3/guild/prefix/{prefix}"
        async with aiohttp.ClientSession() as session:
            async with session.get(api) as response:
                data = await response.json()
                with open('data1.json', 'w') as f:
                    json.dump(data, f, indent=4)
                embed = discord.Embed(
                    title=data.get("name", "Unknown Guild"),
                    color=discord.Color.blue()
                )
                embed.add_field(name="Prefix", value=data.get("prefix", "N/A"), inline=True)
                embed.add_field(name="Members", value=data.get("members", {}).get("total", "N/A"), inline=True)
                embed.add_field(name="Level", value=data.get("level", "N/A"), inline=True)
                
                await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(GuildList(bot))