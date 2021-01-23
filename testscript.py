import discord
from discord.ext import commands
from discord.utils import get
import requests
from decouple import config
TRN_API_KEY = config("TRN_API_KEY")

bot = commands.Bot(command_prefix='?')
bot.remove_command('help')
csgoLinks={}

@bot.event
async def on_ready():
    print(f"Succesfully logged into {bot.user}")

bot.run(config("ALT_TOKEN"))
