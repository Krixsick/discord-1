
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
                
                #getting the info
                guild_name = data.get("name", "Unknown")
                guild_prefix = data.get("prefix", "N/A")
                guild_level = data.get("level", 0)
                guild_territories = data.get("territories", 0)
                guild_wars = data.get("wars", 0)
                guild_total = data.get("members", {}).get("total", 0)
                               
                role_stars = {
                    "owner": "★★★★★",
                    "chief": "★★★★",
                    "strategist": "★★★",
                    "captain": "★★",
                    "recruiter": "★",
                    "recruit": ""
                }
                # Build member list by role
                members_data = data.get("members", {})
                member_lines = []
                
                for role in ["owner", "chief", "strategist", "captain", "recruiter", "recruit"]:
                    role_members = members_data.get(role, {})
                    if role_members:
                        stars = role_stars[role]
                        for username, member_info in role_members.items():
                            if stars:
                                member_lines.append(f"{stars} {username}")
                            else:
                                member_lines.append(f"　 {username}")  # Indent for recruits
                
                embed = discord.Embed(
                    title=f"{guild_name} [{guild_prefix}]",
                    color=discord.Color.blue()
                )

                embed.add_field(name="Level", value=str(guild_level), inline=True)
                embed.add_field(name="Members", value=str(guild_total), inline=True)
                embed.add_field(name="Territories", value=str(guild_territories), inline=True)
                embed.add_field(name="Wars", value=str(guild_wars), inline=True)

                current_chunk = []
                current_len = 0

                for line in member_lines:
                    if current_len + len(line) > 1024:
                        embed.add_field(name="Members", value="\n".join(current_chunk), inline=False)
                        current_chunk = []
                        current_len = 0
                        field_name = ""  
                    current_chunk.append(line)
                    current_len += len(line) + 1

                embed.add_field(name=field_name, value="\n".join(current_chunk) or "No members", inline=False)
                embed.set_footer(text="★★★★★ Owner | ★★★★ Chief | ★★★ Strategist | ★★ Captain | ★ Recruiter")

                await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(GuildList(bot))