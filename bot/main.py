#-----------------------------------------------------------------------INITIALIZATIONS----------------------------------------------------------------------
import discord
from discord.ext import commands
from discord.utils import get
from discord import Webhook, AsyncWebhookAdapter
from discord import FFmpegPCMAudio
from discord import opus
import os
import time
import datetime
from datetime import datetime
from pytz import timezone, utc
import random
import requests
import asyncio
from collections import OrderedDict
import gtts
from gtts import gTTS
import ffmpeg
from mojang import MojangAPI
from mojang import MojangUser
from mojang.exceptions import SecurityAnswerError
from mojang.exceptions import LoginError

bot = commands.Bot(command_prefix='?', intents=discord.Intents.all())
bot.remove_command('help')
guildInfo = {}
clowns = []
raiseErrors = [commands.CommandOnCooldown, commands.NoPrivateMessage, commands.BadArgument, commands.MissingRequiredArgument, commands.UnexpectedQuoteError, commands.DisabledCommand, commands.MissingPermissions, commands.MissingRole, commands.BotMissingPermissions, TimeoutError]
passErrors = [commands.CommandNotFound, commands.NotOwner, commands.CheckFailure]
clownServers = [698735288947834900]
blackListed = []
tempClowns = {}
bedwarsModes = {"solos": "eight_one", "solo": "eight_one", "doubles": "eight_two", "double": "eight_two", "3s": "four_three", "3v3v3v3": "four_three", "triples": "four_three", "4s": "four_four", "4v4v4v4": "four_four", "quadruples":"four_four", "4v4": "two_four",}
modes = {"classic": "classic_duel", "uhc": "uhc_duel", "op": "op_duel", "combo": "combo_duel", "skywars": "sw_duel", "sumo": "sumo_duel", "uhc doubles": "uhc_doubles", "bridge": "bridge",}
xps = [0, 20, 70, 150, 250, 500, 1000, 2000, 3500, 6000, 10000, 15000]
botmaster = 566904870951714826
moves = ["rock", "paper", "scissors"]
emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣"]
teams = ["Team 1", "Team 2", "Team 3", "Team 4", "Team 5", "Team 6", "Team 7", "Team 8"]
ezmessages = ["Wait... This isn't what I typed!", "Anyone else really like Rick Astley?", "Hey helper, how play game?", "Sometimes I sing soppy, love songs in the car.", "I like long walks on the beach and playing Hypixel", "Please go easy on me, this is my first game!", "You're a great person! Do you want to play some Hypixel games with me?", "In my free time I like to watch cat videos on Youtube", "When I saw the witch with the potion, I knew there was trouble brewing.", "If the Minecraft world is infinite, how is the sun spinning around it?", "Hello everyone! I am an innocent player who loves everything Hypixel.", "Plz give me doggo memes!", "I heard you like Minecraft, so I built a computer in Minecraft in your Minecraft so you can Minecraft while you Minecraft", "Why can't the Ender Dragon read a book? Because he always starts at the End.", "Maybe we can have a rematch?", "I sometimes try to say bad things then this happens :(", "Behold, the great and powerful, my magnificent and almighty nemisis!", "Doin a bamboozle fren.", "Your clicks per second are godly.", "What happens if I add chocolate milk to macaroni and cheese?", "Can you paint with all the colors of the wind", "Blue is greener than purple for sure", "I had something to say, then I forgot it.", "When nothing is right, go left.", "I need help, teach me how to play!", "Your personality shines brighter than the sun.", "You are very good at the game friend.", "I like pineapple on my pizza", "I like pasta, do you prefer nachos?", "I like Minecraft pvp but you are truly better than me!", "I have really enjoyed playing with you! <3", "ILY <3", "Pineapple doesn't go on pizza!", "Lets be friends instead of fighting okay?"]
HYPIXEL_KEY = os.environ.get('HYPIXEL_KEY')
TWITCH_CLIENT_ID = os.environ.get('TWITCH_CLIENT_ID')
YT_KEY = os.environ.get('YT_KEY')
TWITCH_AUTH = os.environ.get('TWITCH_AUTH')

async def is_vanilla(ctx):
    try:
        return ctx.guild.id == 698735288947834900
    except AttributeError:
        pass

async def is_guild_owner(ctx):
    try:
        return ctx.guild.owner.id == ctx.author.id
    except AttributeError:
        pass

def convertBooltoStr(bool):
    if bool:
        return "On"
    if not bool:
        return "Off"

def checkstat(data, mode, stat):
    try:
        return data['player']['stats'][mode][stat]
    except KeyError:
        return 0

def getrate(stat1, stat2):
    try:
        return round(stat1/stat2, 2)
    except ZeroDivisionError:
        return 0

def getSkyWarsLevel(xp):
    if xp >= 15000:
        return (xp - 15000) / 10000. + 12
    else:
        for number in xps:
            if not xp > number:
                closestnumber = xps[xps.index(number)-1]
                break
        return round(xps.index(closestnumber) + 1)

def write_roman(num):
    roman = OrderedDict()
    roman[1000] = "M"
    roman[900] = "CM"
    roman[500] = "D"
    roman[400] = "CD"
    roman[100] = "C"
    roman[90] = "XC"
    roman[50] = "L"
    roman[40] = "XL"
    roman[10] = "X"
    roman[9] = "IX"
    roman[5] = "V"
    roman[4] = "IV"
    roman[1] = "I"
    def roman_num(num):
        for r in roman.keys():
            x, y = divmod(num, r)
            yield roman[r] * x
            num -= (r * x)
            if num <= 0:
                break
    return "".join([a for a in roman_num(num)])

def initguild(guild):
    guildInfo[guild.id] = {}
    guildInfo[guild.id]['antiez'] = False
    guildInfo[guild.id]['teamLimit'] = 2
    guildInfo[guild.id]['maximumTeams'] = 1
    guildInfo[guild.id]['TTVCrole'] = "TTVC"


#----------------------------------------------------------------------------BOT-----------------------------------------------------------------------------

#---------------------------------------------------------------------------EVENTS---------------------------------------------------------------------------
@bot.event
async def on_ready():
    print(f"Bot connected with {bot.user} ID:{bot.user.id}")
    global testingserver
    global reports
    testingserver = bot.get_guild(763824152493686795)
    reports = get(testingserver.channels, name="reports")
    get(bot.commands, name="skyblock").update(enabled=False)
    print("Guilds:")
    for guild in bot.guilds:
        initguild(guild)
        print(guild.name)


@bot.event
async def on_guild_join(guild):
    print(f"Joined {guild}")
    game = discord.Game(f"on {len(bot.guilds)} servers. Use ?help to see what I can do!")
    await bot.change_presence(activity=game)
    initguild(guild)


@bot.event
async def on_guild_remove(guild):
    print(f"Left {guild}")
    game = discord.Game(f"on {len(bot.guilds)} servers. Use ?help to see what I can do!")
    await bot.change_presence(activity=game)
    guildInfo.pop(guild.id)


@bot.event
async def on_message_edit(before, message):
    if message.author.id != bot.user.id:
        if not message.author.id in blackListed:
            await bot.process_commands(message)
        if message.guild:
            if message.guild.name == "VanillaMC" and message.channel.id == 782708611603759164 and not message.author.bot and not message.author.guild_permissions.administrator and not message.content.startswith(",suggest"):
                await message.delete()
            messageList = message.content.lower().split()
            if ("ez" in messageList or "kys" in messageList) and guildInfo[message.guild.id]['antiez']:
                webhooks = await message.channel.webhooks()
                webhook = get(webhooks, name="ezbot")
                if not webhook:
                    webhook = await message.channel.create_webhook(name="ezbot")
                print(f"Using webhook {webhook.name}")
                if message.author.nick:
                    username = message.author.nick
                else:
                    username = message.author.name
                await webhook.send(ezmessages[random.randint(0, len(ezmessages))-1], username=username, avatar_url=message.author.avatar_url)
                return await message.delete()
            if message.author.id in clowns and message.guild.id in clownServers:
                await message.add_reaction("🤡")
            elif message.author.id in tempClowns and message.guild.id in clownServers:
                await message.add_reaction("🤡")
                tempClowns.update({message.author.id: tempClowns[message.author.id]+1})
                if tempClowns[message.author.id] == 5:
                    tempClowns.pop(message.author.id)
            if "arman" in message.content.lower() and message.guild.id == 698735288947834900:
                await message.add_reaction("👑")
            if ("prince" in message.content.lower() or "duck" in message.content.lower()) and message.guild.id == 698735288947834900:
                await message.add_reaction("🦆")
            if "rylina" in message.content.lower() or "rylee" in message.content.lower() and message.guild.id == 698735288947834900:
                await message.add_reaction("😎")
            if "coolkid" in message.content.lower() and message.guild.id == 698735288947834900:
                await message.add_reaction("🆒")


@bot.event
async def on_message(message):
    if message.author.id != bot.user.id:
        if not message.author.id in blackListed:
            await bot.process_commands(message)
        if message.guild:
            if message.guild.name == "VanillaMC" and message.channel.id == 782708611603759164 and not message.author.bot and not message.author.guild_permissions.administrator and not message.content.startswith(",suggest"):
                await message.delete()
            messageList = message.content.lower().split()
            if ("ez" in messageList or "kys" in messageList) and guildInfo[message.guild.id]['antiez']:
                webhooks = await message.channel.webhooks()
                if webhooks:
                    webhook = get(webhooks, name="ezbot")
                else:
                    webhook = await message.channel.create_webhook(name="ezbot")
                print(f"Using webhook {webhook.name}")
                if message.author.nick:
                    username = message.author.nick
                else:
                    username = message.author.name
                await webhook.send(ezmessages[random.randint(0, len(ezmessages))-1], username=username, avatar_url=message.author.avatar_url)
                return await message.delete()
            if message.author.id in clowns and message.guild.id in clownServers:
                await message.add_reaction("🤡")
            elif message.author.id in tempClowns and message.guild.id in clownServers:
                await message.add_reaction("🤡")
                tempClowns.update({message.author.id: tempClowns[message.author.id]+1})
                if tempClowns[message.author.id] == 5:
                    tempClowns.pop(message.author.id)
            if "arman" in message.content.lower() and message.guild.id == 698735288947834900:
                await message.add_reaction("👑")
            if ("prince" in message.content.lower() or "duck" in message.content.lower()) and message.guild.id == 698735288947834900:
                await message.add_reaction("🦆")


@bot.event
async def on_command_error(ctx, error):
    if "TimeoutError" in str(error):
        return await ctx.send("Timed out.")
    for e in raiseErrors:
        if isinstance(error, e):
            return await ctx.send(error)
    for e in passErrors:
        if isinstance(error, e):
            return
    await ctx.send("Error. This has been reported and will be reviewed shortly.")
    embed = discord.Embed(title="Error Report", description=None, color=0xff0000)
    embed.add_field(name="Guild Name:", value=ctx.guild.name, inline=True)
    embed.add_field(name="Guild ID:", value=ctx.guild.id, inline=True)
    embed.add_field(name="Guild Owner:", value=str(ctx.guild.owner), inline=True)
    embed.add_field(name="Channel:", value=ctx.channel.name, inline=True)
    embed.add_field(name="Error Victim:", value=str(ctx.author), inline=True)
    embed.add_field(name="Victim ID:", value=ctx.author.id, inline=True)
    embed.add_field(name="Error:", value=error, inline=False)
    await reports.send(bot.get_user(botmaster).mention, embed=embed)
    print(error)


