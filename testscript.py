import discord
from discord.ext import commands
from discord.utils import get
import requests
from decouple import config
TRN_API_KEY = config("TRN_API_KEY")

bot = commands.Bot(command_prefix='?')
bot.remove_command('help')

@bot.event
async def on_ready():
    print(f"Succesfully logged into {bot.user}")

@bot.command()
async def csgo(ctx, player):
    data = requests.get(f"https://public-api.tracker.gg/v2/csgo/standard/profile/steam/{player}", headers={"TRN-Api-Key": TRN_API_KEY}).json()
    data = data['data']
    embed = discord.Embed(title=f"{data['platformInfo']['platformUserHandle']}'s CS:GO Profile'", description=f"Stats for {data['platformInfo']['platformUserHandle']}", color=0xff0000)
    embed.add_field(name="Username:", value=data['platformInfo']['platformUserHandle'], inline=True)
    embed.add_field(name="ID:", value=data['platformInfo']['platformUserId'], inline=True)
    embed.add_field(name="Kills:", value=data['segments'][0]['stats']['kills']['value'], inline=True)
    embed.add_field(name="Deaths:", value=data['segments'][0]['stats']['deaths']['value'], inline=True)
    embed.add_field(name="K/D Rate:", value=data['segments'][0]['stats']['kd']['value'], inline=True)
    embed.add_field(name="Damage:", value=data['segments'][0]['stats']['damage']['value'], inline=True)
    embed.add_field(name="Headshots:", value=data['segments'][0]['stats']['headshots']['value'], inline=True)
    embed.add_field(name="Shots Fired:", value=data['segments'][0]['stats']['shotsFired']['value'], inline=True)
    embed.add_field(name="Shots Hit:", value=data['segments'][0]['stats']['shotsHit']['value'], inline=True)
    embed.add_field(name="Shot Accuracy:", value=data['segments'][0]['stats']['shotsAccuracy']['value'], inline=True)
    embed.add_field(name="Shots Fired:", value=data['segments'][0]['stats']['kd']['value'], inline=True)
    embed.add_field(name="Shots Fired:", value=data['segments'][0]['stats']['kd']['value'], inline=True)
    embed.add_field(name="Shots Fired:", value=data['segments'][0]['stats']['kd']['value'], inline=True)
    await ctx.send(embed=embed)
bot.run("Nzc0NDYyMzcwNDE1Mzc4NDMz.X6YISQ.whEv7Or-K0A7rU25vf8ctaeQbQ0")
