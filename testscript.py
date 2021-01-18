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

@bot.command()
async def csgolink(ctx, id):
    data = requests.get(f"https://public-api.tracker.gg/v2/csgo/standard/profile/steam/{id}", headers={"TRN-Api-Key": TRN_API_KEY}).json()
    try:
        data = data['data']
        await ctx.send(f"{str(ctx.author)} is now linked to {data['platformInfo']['platformUserHandle']} \n**NOTE: There is no way to verify you are actually {data['platformInfo']['platformUserHandle']}, this is purely for convenience so you do not have to memorize ID**")
    except KeyError:
        await ctx.send("Invalid ID")
    csgoLinks[ctx.author.id] = data['platformInfo']['platformUserId']

@bot.command()
async def csgo(ctx, *player):
    if len(player) == 0:
        try:
            player = csgoLinks[ctx.author.id]
        except KeyError:
            return await ctx.send("There is no CS:GO ID linked to your account. Run ?csgolink")
    data = requests.get(f"https://public-api.tracker.gg/v2/csgo/standard/profile/steam/{player}", headers={"TRN-Api-Key": TRN_API_KEY}).json()
    try:
        data['errors']
        return await ctx.send("Could not find player, try searching by Steam ID instead. You can run ?csgolink {your_id} so you don't have to keep going back to check your id")
    except KeyError:
        pass
    data = data['data']
    embed = discord.Embed(title=f"{data['platformInfo']['platformUserHandle']}'s CS:GO Profile", description=f"Stats for {data['platformInfo']['platformUserHandle']}", color=0xff0000)
    embed.set_thumbnail(url=data['platformInfo']['avatarUrl'])
    embed.add_field(name="Username:", value=data['platformInfo']['platformUserHandle'], inline=True)
    embed.add_field(name="ID:", value=data['platformInfo']['platformUserId'], inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    embed.add_field(name="Kills:", value=data['segments'][0]['stats']['kills']['value'], inline=True)
    embed.add_field(name="Deaths:", value=data['segments'][0]['stats']['deaths']['value'], inline=True)
    embed.add_field(name="K/D Rate:", value=round(data['segments'][0]['stats']['kd']['value'], 2), inline=True)
    embed.add_field(name="Damage:", value=data['segments'][0]['stats']['damage']['value'], inline=True)
    embed.add_field(name="Headshots:", value=data['segments'][0]['stats']['headshots']['value'], inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    embed.add_field(name="Shots Fired:", value=data['segments'][0]['stats']['shotsFired']['value'], inline=True)
    embed.add_field(name="Shots Hit:", value=data['segments'][0]['stats']['shotsHit']['value'], inline=True)
    embed.add_field(name="Shot Accuracy:", value=f"{round(data['segments'][0]['stats']['shotsAccuracy']['value'], 2)}%", inline=True)
    embed.add_field(name="Bombs Planted:", value=data['segments'][0]['stats']['bombsPlanted']['value'], inline=True)
    embed.add_field(name="Bombs Defused:", value=data['segments'][0]['stats']['bombsDefused']['value'], inline=True)
    embed.add_field(name="Hostages Rescued:", value=data['segments'][0]['stats']['hostagesRescued']['value'], inline=True)
    embed.add_field(name="Wins:", value=data['segments'][0]['stats']['wins']['value'], inline=True)
    embed.add_field(name="Losses:", value=data['segments'][0]['stats']['losses']['value'], inline=True)
    embed.add_field(name="Ties:", value=data['segments'][0]['stats']['ties']['value'], inline=True)
    embed.add_field(name="W/L Rate:", value=round(data['segments'][0]['stats']['wins']['value']/data['segments'][0]['stats']['losses']['value'], 2), inline=True)
    embed.add_field(name="W/L Percentage:", value=f"{round(data['segments'][0]['stats']['wlPercentage']['value'], 2)}", inline=True)
    await ctx.send(embed=embed)

bot.run(config("ALT_TOKEN"))