@bot.event
async def on_reaction_add(reaction, user):
    if not user.bot:
        if reaction.message.content == "React to get into your teams" and reaction.message.author == bot.user:
            if not get(user.roles, name="Banned from event"):
                if str(reaction) in emojis:
                    team = teams[emojis.index(str(reaction))]
                    role = get(user.guild.roles, name=team)
                    if len(role.members) >= guildInfo[reaction.message.guild.id]['teamLimit']:
                        return await reaction.remove(user)
                    for eachteam in teams:
                        if get(user.roles, name=eachteam):
                            return await reaction.remove(user)
                    await user.add_roles(role)
                    for channel in user.guild.text_channels:
                        if "event-logs" in str(channel.name):
                            if len(role.members)>1:
                                for member in role.members:
                                    if not str(member) == str(user):
                                        await channel.send(f"{user.mention} joined {str(team)} and is now teaming with {member.mention}")
                            else:
                                await channel.send(f"{user.mention} joined {str(role)}")
                            return
                else:
                    await reaction.remove(user)
        try:
            dic = reaction.message.embeds[0].to_dict()
            if dic['title'].startswith("(closed)"):
                await reaction.remove(user)
        except IndexError:
            pass
        except KeyError:
            pass
        try:
            dic = reaction.message.embeds[0].to_dict()
            footer = dic['footer']['text']
            if footer.startswith("Poll by"):
                if str(reaction) in emojis:
                    for thereaction in reaction.message.reactions:
                        if not thereaction == reaction:
                            await thereaction.remove(user)
                else:
                    await reaction.remove(user)
        except IndexError:
            pass
        except KeyError:
            pass
        if reaction.message.content == "Teams are now closed.":
            await reaction.remove(user)


@bot.event
async def on_reaction_remove(reaction, user):
    if reaction.message.content == "React to get into your teams" and reaction.message.author.id == bot.user.id:
        if str(reaction) in emojis:
            team = teams[emojis.index(str(reaction))]
            role = get(user.guild.roles, name=team)
            if role in user.roles:
                await user.remove_roles(role)
                for channel in user.guild.text_channels:
                    if "event-logs" in str(channel):
                        await channel.send(f"{user.mention} left {team}")


#-------------------------------------------------------------------------------COMMANDS---------------------------------------------------------------------------------------
#------------------------------------------------------------------------------OWNER ONLY--------------------------------------------------------------------------------------
@bot.command()
@commands.is_owner()
async def blacklist(ctx, member : discord.Member):
    global blackListed
    if member.id in blackListed:
        return await ctx.send(f"{str(member)} is already blacklisted")
    blackListed.append(member.id)
    await ctx.send(f"Blacklisted {str(member)}")


@bot.command()
@commands.is_owner()
async def unblacklist(ctx, member : discord.Member):
    global blackListed
    if not member.id in blackListed:
        return await ctx.send(f"{str(member)} is not blacklisted")
    blackListed.remove(member.id)
    await ctx.send(f"Unblacklisted {str(member)}")


@bot.command()
@commands.is_owner()
async def blacklisted(ctx):
    message = ""
    for x in blackListed:
        message = f"{message}\n{get(ctx.guild.members, id=x)}"
    await ctx.send(f"List of blacklisted members: {message}")


@bot.command()
@commands.is_owner()
async def remoteshutdown(ctx):
    await ctx.send("Shutting down")
    bot.close()


@bot.command()
@commands.is_owner()
async def disablecommand(ctx, commandName):
    command = get(bot.commands, name=commandName)
    command.update(enabled=False)
    await ctx.send(f"Disabled command {command}")


@bot.command()
@commands.is_owner()
async def enablecommand(ctx, commandName):
    command = get(bot.commands, name=commandName)
    command.update(enabled=True)
    await ctx.send(f"Enabled command {command}")


@bot.command()
@commands.is_owner()
async def guilds(ctx):
    for guild in bot.guilds:
        await ctx.send(f"{guild.name}: \nOwner: {guild.owner.name} \n# of Members: {guild.member_count}")


#------------------------------------------------------------------------------VANILLAMC ONLY--------------------------------------------------------------------------------------
@bot.command()
@commands.check(is_vanilla)
@commands.has_role("Super Donator")
@commands.bot_has_guild_permissions(add_reactions=True)
@commands.cooldown(1, 900, commands.BucketType.user)
async def clown(ctx, member : discord.Member):
    if member.id in tempClowns:
        return await ctx.send(f"{member.name} is already a clown")
    tempClowns[member.id] = 0
    await ctx.send(f"{member.mention} is now a clown for the next 5 messages")


@bot.command()
@commands.check(is_vanilla)
@commands.has_role("Owner")
@commands.bot_has_guild_permissions(add_reactions=True)
async def permclown(ctx, member : discord.Member):
    if member.id == 566904870951714826:
        await ctx.send("You tried to clown senpai???? UNO REVERSE YOU'RE NOW THE CLOWN")
        member = ctx.message.author
    global clowns
    if member.id in clowns:
        return await ctx.send(f"{member.name} is already a clown")
    clowns.append(member.id)
    await ctx.send(f"{member.mention} is now a clown")


@bot.command()
@commands.check(is_vanilla)
@commands.has_role("Owner")
@commands.bot_has_guild_permissions(add_reactions=True)
async def unclown(ctx, member : discord.Member):
    if member == ctx.message.author:
        return await ctx.send('lol u cant unclown urself get good')
    global clowns
    if not member.id in clowns:
        return await ctx.send(f"{member.name} is not a clown")
    clowns.remove(member.id)
    await ctx.send(f"{member.mention} is no longer a clown")


@bot.command()
@commands.check(is_vanilla)
@commands.is_owner()
async def clownlist(ctx):
    message = ""
    for x in clowns:
        message = f"{message}\n{get(ctx.guild.members, id=x)}"
    await ctx.send(f"List of permanent clowns: {message}")


@bot.command()
@commands.check(is_vanilla)
@commands.has_permissions(manage_roles=True)
async def duel(ctx):
    role = get(ctx.guild.roles, name='Hypixel Dueler')
    for member in ctx.message.mentions:
        await member.add_roles(role)
        await ctx.send(f"{str(member)} is now a Dueler")


@bot.command()
@commands.check(is_vanilla)
@commands.has_permissions(manage_roles=True)
async def clearduels(ctx):
    role = get(ctx.guild.roles, name="Hypixel Dueler")
    for member in role.members:
        await member.remove_roles(role)
    await ctx.send("Removed all duelers")


@bot.command()
@commands.check(is_vanilla)
@commands.has_permissions(administrator=True)
async def promote(ctx, member : discord.Member):
        for channel in ctx.guild.text_channels:
            if "ratings" in str(channel):
                messages = await channel.history(limit=10).flatten()
                for message in messages:
                    if member in message.content or member.replace("!", "") in message.content:
                        if messages.index(message) < len(messages) - 2:
                            message1above = messages[messages.index(message)+1]
                            content = message.content[:4] + message1above.content[4:]
                            content1 = message1above.content[:4] + message.content[4:]
                            await message.edit(content=content)
                            await message1above.edit(content=content1)
                            return
                        else:
                            return
                message = messages[0]
                content = message.content[:3] + ctx.message.mentions[0].mention
                return await message.edit(content=content)


#------------------------------------------------------------------------------MISCELLANEOUS--------------------------------------------------------------------------------------
@bot.command()
async def help(ctx, *category):
    if len(category) <= 0:
        embed = discord.Embed(title="Categories", description="This is a list of all the types of commands I can do", color=0xff0000)
        embed.set_thumbnail(url=bot.user.avatar_url)
        embed.add_field(name="VC Commands (?help VC):", value="Commands to help you manage your Voice Channels:", inline=False)
        embed.add_field(name="Team Commands (?help teams)", value="Commands that help you manage your teams for your game nights", inline=False)
        embed.add_field(name="Game Commands (?help games)", value="Commands for mini-games that all members can play", inline=False)
        embed.add_field(name="Game Stats Commands (?help stats)", value="Commands to see Minecraft player's stats", inline=False)
        embed.add_field(name="Miscellaneous Commands (?help misc)", value="All other commands I can do!", inline=False)
        embed.add_field(name="APIs (?help apis)", value=f"APIs used by the {str(bot.user)}", inline=False)
        embed.set_footer(text=f"{str(bot.user)} is a bot created and maintained by tanju_shorty#7767")
    elif category[0] == "VC":
        embed=discord.Embed(title="VC Commands", description="Commands I can do to help you manage your voice channels", color=0xff0000)
        embed.add_field(name="?mute (member or 'all' or 'channel-all')", value="Server mutes a member. 'channel-all' mutes all people in the channel you are currently in while 'all' mutes everyone a voice channel in the server. (Requires permission Mute Members)", inline=False)
        embed.add_field(name="?unmute (member or 'all' or 'channel-all')", value="Server unmutes a member (Requires permission Mute Members)", inline=False)
        embed.add_field(name="?deafen (member or 'all' or 'channel-all')", value="Server deafens a member (Requires permission Deafen Members)", inline=False)
        embed.add_field(name="?undeafen (member or 'all' or 'channel-all')", value="Server undeafens a member (Requires permission Deafen Members)", inline=False)
        embed.add_field(name="?dc (member or 'all' or 'channel-all')", value="Disconnects a member from their voice channel (Requires permission Move Members)", inline=False)
        embed.add_field(name="?move (member or 'all' or 'channel-all')", value="Moves member to another voice channel (Requires permission Move Members)", inline=False)
        embed.add_field(name="?moveteams", value="Moves all people who are in main Voice Channel back to their Team Voice Channel (Requires permission Move Members)", inline=False)
        embed.add_field(name="?speak (message)", value="Joins a voicechannel and uses TTS to speak a message. Useful if you are unable to unmute", inline=False)
    elif category[0] == "teams":
        embed=discord.Embed(title="Team Commands", description="Commands I can do to manage your teams for game nights", color=0xff0000)
        embed.add_field(name="?createteams", value="Creates a team menu where people can react to join teams (max limit of 2 and member can only be in 1 team) (Requires permission Manage Roles)", inline=False)
        embed.add_field(name="?closeteams", value="Close a team menu so people can no longer react (Requires permission Manage Roles)", inline=False)
        embed.add_field(name="?checkteams", value="Checks to make sure no one has somehow got into 2 teams (Requires permission Manage Roles)", inline=False)
        embed.add_field(name="?clearteams", value="Removes all the team roles from all members (Requires permission Manage Roles)", inline=False)
        embed.add_field(name="?clearteam (team)", value="Removes the specified team role from all members", inline=False)
        embed.add_field(name="?setteam (team) (*member)", value="Gives the specified member(s) the specified team role (first clears the members other teams) (Requires permission Manage Roles)", inline=False)
        embed.add_field(name="?eventban (user or 'all')", value="Prevents a user from joining teams or using team text/voice channels (Requires permission Manage Roles)", inline=False)
        embed.add_field(name="?eventunban (user or 'all')", value="Allows a user to join teams and use team text/voice channels (Requires permission Manage Roles)", inline=False)
        embed.add_field(name="?lockevents", value="Locks the team voice channels so that ONLY people with the team role can join", inline=False)
        embed.add_field(name="?unlockevents", value="Unlocks the team voice channels so that ANYONE can join them", inline=False)
    elif category[0] == "misc":
        embed=discord.Embed(title="Miscellaneous Commands", description="All other commands I can do!", color=0xff0000)
        embed.add_field(name="?nick (user)", value="Changes the nickname of a member (Requires permission Manage Nicknames)", inline=False)
        embed.add_field(name="?poll (Poll) (*options)", value="Creates a poll where you can only vote once", inline=False)
        embed.add_field(name="?closepoll", value="Closes a poll and shows the final results", inline=False)
        embed.add_field(name="?ping", value="Checks the bots ping in ms", inline=False)
        embed.add_field(name="?quote (@user) (quote)", value="Quotes a user using a webhook", inline=False)
        embed.add_field(name="?avatar (@user) (format)", value="Returns the avatar of a member in the specified format(‘webp’, ‘jpeg’, ‘jpg’, ‘png’ or ‘gif’)", inline=False)
        embed.add_field(name="?perms (@user)", value="Sends the server permissions for a certain member", inline=False)
        embed.add_field(name="?invite (*(max_age) (max_uses) (reason))", value="Generates a invite to the channel with the specified maximum age, uses, and reason. If no args are provided, it will default to infinite uses, infinite age, and no reason", inline=False)
        embed.add_field(name="?report", value="Report a problem to the bot developers", inline=False)
        embed.add_field(name="?settings", value="Tweak settings for your guild", inline=False)
        embed.add_field(name="?rps (user or 'bot')", value="Challenges a member (or the bot) to Rock Paper Scissors", inline=False)
    elif category[0] == "stats":
        embed=discord.Embed(title="Game Stat Commands", description="Commands to see a player's stats in various games", color=0xff0000)
        embed.add_field(name="?minecraft (minecraft_player)", value="Shows stats about a Minecraft player", inline=False)
        embed.add_field(name="?skin (minecraft_player)", value="Shows the skin of a Minecraft player", inline=False)
        embed.add_field(name="?hypixel (minecraft_player)", value="Shows Hypixel stats about a Minecraft player", inline=False)
        embed.add_field(name="?bedwars (minecraft_player) (optional_mode)", value="Shows stats about a Hypixel Bedwars player \nOptional modes are: solos, doubles, 3v3v3v3, 4v4v4v4, 4v4", inline=False)
        embed.add_field(name="?skywars (minecraft_player) (optional_mode)", value="Shows stats about a Hypixel Skywars player \nOptional modes are: solos normal, solos insane, teams normal, teams insane", inline=False)
        embed.add_field(name="?duels (minecraft_player) (optional_mode)", value="Shows stats about a Hypixel Duels player \nOptional modes are classic, uhc, op, sumo, skywars, uhc doubles, combo, bridge", inline=False)
        embed.add_field(name="?fortnite (fortnite_player)", value="Shows stats about a Fortnite player", inline=False)
        embed.add_field(name="?twitch (channel)", value="Shows stats of a Twitch streamer", inline=False)
        embed.add_field(name="?youtube (channel)", value="Shows stats of a YouTube channel", inline=False)
    elif category[0] == "apis":
        embed = discord.Embed(title="APIs used for statistics", description=f"All APIs used by {str(bot.user)}", color=0xff0000)
        embed.add_field(name="Hypixel API", value="https://api.hypixel.net/", inline=False)
        embed.add_field(name="Mojang API", value="https://mojang.readthedocs.io/en/latest/", inline=False)
        embed.add_field(name="Fortnite API", value="https://fortnite-api.com/", inline=False)
        embed.add_field(name="Twitch API", value="https://dev.twitch.tv/docs/api/", inline=False)
        embed.add_field(name="YouTube API", value="https://developers.google.com/youtube/", inline=False)
    else:
        return await ctx.send("Invalid category")
    await ctx.send(embed=embed)


