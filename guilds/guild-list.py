
import discord
from discord.ext import command, tasks
import aiohttp
import json
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://api.wynncraft.com/v3/guild/prefix/<str:guildName>?identifier=<str:username/uuid>"

class GuildList(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Starting")
        if not self.display_guilds.is_running():
            self.display_guilds.start()
    
    async def display_guilds(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL) as response:
                data = response.json()
                with open('data1.json', 'w') as f:
                    json.dump(data, f, indent=4)
    