@bot.command()
async def settings(ctx, *setting):
    if len(setting) == 0:
        embed = discord.Embed(title=f"Settings for {ctx.guild.name}", description="To edit a setting use '?settings setting on/off", color=0xff0000)
        embed.add_field(name=f"Anti-Ez: `{convertBooltoStr(guildInfo[ctx.guild.id]['antiez'])}`", value="?settings antiez off")
        embed.add_field(name=f"Maximum members allowed on one team: `{guildInfo[ctx.guild.id]['teamLimit']}`", value="?settings teamlimit 1")
        embed.add_field(name=f"Role required to use ?speak (Text to Voice Channel): `{guildInfo[ctx.guild.id]['TTVCrole']}`", value="?settings TTVCrole some_role")
    elif len(setting) == 2:
        if not ctx.author.guild_permissions.administrator:
            return await ctx.send(f"You are missing Administrator permission(s) to run this command.")
        if setting[0] == "antiez":
            if setting[1] == "on":
                guildInfo[ctx.guild.id]['antiez'] = True
            elif setting [1] == "off":
                guildInfo[ctx.guild.id]['antiez'] = False
            else:
                return await ctx.send("Argument must be 'on' or 'off'")
            embed = discord.Embed(title=f"Anti-EZ is now {convertBooltoStr(guildInfo[ctx.guild.id]['antiez'])}", description=None, color=0xff0000)
        elif setting[0] == "teamlimit":
            try:
                setting = int(setting[1])
            except ValueError:
                return await ctx.send("Argument must be a number")
            guildInfo[ctx.guild.id]['teamLimit'] = setting
            embed = discord.Embed(title=f"Maximum members allowed in one team is now {guildInfo[ctx.guild.id]['teamLimit']}", description=None, color=0xff0000)
        elif setting[0] == "TTVCrole":
            if not get(ctx.guild.roles, name=setting[1]):
                return await ctx.send('Invalid role')
            guildInfo[ctx.guild.id]['TTVCrole'] = setting[1]
            embed = discord.Embed(title=f"TTVC Role is now set to {guildInfo[ctx.guild.id]['TTVCrole']}", description=None, color=0xff0000)
        else:
            return await ctx.send("Invalid setting")
    else:
        return await ctx.send("Invalid arguments")
    await ctx.send(embed=embed)


@bot.command()
@commands.has_guild_permissions(use_voice_activation=True, connect=True, speak=True)
@commands.bot_has_guild_permissions(use_voice_activation=True, connect=True, speak=True)
async def speak(ctx, *message):
    role = get(ctx.author.roles, name=guildInfo[ctx.guild.id]['TTVCrole'])
    if not role:
        return await ctx.send(f"Role {guildInfo[ctx.guild.id]['TTVCrole']} is required to use TTVC")
    fullmessage = f"{ctx.author.name} says "
    for messageVar in message:
        fullmessage = f"{fullmessage} {messageVar}"
    if ctx.guild.voice_client:
        vc = ctx.guild.voice_client
    elif ctx.author.voice:
        vc = await ctx.author.voice.channel.connect()
    else:
        return await ctx.send("You are not in a voice channel.")
    tts = gtts.gTTS(fullmessage, lang="en")
    tts.save("text.mp3")
    while True:
        try:
            vc.play(discord.FFmpegPCMAudio("text.mp3"))
            return
        except discord.ClientException:
            pass


@bot.command()
@commands.has_guild_permissions(create_instant_invite=True)
@commands.bot_has_guild_permissions(create_instant_invite=True)
async def invite(ctx, *args):
    max_age = 0
    max_uses = 0
    reason = None
    if len(args) != 0:
        try:
            max_age = args[0]
            max_uses = args[1]
            reason = args[2]
        except IndexError:
            return await ctx.send("Invalid args. 'max_age', 'max_uses', 'reason' ")
    await ctx.send(f"Invite with a maximum age of {max_age} seconds, {max_uses} maximum uses, and with {reason} as the reason. \n{await ctx.channel.create_invite(max_age=max_age, max_uses=max_uses, reason=reason)}")


@bot.command()
@commands.guild_only()
async def perms(ctx, member : discord.Member):
    await ctx.send(f"Perms for {str(member)} in {ctx.guild}")
    perms = ""
    for perm in member.guild_permissions:
        perms = f"{perms} {perm}"
    await ctx.send(perms)


@bot.command()
async def avatar(ctx, member : discord.Member, *format):
    if not format:
        format = "png"
    try:
        await ctx.send(member.avatar_url_as(format=format, size=1024))
    except discord.InvalidArgument:
        return await ctx.send("Format must be 'webp', 'gif' (if animated avatar), 'jpeg', 'jpg', 'png'")


@bot.command()
@commands.bot_has_guild_permissions(add_reactions=True, manage_messages=True)
async def poll(ctx, poll, *options):
    if len(options) > 8:
        return await ctx.send("Maximum options = 8")
    if len(options) < 2:
        return await ctx.send("Minimum of 2 options")
    embed = discord.Embed(title=poll, description=None, color=0xff0000)
    for option in options:
        embed.add_field(name=emojis[options.index(option)], value="\u200b", inline=True)
        embed.add_field(name=option, value="\u200b", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
    embed.set_footer(text=f"Poll by {str(ctx.author)}")
    msg = await ctx.send(embed=embed)
    await ctx.message.delete()
    for emoji in emojis:
        if emojis.index(emoji) < len(options):
            await msg.add_reaction(emoji)
        else:
            return


@bot.command()
@commands.bot_has_guild_permissions(add_reactions=True, manage_messages=True)
async def closepoll(ctx):
        close = await ctx.send("React to the poll I must close with an ❌")
        def check(reaction, user):
            return user == ctx.author and str(reaction) == "❌"
        reaction, user = await bot.wait_for('reaction_add', timeout=120.0, check=check)
        dic = reaction.message.embeds[0].to_dict()
        footer = dic['footer']['text']
        footer = footer[8:]
        title = f"(closed) {dic['title']}"
        if str(user) == footer:
            embed=discord.Embed(title=title, description=None, color=0xff0000)
            await ctx.message.delete()
            await close.delete()
            x = 0
            for field in reaction.message.embeds[0].fields:
                if not field.name in emojis and not field.name=="\u200b":
                    eachreaction = reaction.message.reactions[x]
                    if str(eachreaction) in emojis:
                        embed.add_field(name=eachreaction.count-1, value="\u200b", inline=True)
                        embed.add_field(name=f" person(s) voted {field.name}", value="\u200b", inline=True)
                        embed.add_field(name="\u200b", value="\u200b", inline=True)
                    x = x + 1
            await reaction.message.edit(embed=embed)
            await reaction.remove(user)
        else:
            await ctx.send(f"Only {dic} can close that poll")


@bot.command()
@commands.bot_has_guild_permissions(manage_nicknames=True)
@commands.has_permissions(manage_nicknames=True)
async def nick(ctx, member : discord.Member, *nick):
            joinednick = ""
            if len(nick) == 0:
                joinednick = member.name
                await ctx.send(f"Changed {member.name}'s nickname from {member.nick} to {joinednick}")
                await member.edit(nick=None)
            else:
                for nickvar in nick:
                    joinednick = f"{joinednick}{nickvar} "
                if member.nick:
                    nick = member.nick
                else:
                    nick = member.name
                try:
                    await member.edit(nick=joinednick)
                except discord.HTTPException:
                    return await ctx.send("Nickname must be 32 characters or fewer in length.")
                await ctx.send(f"Changed {member.name}'s nickname from {nick} to {joinednick}")


@bot.command()
@commands.cooldown(1, 5, commands.BucketType.channel)
async def ping(ctx):
    t = await ctx.send("Pong!")
    await t.edit(content=f'Pong! {(t.created_at-ctx.message.created_at).total_seconds() * 1000}ms')


@bot.command()
@commands.bot_has_guild_permissions(manage_webhooks=True)
async def quote(ctx, member : discord.Member, *messagevar):
    message = ""
    for m in messagevar:
        message = f"{message} {m}"
    webhooks = await ctx.channel.webhooks()
    for webhook in webhooks:
        if webhook.user == bot.user:
            if member.nick:
                username = member.nick
            else:
                username = member.name
            await webhook.send(message, username=username, avatar_url=member.avatar_url)
            return await ctx.message.delete()
    webhook = await ctx.channel.create_webhook(name="quotebot")
    if member.nick:
        username = member.nick
    else:
        username = member.name
    await webhook.send(message, username=username, avatar_url=member.avatar_url)
    return await ctx.message.delete()


@bot.command()
@commands.cooldown(1, 600, commands.BucketType.guild)
async def report(ctx):
    await ctx.send("Please write your message as to what errors/problems you are experiencing. This will timeout in 3 minutes")
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    message = await bot.wait_for('message', timeout=180, check=check)
    embed = discord.Embed(title="Report", description=None, color=0xff0000)
    embed.add_field(name="Guild Name:", value=ctx.guild.name, inline=True)
    embed.add_field(name="Guild ID:", value=ctx.guild.id, inline=True)
    embed.add_field(name="Guild Owner:", value=str(ctx.guild.owner), inline=True)
    embed.add_field(name="Reporter:", value=str(ctx.author), inline=True)
    embed.add_field(name="Reporter ID:", value=ctx.author.id, inline=True)
    embed.add_field(name="Report:", value=message.content, inline=False)
    await ctx.send(embed=embed)
    await reports.send(embed=embed)
    await ctx.send("Your report is submitted")


#------------------------------------------------------------------------------VOICE CHANNEL MANAGEMENT--------------------------------------------------------------------------------------
@bot.command()
@commands.bot_has_guild_permissions(manage_channels=True)
@commands.has_permissions(manage_channels=True)
async def lockevents(ctx):
        for team in teams:
            channel = get(ctx.guild.voice_channels, name=team)
            if not channel:
                return await ctx.send("Could not find voice channel, your server may not be setup for Game Events yet. Run ?setup")
            perms = channel.overwrites_for(ctx.guild.default_role)
            perms.connect = False
            await channel.set_permissions(ctx.guild.default_role, overwrite=perms)
            await channel.edit(user_limit=guildInfo[ctx.guild.id]['teamLimit'])
        await ctx.send("Locked all voice channels")


@bot.command()
@commands.bot_has_guild_permissions(manage_channels=True)
@commands.has_guild_permissions(manage_channels=True)
async def unlockevents(ctx):
        for team in teams:
            voicechannel = get(ctx.guild.voice_channels, name=team)
            if not voicechannel:
                return await ctx.send("Could not find voice channel, your server may not be setup for Game Events yet. Run ?setup")
            await voicechannel.set_permissions(ctx.guild.default_role, connect=True)
            await voicechannel.edit(user_limit=None)
        await ctx.send("Unlocked all voice channels")


@bot.command()
@commands.bot_has_guild_permissions(move_members=True)
@commands.has_guild_permissions(move_members=True)
async def move(ctx, member, *channel):
        joinedchannel = ""
        for arg in channel:
            joinedchannel = f"{joinedchannel}{arg} "
        channel = get(ctx.guild.voice_channels, name=joinedchannel[:-1])
        if not channel:
            return await ctx.send("That voice channel doest not exist.")
        if member == "channel-all":
            if not ctx.author.voice:
                return await ctx.send("You are not in a voice channel")
            for member in ctx.author.voice.channel.members:
                await member.move_to(channel)
            await ctx.send(f"Moved all in {ctx.author.voice.channel.name} to {channel.name}")
        elif member == "server-all":
            for voice_channel in ctx.guild.voice_channels:
                for member in voice_channel.members:
                    await member.move_to(channel)
            await ctx.send(f"Moved all members to {channel.name}")
        else:
            try:
                member = ctx.message.mentions[0]
            except IndexError:
                return await ctx.send("Invalid member")
            try:
                await member.edit(voice_channel=channel)
                await ctx.send(f"Moved {str(member)} to {str(channel)}")
            except discord.errors.HTTPException:
                await ctx.send("That member is not in a VC")


@bot.command()
@commands.bot_has_guild_permissions(mute_members=True)
@commands.has_guild_permissions(mute_members=True)
async def mute(ctx, member):
        if member == "channel-all":
            if not ctx.author.voice.channel:
                return await ctx.send("You are not in a voice channel")
            for member in ctx.author.voice.channel.members:
                await member.edit(mute=True)
            await ctx.send(f"Muted all in {ctx.author.voice.channel.name}")
        elif member == "server-all":
            for voicechannel in ctx.guild.voice_channels:
                for member in voicechannel.members:
                    await member.edit(mute=True)
            await ctx.send("Muted all")
        else:
            try:
                member = ctx.message.mentions[0]
                await member.edit(mute=True)
                await ctx.send(f"Muted {str(member)}")
            except discord.errors.HTTPException:
                await ctx.send("That member is not in a VC")
            except IndexError:
                await ctx.send("That is not a valid user")


@bot.command()
@commands.bot_has_guild_permissions(deafen_members=True)
@commands.has_guild_permissions(deafen_members=True)
async def deafen(ctx, member):
        if member == "channel-all":
            if not ctx.author.voice.channel:
                return await ctx.send("You are not in a voice channel")
            for member in ctx.author.voice.channel.members:
                await member.edit(deafen=True)
            await ctx.send(f"Deafened all in {ctx.author.voice.channel.name}")
        elif member == "server-all":
            for voicechannel in ctx.guild.voice_channels:
                for member in voicechannel.members:
                    await member.edit(deafen=True)
            await ctx.send("Deafened all")
        else:
            try:
                member = ctx.message.mentions[0]
                await member.edit(deafen=True)
                await ctx.send(f"Deafened {str(member)}")
            except discord.errors.HTTPException:
                await ctx.send("That member is not in a VC")
            except IndexError:
                await ctx.send("That is not a valid user")


@bot.command()
@commands.bot_has_guild_permissions(mute_members=True)
@commands.has_guild_permissions(mute_members=True)
async def unmute(ctx, member):
        if member == "channel-all":
            if not ctx.author.voice:
                return await ctx.send("You are not in a voice channel")
            for member in ctx.author.voice.channel.members:
                await member.edit(mute=False)
            await ctx.send(f"Unmuted all in {ctx.author.voice.channel.name}")
        elif member == "server-all":
            for voicechannel in ctx.guild.voice_channels:
                for member in voicechannel.members:
                    await member.edit(mute=False)
            await ctx.send("Unmuted all")
        else:
            try:
                member = ctx.message.mentions[0]
                await member.edit(mute=False)
                await ctx.send(f"Unmuted {str(member)}")
            except discord.errors.HTTPException:
                await ctx.send("That member is not in a VC")
            except IndexError:
                await ctx.send("That is not a valid user")


@bot.command()
@commands.bot_has_guild_permissions(deafen_members=True)
@commands.has_guild_permissions(deafen_members=True)
async def undeafen(ctx, member):
        if member == "channel-all":
            if not ctx.author.voice:
                return await ctx.send("You are not in a voice channel")
            for member in ctx.author.voice.channel.members:
                await member.edit(deafen=False)
            await ctx.send(f"Undeafened all in {ctx.author.voice.channel.name}")
        if member == "server-all":
            for voicechannel in ctx.guild.voice_channels:
                for member in voicechannel.members:
                    await member.edit(deafen=False)
            await ctx.send("Undeafened all members")
        else:
            try:
                member = ctx.message.mentions[0]
                await member.edit(deafen=False)
                await ctx.send(f"Undeafend {str(member)}")
            except discord.errors.HTTPException:
                await ctx.send("That member is not in a VC")
            except IndexError:
                await ctx.send("That is not a valid user")


@bot.command()
@commands.bot_has_guild_permissions(move_members=True)
@commands.has_guild_permissions(move_members=True)
async def dc(ctx, member):
    if member == "channel-all":
        if not ctx.author.voice:
            return await ctx.send("You are not in a voice channel")
        for member in ctx.author.voice.channel.members:
            await member.move_to(None)
        await ctx.send(f"Disconnected all in {ctx.author.voice.channel.name}")
    elif member == "server-all":
        for voicechannel in ctx.guild.voice_channels:
            for member in voicechannel.members:
                await member.move_to(None)
        await ctx.send("Disconnected all")
    else:
        try:
            member = ctx.message.mentions[0]
        except IndexError:
            return await ctx.send("That is not a valid user")
        if not member.voice:
            return await ctx.send("That member is not in a VC")
        await member.edit(voice_channel=None)
        await ctx.send(f"Disconnected {str(member)}")


@bot.command()
@commands.guild_only()
@commands.bot_has_guild_permissions(move_members=True)
@commands.has_guild_permissions(move_members=True)
async def moveteams(ctx):
        for voicechannel in ctx.guild.voice_channels:
            if "Events" in str(voicechannel):
                for member in voicechannel.members:
                    for team in teams:
                        if get(member.roles, name=team):
                            await member.edit(voice_channel=get(ctx.guild.voice_channels, name=team))
                            await ctx.send(f"Moved {str(member)} to {team}")
                return
        await ctx.send("Could not find voice channel, your server may not be setup for Game Events yet. Run ?setup")


#------------------------------------------------------------------------------TEAM/EVENT MANAGEMENT--------------------------------------------------------------------------------------
@bot.command()
@commands.bot_has_guild_permissions(manage_roles=True)
@commands.has_guild_permissions(manage_roles=True)
async def eventban(ctx, member : discord.Member):
        role = get(ctx.guild.roles, name="Banned from event")
        if not role:
            return await ctx.send("Could not find role, your server may not be setup for Game Events yet. Run ?setup")
        if member.id == botmaster:
            return await ctx.send("I would never ban senpai")
        if role in member.roles:
            await ctx.send("That user is already banned")
        else:
            await member.add_roles(role)
            await ctx.send(f"Banned {str(member)} from events")


@bot.command()
@commands.bot_has_guild_permissions(manage_roles=True)
@commands.has_guild_permissions(manage_roles=True)
async def eventunban(ctx, member):
        role = get(ctx.guild.roles, name="Banned from event")
        if not role:
            return await ctx.send("Could not find role, your server may not be setup for Game Events yet. Run ?setup")
        if member == "all":
            for member in role.members:
                await member.remove_roles(role)
                await ctx.send(f"Unbanned {str(member)} from events")
        else:
            try:
                member = ctx.message.mentions[0]
                if role in member.roles:
                    await member.remove_roles(role)
                    await ctx.send(f"Unbanned {str(member)} from events")
                else:
                    await ctx.send("That user is not banned")
            except IndexError:
                await ctx.send("Invalid user")


@bot.command()
@commands.bot_has_guild_permissions(manage_roles=True, manage_messages=True)
@commands.has_guild_permissions(manage_roles=True, manage_messages=True)
async def createteams(ctx):
        for team in teams:
            role = get(ctx.guild.roles, name=team)
            if not role:
                return await ctx.send("Could not find the team roles, your server may not be setup for Game Events yet. Run ?setup")
        await ctx.message.delete()
        msg = await ctx.send("React to get into your teams")
        for emoji in emojis:
            await msg.add_reaction(emoji)


@bot.command()
@commands.bot_has_guild_permissions(manage_roles=True)
@commands.has_guild_permissions(manage_roles=True)
async def clearteam(ctx, team : discord.Role):
    if team.name in teams:
        role = get(ctx.guild.roles, name=team)
        if not role:
            return await ctx.send("Could not find team roles, your server may not be setup for Game Events yet. Run ?setup")
        for member in role.members:
            await member.remove_roles(role)
            await ctx.send(f"Cleared {str(role)}")
    else:
        await ctx.send("Invalid team")


@bot.command()
@commands.bot_has_guild_permissions(manage_roles=True)
@commands.has_guild_permissions(manage_roles=True)
async def clearteams(ctx):
        for team in teams:
            role = get(ctx.guild.roles, name=team)
            if not role:
                return await ctx.send("Could not find voice channel, your server may not be setup for Game Events yet. Run ?setup")
            for member in role.members:
                await member.remove_roles(role)
        await ctx.send("Cleared all teams")


@bot.command()
@commands.bot_has_guild_permissions(manage_channels=True, manage_roles=True)
@commands.has_guild_permissions(manage_channels=True, manage_roles=True)
async def setup(ctx):
            await ctx.send("Alright lets get started setting up your server! What game are you going to be playing on your server?")
            def check(m):
                return m.channel == ctx.channel and m.author == ctx.author
            msg = await bot.wait_for('message', check=check)
            await ctx.send(f"Setting up your server for {msg.content} Events")
            category = await ctx.guild.create_category(msg.content + " Events")
            announcement = await ctx.guild.create_text_channel(f"{msg.content}-announcement", overwrites=None, category=category)
            rules = await ctx.guild.create_text_channel(f"{msg.content}-rules", overwrites=None, category=category)
            logs = await ctx.guild.create_text_channel(f"{msg.content}-bot-logs", overwrites=None, category=category)
            await announcement.set_permissions(ctx.guild.default_role, send_messages=False)
            await rules.set_permissions(ctx.guild.default_role, send_messages=False)
            await logs.set_permissions(ctx.guild.default_role, send_messages=False)
            lounge = await ctx.guild.create_text_channel(f"{msg.content}-lounge", overwrites=None, category=category)
            banned = await ctx.guild.create_role(name="Banned from event")
            perms = lounge.overwrites_for(banned)
            perms.send_messages = False
            await lounge.set_permissions(banned, overwrite=perms)
            channel1 = await ctx.guild.create_voice_channel(f"{msg.content} Events", overwrites=None, category=category)
            perms = channel1.overwrites_for(banned)
            perms.connect = False
            await channel1.set_permissions(banned, overwrite=perms)
            perms1 = channel1.overwrites_for(ctx.guild.default_role)
            perms1.connect = True
            await channel1.set_permissions(ctx.guild.default_role, overwrite=perms1)
            for team in teams:
                role = await ctx.guild.create_role(name=team)
                channel = await ctx.guild.create_voice_channel(team, overwrites=None, category=category, user_limit=2)
                perms = channel.overwrites_for(role)
                perms.connect = True
                await channel.set_permissions(role, overwrite=perms)
                perms = channel.overwrites_for(ctx.guild.default_role)
                perms.connect = False
                await channel.set_permissions(ctx.guild.default_role, overwrite=perms)
            await ctx.send("Your server is setup! \nIMPORTANT: DO NOT change the name of the voicechannels or the roles that I created it may mess up certain commands. ")


@bot.command()
@commands.bot_has_guild_permissions(manage_messages=True)
@commands.has_guild_permissions(manage_messages=True)
async def closeteams(ctx):
        close = await ctx.send("React to the message I must close")
        def check(reaction, user):
            return user == ctx.author and reaction.message.content == "React to get into your teams"
        reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
        await close.delete()
        await ctx.message.delete()
        await reaction.message.edit(content="Teams are now closed.")


@bot.command()
@commands.bot_has_guild_permissions(manage_channels=True, manage_roles=True)
@commands.has_guild_permissions(manage_channels=True, manage_roles=True)
async def wipe(ctx):
        def check(m):
            return m.channel == ctx.channel and m.author == ctx.author and (m.content == "n" or m.content == "y")
        await ctx.send("Are you sure you want to wipe the server of all event channels? This will delete ALL channels and ALL roles I have created (y/n)")
        response = await bot.wait_for('message', timeout=60, check=check)
        if response.content == "y":
            for category in ctx.guild.categories:
                if "Events" in str(category):
                    for channel in category.channels:
                        await channel.delete()
                    await category.delete()
            for team in teams:
                role = get(ctx.guild.roles, name=team)
                await role.delete()
            role = get(ctx.guild.roles, name="Banned from event")
            await role.delete()
            await ctx.send("Wiped all event channels")
        if response.content == "n":
            await ctx.send("Ok, cancelled the wipe")


@bot.command()
@commands.bot_has_guild_permissions(manage_roles=True)
@commands.has_guild_permissions(manage_roles=True)
async def setteam(ctx, team : discord.Role):
        if team.name in teams:
            role = get(ctx.guild.roles, name=team)
            if role.name in teams:
                for roles in ctx.author.roles:
                    if roles.name in teams:
                        await ctx.author.remove_roles(roles)
                try:
                    for member in ctx.message.mentions:
                        await member.add_roles(role)
                        await ctx.send(f"Added {str(member)} to {str(role)}")
                except IndexError:
                    await ctx.send("That is not a valid user")
        else:
            await ctx.send("Invalid team")


#------------------------------------------------------------------------------MINI-GAMES--------------------------------------------------------------------------------------
@bot.command()
@commands.guild_only()
async def rps(ctx, member):
    if member == "bot":
        await ctx.send("Please choose from `rock`, `paper`, or `scissors`")
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content in moves
        move1 = await bot.wait_for('message', timeout = 60.0, check=check)
        botmove = moves[random.randint(0,2)]
        move2 = await ctx.send(botmove)
    else:
        member = ctx.message.mentions[0]
        await ctx.send(f"{member.mention}! {ctx.author.mention} challenges you to rock paper scissors!")
        await ctx.send(f"{ctx.author.mention} DM me your move")
        dm = await ctx.author.create_dm()
        await dm.send("Please choose from `rock`, `paper`, or `scissors`")
        def check(m):
            return m.author == ctx.author and m.guild == None and m.content in moves
        move1 = await bot.wait_for('message', timeout = 60.0, check=check)
        await ctx.send(f"{member.mention} DM me your move")
        dm = await member.create_dm()
        await dm.send("Please choose from `rock`, `paper`, or `scissors`")
        def check(m):
            return m.author == member and m.guild == None and m.content in moves
        move2 = await bot.wait_for('message', timeout = 60.0, check=check)
    if move1.content == move2.content:
        embedVar = discord.Embed(title=f"{str(move1.author)} and {str(move2.author)} Tie! ", description=f"{move1.content.capitalize()} and {move2.content.capitalize()}", color=0xfbff00)
    if move1.content == "rock" and move2.content == "scissors":
        embedVar = discord.Embed(title=f"{str(move1.author)} beats {str(move2.author)}", description=f"{move1.content.capitalize()} and {move2.content.capitalize()}", color=0x00ff00)
    if move1.content == "scissors" and move2.content == "rock":
        embedVar = discord.Embed(title=f"{str(move2.author)} beats {str(move1.author)}", description=f"{move2.content.capitalize()} and {move1.content.capitalize()}", color=0xff0000)
    if move1.content == "rock" and move2.content == "paper":
        embedVar = discord.Embed(title=f"{str(move2.author)} beats {str(move1.author)}", description=f"{move2.content.capitalize()} and {move1.content.capitalize()}", color=0xff0000)
    if move1.content == "scissors" and move2.content == "paper":
        embedVar = discord.Embed(title=f"{str(move1.author)} beats {str(move2.author)}", description=f"{move1.content.capitalize()} and {move2.content.capitalize()}", color=0x00ff00)
    if move1.content == "paper" and move2.content == "rock":
        embedVar = discord.Embed(title=f"{str(move1.author)} beats {str(move2.author)}", description=f"{move1.content.capitalize()} and {move2.content.capitalize()}", color=0x00ff00)
    if move1.content == "paper" and move2.content == "scissors":
        embedVar = discord.Embed(title=f"{str(move2.author)} beats {str(move1.author)}", description=f"{move2.content.capitalize()} and {move1.content.capitalize()}", color=0xff0000)
    await ctx.send(embed=embedVar)

#-------------------------------------------------------------------------------STATS-----------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------MINECRAFT--------------------------------------------------------------------------------------------
@bot.command(aliases=['mc'])
async def minecraft(ctx, player):
    uuid = MojangAPI.get_uuid(player)
    if not uuid:
        return await ctx.send("That player does not exist")
    info = MojangAPI.get_profile(uuid)
    name_history = MojangAPI.get_name_history(uuid)
    history = ""
    for name in name_history:
        history = f"{history}\n{name['name']}"
    embed=discord.Embed(title=f"{info.name}'s Minecraft Profile", description=f"Stats for {info.name}", color=0xff0000)
    embed.set_thumbnail(url=f"https://mc-heads.net/head/{uuid}")
    embed.set_footer(text="Stats provided using the Mojang APIs \nAvatars and skins from MC Heads")
    embed.add_field(name="Username:", value=info.name, inline=True)
    embed.add_field(name="UUID:", value=info.id, inline=True)
    embed.add_field(name="Past Usernames (From oldest down to latest):", value=history, inline=False)
    await ctx.send(embed=embed)


@bot.command()
async def skin(ctx, player):
    uuid = MojangAPI.get_uuid(player)
    if not uuid:
        return await ctx.send("That player does not exist")
    info = MojangAPI.get_profile(uuid)
    embed=discord.Embed(title=f"{info.name}'s Skin", description=f"Full render of {info.name}'s skin", color=0xff0000)
    embed.set_footer(text="Stats provided using the Mojang API \nAvatars and skins from MC Heads")
    embed.set_image(url=f"https://mc-heads.net/body/{uuid}")
    await ctx.send(embed=embed)


@bot.command()
async def changeprofile(ctx):
    await ctx.send("To sign in and edit your Minecraft account, please DM your login credentials \n**THIS DOES NOT GET SAVED INTO ANY OF THE BOTS FILES**")
    dm = await ctx.author.create_dm()
    await dm.send("Please type your email for your Mojang account")
    def check(m):
        return m.channel == dm and m.author == ctx.author
    user = await bot.wait_for('message', timeout = 60.0, check=check)
    await user.channel.send("Ok thanks! Now can I get your password?")
    password = await bot.wait_for('message', timeout = 60.0, check=check)
    try:
        account = MojangUser(user.content, password.content)
    except LoginError:
        return await user.channel.send("Invalid user or password")
    if account.is_fully_authenticated:
        await user.channel.send(f"Authenticated, security challenges are not required. Let's head back to {ctx.channel.mention}")
    else:
        await user.channel.send("Please fill out the security questions")
        answers = []
        print(account.security_challenges)
        for question in account.security_challenges:
            await ctx.send(question)
            answer = await bot.wait_for('message', timeout = 60.0, check=check)
            answers.append(answers.content)
        try:
            account.answer_security_challenges(answers)
        except SecurityAnswerError:
            return await user.channel.send("A security answer was answered incorrectly.")
    await ctx.send(f"Ok {ctx.author.mention} we've signed into your account")
    def check(m):
        return m.channel == ctx.channel and m.author == ctx.author
    exploring = True
    while exploring:
        await ctx.send("What would you like to change? Choose from: `change name`, `change skin`, or `cancel`")
        msg = await bot.wait_for('message', timeout = 60.0, check=check)
        if msg.content == "cancel":
            await ctx.send("Ok, we've signed out of your account")
            exploring = False
        elif msg.content == "change name":
            await ctx.send("What would you like to change our name to?")
            message = await bot.wait_for('message', timeout = 60.0, check=check)
            await ctx.send(f'Are you sure you would like to change your name to {message.content}? You will not be able to change your name for 30 days after this. (Respond y/n)')
            confirm = await bot.wait_for('message', timeout = 60.0, check=check)
            if confirm.content == "y":
                try:
                    account.profile.change_name(message.content)
                    await ctx.send("Success!!")
                except ForbiddenNameChange:
                    await ctx.send("Sorry, you can only change your name every 30 days")
        elif msg.content == "change skin":
            await ctx.send("How would you like to change your skin? You can `upload`, `copy` from another user, or `reset` to a default skin")
            msg = await bot.wait_for('message', timeout = 60.0, check=check)
            if msg.content == "upload":
                await ctx.send("Great! Please upload an image with the correct dimensions")
                newskin = await bot.wait_for('message', timeout = 60.0, check=check)
                resp = requests.get(newskin.attachments[0].url)
                try:
                    account.profile.skin_upload("slim", image_bytes=resp.content)
                    await ctx.send("Success!!")
                except ValueError:
                    await ctx.send("Error changing your skin. Check that the dimensions are correct, and you are logged in correctly")
            if msg.content == "copy":
                await ctx.send("Ok! Please give me the username of the player whos skin you want to copy!")
                copy = await bot.wait_for('message', timeout = 60.0, check=check)
                uuid = MojangAPI.get_uuid(copy.content)
                if not uuid:
                    await ctx.send("That is not a valid player")
                else:
                    account.profile.skin_copy(uuid)
                    await ctx.send(f"Success!! You are now using {copy.content}'s skin")
            if msg.content == "reset":
                account.profile.skin_reset()
                await ctx.send("Success!")
        else:
            await ctx.send("Invalid response")


@bot.command()
async def hypixel(ctx, player):
    data = requests.get(f"https://api.hypixel.net/player?key={HYPIXEL_KEY}&name={player}").json()
    if not data['player']:
        return await ctx.send(f"{player} has not played Hypixel")
    embed = discord.Embed(title=f"{data['player']['displayname']}'s Hypixel Profile", description=f"Hypixel stats for {data['player']['displayname']}", color=0xff0000)
    embed.set_thumbnail(url=f"https://mc-heads.net/head/{data['player']['uuid']}")
    embed.set_footer(text="Stats provided using the Mojang and Hypixel APIs \nAvatars from MC Heads")
    status = False
    try:
        ts = data['player']['lastLogin']/1000
        d = ((datetime.fromtimestamp(ts)).astimezone(timezone('US/Pacific'))).strftime('%H:%M:%S %m/%d/%Y')
    except KeyError:
        d = "Never"
        status = "Offline"
    try:
        ts = data['player']['lastLogout']/1000
        date_format='%H:%M:%S %m/%d/%Y'
        date = datetime.fromtimestamp(ts)
        date = date.astimezone(timezone('US/Pacific'))
        d1 = date.strftime(date_format)
    except KeyError:
        d1 = "Never"
        status = "Online"
    if not status:
        if data['player']['lastLogout'] < data['player']['lastLogin']:
            status = "Online"
        else:
            status = "Offline"
    try:
        rank = data['player']['rank']
    except KeyError:
        try:
            if (data['player']['monthlyPackageRank'] and data['player']['monthlyPackageRank'] != 'NONE'):
                rank = ("MVP++")
            else:
                rank = (data['player']['newPackageRank'])
        except KeyError:
            try:
                rank = data['player']['newPackageRank']
            except KeyError:
                rank = "No rank"
    rank = rank.replace("_PLUS","+")
    embed.add_field(name="Status:", value=status, inline=True)
    embed.add_field(name="Rank:", value=rank, inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    embed.add_field(name="Last Logged In:", value=(d), inline=True)
    embed.add_field(name="Last Logged Off:", value=(d1), inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    try:
        mostRecentGameType = ((data['player']['mostRecentGameType']).lower()).capitalize()
    except KeyError:
        mostRecentGameType = "None"
    embed.add_field(name="Last Game Played:", value=(mostRecentGameType))
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    try:
        EXP = round(data['player']['networkExp'])
        level = round(1 + (-8750. + (8750**2 + 5000*data['player']['networkExp'])**.5) / 2500)
    except KeyError:
        EXP = "None"
        level = "None"
    try:
        karma = data['player']['karma']
    except KeyError:
        karma = 0
    embed.add_field(name="EXP:", value=EXP, inline=True)
    embed.add_field(name="Level:", value=level, inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    embed.add_field(name="Karma:", value=karma, inline=True)
    friends = requests.get(f"https://api.hypixel.net/friends?key={HYPIXEL_KEY}&uuid={data['player']['uuid']}").json()
    try:
        friends = str(len(friends['records']))
    except KeyError:
        friends = "None"
    embed.add_field(name="Friends:", value=friends, inline=True)
    id = requests.get(f"https://api.hypixel.net/findGuild?key={HYPIXEL_KEY}&byUuid={data['player']['uuid']}").json()
    try:
        guild = requests.get(f"https://api.hypixel.net/guild?key={HYPIXEL_KEY}&id={id['guild']}").json()
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="Guild:", value=guild['guild']['name'], inline=True)
        embed.add_field(name="Guild Members:", value=len(guild['guild']['members']), inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
    except KeyError:
        embed.add_field(name="Guild:", value="None", inline=True)
    await ctx.send(embed=embed)


@bot.command(aliases=['bw'])
async def bedwars(ctx, player, *mode):
    data = requests.get(f"https://api.hypixel.net/player?key={HYPIXEL_KEY}&name={player}").json()
    if not data['player']:
        return await ctx.send(f"{player} has not played Bedwars")
    if len(mode) == 0:
            try:
                level = data['player']['achievements']['bedwars_level']
            except KeyError:
                level = 0
            embed=discord.Embed(title=f"{data['player']['displayname']}'s Hypixel Bedwars Profile", description=f"Bedwars stats for {data['player']['displayname']}", color=0xff0000)
            embed.add_field(name="Coins:", value=checkstat(data, 'Bedwars', "coins"), inline=True)
            embed.add_field(name="EXP:", value=checkstat(data, 'Bedwars', "Experience"), inline=True)
            embed.add_field(name="Level:", value=level, inline=True)
            embed.add_field(name="Games Played:", value=checkstat(data, "Bedwars", "games_played_bedwars"), inline=True)
            embed.add_field(name="Current Winstreak:", value=checkstat(data, "Bedwars", "winstreak"), inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            embed.add_field(name="Wins:", value=checkstat(data, "Bedwars", "wins_bedwars"), inline=True)
            embed.add_field(name="Losses:", value=checkstat(data, "Bedwars", "losses_bedwars"), inline=True)
            embed.add_field(name="W/L Rate:", value=getrate(checkstat(data, "Bedwars", "wins_bedwars"), checkstat(data, "Bedwars", "losses_bedwars")), inline=True)
            embed.add_field(name="Kills:", value=checkstat(data, "Bedwars", "kills_bedwars"), inline=True)
            embed.add_field(name="Deaths:", value=checkstat(data, "Bedwars", "deaths_bedwars"), inline=True)
            embed.add_field(name="K/D Rate:", value=getrate(checkstat(data, "Bedwars", "kills_bedwars"), checkstat(data, "Bedwars", "deaths_bedwars")), inline=True)
            embed.add_field(name="Final Kills:", value=checkstat(data, "Bedwars", "final_kills_bedwars"), inline=True)
            embed.add_field(name="Final Deaths:", value=checkstat(data, "Bedwars", "final_deaths_bedwars"), inline=True)
            embed.add_field(name="Final K/D Rate:", value=getrate(checkstat(data, "Bedwars", "final_kills_bedwars"), checkstat(data, "Bedwars", "final_deaths_bedwars")), inline=True)
            embed.add_field(name="Beds Broken:", value=checkstat(data, "Bedwars", "beds_broken_bedwars"), inline=True)
            embed.add_field(name="Beds Lost:", value=checkstat(data, "Bedwars", "beds_lost_bedwars"), inline=True)
            embed.add_field(name="B/L Rate:", value=getrate(checkstat(data, "Bedwars", "beds_broken_bedwars"), checkstat(data, "Bedwars", "beds_lost_bedwars")), inline=True)
    else:
        if mode[0] in bedwarsModes:
            embed = discord.Embed(title=f"{data['player']['displayname']}'s Hypixel {mode[0].capitalize()} Bedwars Profile", description=f"{mode[0].capitalize()} Bedwars stats for {data['player']['displayname']}", color=0xff0000)
            mode = bedwarsModes[mode[0]]
        else:
            return await ctx.send("Invalid Mode")
        embed.add_field(name="Games Played:", value=checkstat(data, 'Bedwars', f'{mode}_games_played_bedwars'), inline=True)
        embed.add_field(name="Current Winstreak:", value=checkstat(data, 'Bedwars', f"{mode}_winstreak"), inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="Kills:", value=checkstat(data, 'Bedwars', f'{mode}_kills_bedwars'), inline=True)
        embed.add_field(name="Deaths:", value=checkstat(data, 'Bedwars', f'{mode}_deaths_bedwars'), inline=True)
        embed.add_field(name="K/D Rate:", value=getrate(checkstat(data, 'Bedwars', f'{mode}_kills_bedwars'), checkstat(data, 'Bedwars', f'{mode}_deaths_bedwars')), inline=True)
        embed.add_field(name="Final Kills:", value=checkstat(data, 'Bedwars', f'{mode}_final_kills_bedwars'), inline=True)
        embed.add_field(name="Final Deaths:", value=checkstat(data, 'Bedwars', f'{mode}_final_deaths_bedwars'), inline=True)
        embed.add_field(name="Final K/D Rate:", value=getrate(checkstat(data, 'Bedwars', f'{mode}_final_kills_bedwars'), checkstat(data, 'Bedwars', f'{mode}_final_deaths_bedwars')), inline=True)
        embed.add_field(name="Wins:", value=checkstat(data, 'Bedwars', f'{mode}_wins_bedwars'), inline=True)
        embed.add_field(name="Losses:", value=checkstat(data, 'Bedwars', f'{mode}_losses_bedwars'), inline=True)
        embed.add_field(name="W/L Rate", value=getrate(checkstat(data, 'Bedwars', f'{mode}_wins_bedwars'), checkstat(data, 'Bedwars', f'{mode}_losses_bedwars')), inline=True)
    embed.set_thumbnail(url=f"https://mc-heads.net/head/{data['player']['uuid']}")
    embed.set_footer(text="Stats provided using the Mojang and Hypixel APIs \nAvatars from MC Heads")
    await ctx.send(embed=embed)


@bot.command(aliases=["sw"])
async def skywars(ctx, player, *mode):
    data = requests.get(f"https://api.hypixel.net/player?key={HYPIXEL_KEY}&name={player}").json()
    if not data['player']:
        return await ctx.send(f"{player} has not played SkyWars")
    if len(mode) == 0:
        embed=discord.Embed(title=f"{data['player']['displayname']}'s Hypixel Skywars Profile", description=f"Skywars stats for {data['player']['displayname']}", color=0xff0000)
        embed.add_field(name="Coins:", value=checkstat(data, "SkyWars", 'coins'), inline=True)
        embed.add_field(name="EXP:", value=checkstat(data, "SkyWars", 'skywars_experience'), inline=True)
        embed.add_field(name="Level:", value=getSkyWarsLevel(checkstat(data, "SkyWars", 'skywars_experience')), inline=True)
        embed.add_field(name="Games Played:", value=checkstat(data, "SkyWars", 'wins')+checkstat(data, "SkyWars", 'losses'), inline=True)
        embed.add_field(name="Current Winstreak:", value=checkstat(data, "SkyWars", 'win_streak'), inline=True)
        embed.add_field(name="Assists:", value=checkstat(data, "SkyWars", 'assists'), inline=True)
        embed.add_field(name="Kills:", value=checkstat(data, "SkyWars", 'kills'), inline=True)
        embed.add_field(name="Deaths:", value=checkstat(data, "SkyWars", 'deaths'), inline=True)
        embed.add_field(name="K/D Rate:", value=getrate(checkstat(data, "SkyWars", 'kills'), checkstat(data, "SkyWars", 'deaths')), inline=True)
        embed.add_field(name="Wins:", value=checkstat(data, "SkyWars", 'wins'), inline=True)
        embed.add_field(name="Losses:", value=checkstat(data, "SkyWars", 'losses'), inline=True)
        embed.add_field(name="W/L Rate:", value=getrate(checkstat(data, "SkyWars", 'wins'), checkstat(data, "SkyWars", 'losses')), inline=True)
    else:
        joinedmode = ""
        for x in mode:
            joinedmode = f"{joinedmode}{x} "
        joinedmode = joinedmode[:-1]
        if joinedmode == "solos normal":
            embed = discord.Embed(title=f"{data['player']['displayname']}'s Hypixel Solos Normal Skywars Profile", description=f"Solo Normal Skywars stats for {data['player']['displayname']}", color=0xff0000)
            embed.add_field(name="EXP:", value=checkstat(data, "SkyWars", 'skywars_experience'), inline=True)
            embed.add_field(name="Level:", value=getSkyWarsLevel(checkstat(data, "SkyWars", 'skywars_experience')), inline=True)
            embed.add_field(name="Games Played:", value=(checkstat(data, "SkyWars", 'wins_solo')-checkstat(data, "SkyWars", 'wins_solo_insane'))+(checkstat(data, "SkyWars", 'losses_solo')-checkstat(data, "SkyWars", 'losses_solo_insane')), inline=True)
            embed.add_field(name="Kills:", value=checkstat(data, "SkyWars", 'kills_solo')-checkstat(data, "SkyWars", 'kills_solo_insane'), inline=True)
            embed.add_field(name="Deaths:", value=checkstat(data, "SkyWars", 'deaths_solo')-checkstat(data, "SkyWars", 'deaths_solo_insane'), inline=True)
            embed.add_field(name="K/D Rate:", value=getrate(checkstat(data, "SkyWars", 'kills_solo')-checkstat(data, "SkyWars", 'kills_solo_insane'), checkstat(data, "SkyWars", 'deaths_solo')-checkstat(data, "SkyWars", 'deaths_solo_insane')), inline=True)
            embed.add_field(name="Wins:", value=checkstat(data, "SkyWars", 'wins_solo')-checkstat(data, "SkyWars", 'wins_solo_insane'), inline=True)
            embed.add_field(name="Losses:", value=checkstat(data, "SkyWars", 'losses_solo')-checkstat(data, "SkyWars", 'losses_solo_insane'), inline=True)
            embed.add_field(name="W/L Rate:", value=getrate((checkstat(data, "SkyWars", 'wins_solo')-checkstat(data, "SkyWars", 'wins_solo_insane')), checkstat(data, "SkyWars", 'losses_solo')-checkstat(data, "SkyWars", 'losses_solo_insane')), inline=True)
        elif joinedmode == "solos insane":
            embed = discord.Embed(title=f"{data['player']['displayname']}'s Hypixel Solos Insane Skywars Profile", description=f"Solo Insane Skywars stats for {data['player']['displayname']}", color=0xff0000)
            embed.add_field(name="EXP:", value=checkstat(data, "SkyWars", 'skywars_experience'), inline=True)
            embed.add_field(name="Level:", value=getSkyWarsLevel(checkstat(data, "SkyWars", 'skywars_experience')), inline=True)
            embed.add_field(name="Games Played:", value=checkstat(data, "SkyWars", 'wins_solo_insane')+checkstat(data, "SkyWars", 'losses_solo_insane'), inline=True)
            embed.add_field(name="Kills:", value=checkstat(data, "SkyWars", 'kills_solo_insane'), inline=True)
            embed.add_field(name="Deaths:", value=checkstat(data, "SkyWars", 'deaths_solo_insane'), inline=True)
            embed.add_field(name="K/D Rate:", value=getrate(checkstat(data, "SkyWars", 'kills_solo_insane'), checkstat(data, "SkyWars", 'deaths_solo_insane')), inline=True)
            embed.add_field(name="Wins:", value=checkstat(data, "SkyWars", 'wins_solo_insane'), inline=True)
            embed.add_field(name="Losses:", value=checkstat(data, "SkyWars", 'losses_solo_insane'), inline=True)
            embed.add_field(name="W/L Rate:", value=getrate(checkstat(data, "SkyWars", 'wins_solo_insane'), checkstat(data, "SkyWars", 'losses_solo_insane')), inline=True)
        elif joinedmode == "teams normal":
            embed = discord.Embed(title=f"{data['player']['displayname']}'s Hypixel Teams Normal Skywars Profile", description=f"Teams Normal Skywars stats for {data['player']['displayname']}", color=0xff0000)
            embed.add_field(name="EXP:", value=checkstat(data, "SkyWars", 'skywars_experience'), inline=True)
            embed.add_field(name="Level:", value=getSkyWarsLevel(checkstat(data, "SkyWars", 'skywars_experience')), inline=True)
            embed.add_field(name="Games Played:", value=(checkstat(data, "SkyWars", 'wins_teams')-checkstat(data, "SkyWars", 'wins_teams_insane'))+(checkstat(data, "SkyWars", 'losses_teams')-checkstat(data, "SkyWars", 'losses_teams_insane')), inline=True)
            embed.add_field(name="Kills:", value=checkstat(data, "SkyWars", 'kills_teams')-checkstat(data, "SkyWars", 'kills_teams_insane'), inline=True)
            embed.add_field(name="Deaths:", value=checkstat(data, "SkyWars", 'deaths_teams')-checkstat(data, "SkyWars", 'deaths_teams_insane'), inline=True)
            embed.add_field(name="K/D Rate:", value=getrate(checkstat(data, "SkyWars", 'kills_teams')-checkstat(data, "SkyWars", 'kills_teams_insane'), checkstat(data, "SkyWars", 'deaths_teams')-checkstat(data, "SkyWars", 'deaths_teams_insane')), inline=True)
            embed.add_field(name="Wins:", value=checkstat(data, "SkyWars", 'wins_teams')-checkstat(data, "SkyWars", 'wins_teams_insane'), inline=True)
            embed.add_field(name="Losses:", value=checkstat(data, "SkyWars", 'losses_teams')-checkstat(data, "SkyWars", 'losses_teams_insane'), inline=True)
            embed.add_field(name="W/L Rate:", value=getrate((checkstat(data, "SkyWars", 'wins_teams')-checkstat(data, "SkyWars", 'wins_teams_insane')), checkstat(data, "SkyWars", 'losses_teams')-checkstat(data, "SkyWars", 'losses_teams_insane')), inline=True)
        elif joinedmode == "teams insane":
            embed = discord.Embed(title=f"{data['player']['displayname']}'s Hypixel Teams Insane Skywars Profile", description=f"Teams Insane Skywars stats for {data['player']['displayname']}", color=0xff0000)
            embed.add_field(name="EXP:", value=checkstat(data, "SkyWars", 'skywars_experience'), inline=True)
            embed.add_field(name="Level:", value=getSkyWarsLevel(checkstat(data, "SkyWars", 'skywars_experience')), inline=True)
            embed.add_field(name="Games Played:", value=checkstat(data, "SkyWars", 'wins_teams_insane')+checkstat(data, "SkyWars", 'losses_teams_insane'), inline=True)
            embed.add_field(name="Kills:", value=checkstat(data, "SkyWars", 'kills_teams_insane'), inline=True)
            embed.add_field(name="Deaths:", value=checkstat(data, "SkyWars", 'deaths_teams_insane'), inline=True)
            embed.add_field(name="K/D Rate:", value=getrate(checkstat(data, "SkyWars", 'kills_teams_insane'), checkstat(data, "SkyWars", 'deaths_teams_insane')), inline=True)
            embed.add_field(name="Wins:", value=checkstat(data, "SkyWars", 'wins_teams_insane'), inline=True)
            embed.add_field(name="Losses:", value=checkstat(data, "SkyWars", 'losses_teams_insane'), inline=True)
            embed.add_field(name="W/L Rate:", value=getrate(checkstat(data, "SkyWars", 'wins_teams_insane'), checkstat(data, "SkyWars", 'losses_teams_insane')), inline=True)
        else:
            return await ctx.send("Invalid mode")
    embed.set_thumbnail(url=f"https://mc-heads.net/head/{data['player']['uuid']}")
    embed.set_footer(text="Stats provided using the Mojang and Hypixel APIs \nAvatars from MC Heads")
    await ctx.send(embed=embed)


@bot.command()
async def duels(ctx, player, *mode):
    data = requests.get(f"https://api.hypixel.net/player?key={HYPIXEL_KEY}&name={player}").json()
    if not data['player']:
        return await ctx.send(f"{player} has not played Duels")
    if len(mode) == 0:
        embed=discord.Embed(title=f"{data['player']['displayname']}'s Hypixel Duels Profile", description=f"Duels stats for {data['player']['displayname']}", color=0xff0000)
        embed.add_field(name="Games Played:", value=checkstat(data, "Duels", 'wins')+checkstat(data, "Duels", 'losses'), inline=True)
        embed.add_field(name="Winstreak:", value=checkstat(data, "Duels", 'current_winstreak'), inline=True)
        embed.add_field(name="Best Winstreak:", value=checkstat(data, "Duels", 'best_overall_winstreak'), inline=True)
        embed.add_field(name="Coins:", value=checkstat(data, "Duels", 'coins'), inline=False)
        embed.add_field(name="Kills:", value=checkstat(data, "Duels", 'kills'), inline=True)
        embed.add_field(name="Deaths:", value=checkstat(data, "Duels", 'deaths'), inline=True)
        embed.add_field(name="K/D Rate:", value=getrate(checkstat(data, "Duels", 'kills'), checkstat(data, "Duels", 'deaths')), inline=True)
        embed.add_field(name="Wins:", value=checkstat(data, "Duels", 'wins'), inline=True)
        embed.add_field(name="Losses:", value=checkstat(data, "Duels", 'losses'), inline=True)
        embed.add_field(name="W/L Rate:", value=getrate(checkstat(data, "Duels", 'wins'), checkstat(data, "Duels", 'losses')), inline=True)
        embed.add_field(name="Arrows Shot:", value=checkstat(data, "Duels", 'bow_shots'), inline=True)
        embed.add_field(name="Arrows Hit:", value=checkstat(data, "Duels", 'bow_hits'), inline=True)
        embed.add_field(name="Arrows Missed:", value=checkstat(data, "Duels", 'bow_shots')-checkstat(data, "Duels", 'bow_hits'), inline=True)
        embed.add_field(name="Arrow H/S Rate:", value=getrate(checkstat(data, "Duels", 'bow_hits'), checkstat(data, "Duels", 'bow_shots')), inline=False)
        embed.add_field(name="Melee Swings:", value=checkstat(data, "Duels", 'melee_swings'), inline=True)
        embed.add_field(name="Melee Hits:", value=checkstat(data, "Duels", 'melee_hits'), inline=True)
        embed.add_field(name="Melee Missed:", value=checkstat(data, "Duels", 'melee_swings')-checkstat(data, "Duels", 'melee_hits'), inline=True)
        embed.add_field(name="Melee H/S Rate:", value=getrate(checkstat(data, "Duels", 'melee_hits'), checkstat(data, "Duels", 'melee_swings')), inline=True)
    else:
        joinedmode = ""
        for x in mode:
            joinedmode = f"{joinedmode}{x} "
        mode = (joinedmode[:-1]).lower()
        if not mode in modes:
            return await ctx.send("Invalid mode")
        embed=discord.Embed(title=f"{data['player']['displayname']}'s Hypixel {mode.capitalize()} Duel Profile", description=f"{mode.capitalize()} duel stats for {data['player']['displayname']}", color=0xff0000)
        try:
            if data['player']['stats']['Duels'][f'godlike_{mode.split()[0]}']:
                prestige = "Godlike"
        except KeyError:
            try:
                prestige = f"Grandmaster {write_roman(data['player']['stats']['Duels'][f'{mode.split()[0]}_grandmaster_title_prestige'])}"
            except KeyError:
                try:
                    prestige = f"Legend {write_roman(data['player']['stats']['Duels'][f'{mode.split()[0]}_legend_title_prestige'])}"
                except KeyError:
                    try:
                        prestige = f"Master {write_roman(data['player']['stats']['Duels'][f'{mode.split()[0]}_master_title_prestige'])}"
                    except KeyError:
                        try:
                            prestige = f"Diamond {write_roman(data['player']['stats']['Duels'][f'{mode.split()[0]}_diamond_title_prestige'])}"
                        except KeyError:
                            try:
                                prestige = f"Gold {write_roman(data['player']['stats']['Duels'][f'{mode.split()[0]}_gold_title_prestige'])}"
                            except KeyError:
                                try:
                                    prestige = f"Iron {write_roman(data['player']['stats']['Duels'][f'{mode.split()[0]}_iron_title_prestige'])}"
                                except KeyError:
                                    if data['player']['stats']['Duels'][f'{mode.split()[0]}_rookie_title_prestige'] > 1:
                                        prestige = f"Rookie {write_roman(data['player']['stats']['Duels'][f'{mode.split()[0]}_rookie_title_prestige'])}"
                                    else:
                                        prestige = "None"
        mode = modes[mode]
        embed.add_field(name="Prestige", value=prestige, inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="Kills:", value=checkstat(data, "Duels", f'{mode}_kills'), inline=True)
        embed.add_field(name="Deaths:", value=checkstat(data, "Duels", f'{mode}_deaths'), inline=True)
        embed.add_field(name="K/D Rate:", value=getrate(checkstat(data, "Duels", f'{mode}_kills'), checkstat(data, "Duels", f'{mode}_deaths')), inline=True)
        if mode == "bridge":
            mode = "bridge_duel"
        embed.add_field(name="Wins:", value=checkstat(data, "Duels", f'{mode}_wins'), inline=True)
        embed.add_field(name="Losses:", value=checkstat(data, "Duels", f'{mode}_losses'), inline=True)
        embed.add_field(name="W/L Rate:", value=getrate(checkstat(data, "Duels", f'{mode}_wins'), checkstat(data, "Duels", f'{mode}_losses')), inline=True)
    embed.set_thumbnail(url=f"https://mc-heads.net/head/{data['player']['uuid']}")
    embed.set_footer(text="Stats provided using the Mojang and Hypixel APIs \nAvatars from MC Heads")
    await ctx.send(embed=embed)


@bot.command(aliases=["sb"])
async def skyblock(ctx, player):
    if ctx.author.id != botmaster:
        return await ctx.send("This command is not ready yet. Sorry :(")
    data = requests.get(f"https://api.hypixel.net/player?key={HYPIXEL_KEY}&name={player}").json()
    if not data['player']:
        return await ctx.send("That player does not exist")
    profiles = data['player']['stats']['SkyBlock']['profiles']
    message = ""
    for profile in profiles:
        message = f"{message}\n{profiles[profile]['cute_name']}"
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content in profiles
    await ctx.send("Which profile would you like stats for?")
    await ctx.send(message)
    response = await bot.wait_for('message', timeout=120, check=check)
    await ctx.send(f"Stats for {response.content}")
    #sbData = requests.get("https://api.slothpixel.me/api/skyblock/profiles/princeoftoxicity").json()
    #sbData = sbData['members'][data['player']['uuid']]
    #skill average (convert to level/total skill)
    #display all skills
    #catacombs level
    #class levels
    #coins
    #equipped armor
    #await ctx.send(embed=embed)


@bot.command()
async def fortnite(ctx, player):
    data = requests.get(f"https://fortnite-api.com/v1/stats/br/v2?name={player}").json()
    if data['status'] == 404:
        return await ctx.send("Invalid player")
    else:
        embed = discord.Embed(title=f"Fortnite stats for {data['data']['account']['name']}", description=None, color=0xff0000)
        embed.add_field(name="Username:", value=data['data']['account']['name'], inline=False)
        embed.add_field(name="ID:", value=data['data']['account']['id'], inline=False)
        embed.add_field(name="BattlePass Level:", value=data['data']['battlePass']['level'], inline=False)
        embed.add_field(name="BattlePass Progress:", value=data['data']['battlePass']['progress'], inline=False)
        embed.add_field(name="Score", value=data['data']['stats']['all']['overall']['score'], inline=False)
        embed.add_field(name="Overall Kills:", value=data['data']['stats']['all']['overall']['kills'], inline=False)
        embed.add_field(name="Overall Deaths", value=data['data']['stats']['all']['overall']['deaths'], inline=False)
        embed.add_field(name="Overall K/D Rate", value=data['data']['stats']['all']['overall']['kd'], inline=False)
        embed.add_field(name="Overall Games Played", value=data['data']['stats']['all']['overall']['matches'], inline=False)
        embed.add_field(name="Overall Wins", value=data['data']['stats']['all']['overall']['wins'], inline=False)
        embed.add_field(name="Overall Losses", value=data['data']['stats']['all']['overall']['deaths'], inline=False)
        embed.add_field(name="Overall W/L Rate", value=round(data['data']['stats']['all']['overall']['wins']/data['data']['stats']['all']['overall']['deaths'], 2), inline=False)
        embed.set_footer(text="Stats provided using the unofficial Fortnite-API")
        embed.set_thumbnail(url="https://logodix.com/logo/45400.jpg")
        await ctx.send(embed=embed)


@bot.command()
async def twitch(ctx, channel):
    user = requests.get(f"https://api.twitch.tv/helix/users?login={channel}", headers={"client-id":f"{TWITCH_CLIENT_ID}", "Authorization":f"{TWITCH_AUTH}"}).json()
    if not user['data']:
        return await ctx.send("Invalid channel")
    try:
        data = (user['data'])[0]
        embed = discord.Embed(title=f"{data['display_name']}'s' Twitch Stats", description=f"https://twitch.tv/{channel}", color=0xff0000)
        embed.set_thumbnail(url=data['profile_image_url'])
        embed.add_field(name="Username:", value=data['display_name'], inline=True)
        embed.add_field(name="Login Name:", value=data['login'], inline=True)
        embed.add_field(name="ID", value=data['id'], inline=True)
        embed.add_field(name="Channel Type", value=data['broadcaster_type'].capitalize(), inline=False)
        embed.add_field(name="Channel Description", value=data['description'], inline=False)
        embed.add_field(name="Views", value=data['view_count'], inline=True)
        followers = requests.get(f"https://api.twitch.tv/helix/users/follows?to_id={data['id']}", headers={"client-id":f"{TWITCH_CLIENT_ID}", "Authorization":f"{TWITCH_AUTH}"}).json()
        embed.add_field(name="Followers", value=followers['total'], inline=True)
        stream = requests.get(f"https://api.twitch.tv/helix/search/channels?query={channel}/", headers={"client-id":f"{TWITCH_CLIENT_ID}", "Authorization":f"{TWITCH_AUTH}"}).json()
        for x in stream['data']:
            is_live = x['is_live']
            break
        if is_live:
            status = "Live"
            embed.set_thumbnail(url=x['thumbnail_url'])
        if not is_live:
            status = "Not Live"
        embed.add_field(name="Status:", value=status, inline=True)
        if status == "Live":
            embed.add_field(name="Stream:", value=x['title'], inline=True)
        await ctx.send(embed=embed)
    except discord.errors.HTTPException:
        await ctx.send("Channel has not streamed")


@bot.command(aliases=['yt'])
async def youtube(ctx, *channelarg):
    if len(channelarg) == 0:
        return await ctx.send("Invalid channel")
    channel = ""
    for x in channelarg:
        channel = f"{channel} {x}"
    channel = channel.replace(" ", "%20")
    channel = channel[3:]
    data = requests.get(f"https://youtube.googleapis.com/youtube/v3/search?part=snippet&q={channel}&type=channel&key={YT_KEY}").json()
    if not data['items']:
        return await ctx.send("Invalid channel")
    channel_id = ((data['items'])[0]['snippet']['channelId'])
    stats = requests.get(f"https://www.googleapis.com/youtube/v3/channels?part=statistics&id={channel_id}&key={YT_KEY}").json()
    embed = discord.Embed(title=f"YouTube statistics for {data['items'][0]['snippet']['title']}", description=f"https://www.youtube.com/channel/{channel_id}", color=0xff0000)
    embed.add_field(name="Channel Name:", value=data['items'][0]['snippet']['title'], inline=True)
    embed.add_field(name="Channel ID:", value=channel_id, inline=True)
    embed.add_field(name="Channel Description:", value=(data['items'][0]['snippet'])['description'], inline=False)
    embed.add_field(name="Views:", value=stats['items'][0]['statistics']['viewCount'], inline=True)
    embed.add_field(name="Subscribers:", value=stats['items'][0]['statistics']['subscriberCount'], inline=True)
    embed.add_field(name="Videos:", value=stats['items'][0]['statistics']['videoCount'], inline=True)
    embed.set_thumbnail(url=(data['items'][0])['snippet']['thumbnails']['default']['url'])
    embed.set_footer(text=f"Stats provided by the YouTube API \nNot the Youtuber your looking for? Type 'see more' to see more {channelarg}s and then run '?youtube (id_of_the_channel_you_want)'")
    try:
        await ctx.send(embed=embed)
    except discord.HTTPException:
        return await ctx.send(f"{data['items'][0]['snippet']['title']} has no videos")
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content == "see more"
    try:
        seemore = await bot.wait_for('message', timeout=30, check=check)
    except asyncio.TimeoutError:
        pass
    for item in data['items']:
        if item != data['items'][0]:
            try:
                embed = discord.Embed(title=f"YouTube statistics for {item['snippet']['title']}", description=f"https://www.youtube.com/channel/{item['snippet']['channelId']}", color=0xff0000)
                embed.add_field(name="Name:", value=item['snippet']['title'], inline=True)
                embed.add_field(name="ID:", value=item['snippet']['channelId'], inline=True)
                embed.add_field(name="Description:", value=item['snippet']['description'], inline=True)
                embed.set_thumbnail(url=item['snippet']['thumbnails']['default']['url'])
                await ctx.send(embed=embed)
            except discord.HTTPException:
                pass


bot.run(os.environ.get("TOKEN"))
