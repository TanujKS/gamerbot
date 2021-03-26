#-----------------------------------------------------------------------INITIALIZATIONS----------------------------------------------------------------------
import discord
from discord.ext import commands
from discord.utils import get

from discord import FFmpegPCMAudio
from discord import opus
import gtts
from gtts import gTTS
import ffmpeg

import decouple
from decouple import config
import redis

import os
import sys

import random
import requests
import asyncio
from collections import OrderedDict
import json
import ast
import math

import time
import datetime
from datetime import datetime
from pytz import timezone, utc

from mojang import MojangAPI
from mojang import MojangUser
from mojang.exceptions import SecurityAnswerError
from mojang.exceptions import LoginError

from PIL import Image
from io import BytesIO

from googletrans import Translator
from googletrans.constants import LANGUAGES

from PyDictionary import PyDictionary


keys = ['HYPIXEL_KEY', 'TWITCH_CLIENT_ID', 'YT_KEY', 'TWITCH_AUTH', 'TOKEN', 'REDIS_URL', 'TRN_API_KEY', 'ALT_TOKEN', 'STATUS_WEBHOOK']
for k in keys:
    globals()[k] = os.environ.get(k)
    if globals()[k] is None:
        try:
            globals()[k] = config(k)
        except decouple.UndefinedValueError:
            raise Exception(f"Could not initialise key: {k}")

r = redis.from_url(REDIS_URL)

shutDown = r.get("shutdown")
if shutDown == "True":
    raise Exception("Shutting down")


emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣"]
teams = ["Team 1", "Team 2", "Team 3", "Team 4", "Team 5", "Team 6", "Team 7", "Team 8"]
stopWatches = {}
translator = Translator()
dictionary = PyDictionary()


blackListed = r.lrange("blacklisted", 0, -1)
for i in range(0, len(blackListed)):
    blackListed[i] = blackListed[i].decode("utf-8")


rval = r.get("guildInfo")
tempGuildInfo = json.loads(rval)
guildInfo = {}

for g in tempGuildInfo:
    guildInfo[int(g)] = tempGuildInfo[g]


rval = r.get("trackingGuilds")
tempTrackingGuilds = json.loads(rval)
trackingGuilds = {}

for t in tempTrackingGuilds:
    trackingGuilds[int(t)] = tempTrackingGuilds[t]
    for u in trackingGuilds[int(t)]:
        index = trackingGuilds[int(t)].index(u)
        trackingGuilds[int(t)][index]['channel-id'] = int(trackingGuilds[int(t)][index]['channel-id'])


rval = r.get("csgoLinks")
tempCsgoLinks = json.loads(rval)
csgoLinks = {}

for c in tempCsgoLinks:
    csgoLinks[int(c)] = int(tempCsgoLinks[c])


def multi_key_dict_get(d : dict, k):
    for keys, v in d.items():
        if k in keys:
            return v
    return None


def convertBooltoStr(bool : bool):
    if bool is True:
        return "On"
    if bool is False:
        return "Off"


def convertBooltoExpress(bool : bool):
    if bool:
        return "Yes"
    if not bool:
        return "No"


defaultPrefix = '?'

def initGuild(guild : discord.Guild):
    print(f"Initialsed {guild.name}")
    guildInfo[guild.id] = {}
    guildInfo[guild.id]['antiez'] = False
    guildInfo[guild.id]['teamLimit'] = 2
    guildInfo[guild.id]['maximumTeams'] = 1
    guildInfo[guild.id]['TTVCrole'] = "TTVC"
    guildInfo[guild.id]['prefix'] = defaultPrefix
    rval = json.dumps(guildInfo)
    r.set("guildInfo", rval)

def determine_prefix(bot, message):
    guild = message.guild
    if guild:
        return guildInfo[guild.id].get('prefix')
    else:
        return defaultPrefix

ownerID = 816440833250689034

async def is_owner(ctx):
    return ctx.author.id == ownerID


#----------------------------------------------------------------------------BOT-----------------------------------------------------------------------------
bot = commands.Bot(command_prefix=determine_prefix, intents=discord.Intents.all(), case_insensitive=True)
bot.remove_command('help')
#---------------------------------------------------------------------------EVENTS---------------------------------------------------------------------------
@bot.event
async def on_ready():
    print(f"Bot connected with {bot.user} \nID:{bot.user.id}")
    if len(sys.argv) >= 3:
        if sys.argv[2] == "owner":
            bot.add_check(is_owner)
            print("In owner mode")

    game = discord.Game(f"on {len(bot.guilds)} servers. Use @{str(bot.user)} to see what I can do!")

    await bot.change_presence(activity=game)

    await bot.change_presence(status=discord.Status.online, activity=game)

    global reports
    global statusPings
    global statusChannel

    supportServer = bot.get_guild(763824152493686795)

    reports = get(supportServer.channels, name="reports")
    statusChannel = get(supportServer.channels, name="bot-status")
    statusPings = get(supportServer.roles, name="Status Pings")
    r.set("statusPingsMention", statusPings.mention)

    global botmaster
    botmaster = bot.get_user(ownerID)

    for guild in bot.guilds:
        if not trackingGuilds.get(guild.id):
            trackingGuilds[guild.id] = []
        if not guildInfo.get(guild.id):
            initGuild(guild)

    rval = json.dumps(guildInfo)
    r.set("guildInfo", rval)

    disabledCommands = ['twitchtrack', 'twitchtracklist', 'deltrack']

    for disabled in disabledCommands:
        command = get(bot.commands, name=disabled)
        if not command:
            raise Exception("Invalid command", disabled)
        command.update(enabled=False)

    #await bot.loop.create_task(checkIfLive())


async def sendStatusMessage(bot, statusMessage):
    if bot.user.name == "GamerBot":
        mention = r.get("statusPingsMention").decode('utf-8')

        data = {"content": f"{str(bot.user)} is now **{statusMessage}** \n{mention}", "username": "GamerBot Status", "avatar_url": f"{str(bot.user.avatar_url)}"}

        result = requests.post(STATUS_WEBHOOK, data=json.dumps(data), headers={"Content-Type": "application/json"})

        try:
            result.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(f"ERROR: {err}")


@bot.event
async def on_connect():
    await sendStatusMessage(bot, "Online")


@bot.event
async def on_disconnect():
    await sendStatusMessage(bot, "Offline")


@bot.event
async def on_guild_join(guild):
    print(f"Joined {guild}")
    game = discord.Game(f"on {len(bot.guilds)} servers. Use @{bot.user} to see what I can do!")
    await bot.change_presence(activity=game)

    try:
        trackingGuilds[guild.id]
    except KeyError:
        trackingGuilds[guild.id] = []
    try:
        guildInfo[guild.id]
    except KeyError:
        initGuild(guild)
    rval = json.dumps(trackingGuilds)
    r.set("trackingGuilds", rval)
    await reports.send(f"Joined {guild.name} with {guild.member_count} members")


@bot.event
async def on_guild_remove(guild):
    print(f"Left {guild}")
    game = discord.Game(f"on {len(bot.guilds)} servers. Use @{str(bot.user)} to check my prefix")
    await bot.change_presence(activity=game)

    await reports.send(f"Left {guild.name} with {guild.member_count} members")

    try:
        dm = await guild.owner.create_dm()
        def check(m):
            return m.author == dm.recipient and m.channel == dm
        await dm.send(f"Hello {str(guild.owner)}. I see you have removed GamerBot from your server. As GamerBot is a new bot and is still in development it would be great to get your feedback on how the bot is/why you removed it. Would you be willing to answer a few questions? (y/n)")
        response = await bot.wait_for('message', timeout=120, check=check)
        if response.content == "y":
            await dm.send("Thank you! First, why are you removing GamerBot from your server?")
            response = await bot.wait_for('message', timeout=120, check=check)
            await reports.send(f"Reason for removal: {response.content}")

            await dm.send("Got it, on a scale of 1-10 how would you rate GamerBot's features, response time, ease of use, etc")
            response = await bot.wait_for('message', timeout=120, check=check)
            await reports.send(f"Rating: {response.content}")

            await dm.send("Thanks! Any other comments/feedback?")
            response = await bot.wait_for('message', timeout=120, check=check)
            await reports.send(f"Feedback: {response.content}")
            await dm.send(f"Thank you. Your feedback helps us make {bot.user.name} a better bot.")
        else:
            await dm.send("No problem. Goodbye!")
    except Exception as e:
        await reports.send(f"Could not DM {str(guild.owner)} Exception: {e}")


ezmessages = ["Wait... This isn't what I typed!", "Anyone else really like Rick Astley?", "Hey helper, how play game?", "Sometimes I sing soppy, love songs in the car.", "I like long walks on the beach and playing Hypixel", "Please go easy on me, this is my first game!", "You're a great person! Do you want to play some Hypixel games with me?", "In my free time I like to watch cat videos on Youtube", "When I saw the witch with the potion, I knew there was trouble brewing.", "If the Minecraft world is infinite, how is the sun spinning around it?", "Hello everyone! I am an innocent player who loves everything Hypixel.", "Plz give me doggo memes!", "I heard you like Minecraft, so I built a computer in Minecraft in your Minecraft so you can Minecraft while you Minecraft", "Why can't the Ender Dragon read a book? Because he always starts at the End.", "Maybe we can have a rematch?", "I sometimes try to say bad things then this happens :(", "Behold, the great and powerful, my magnificent and almighty nemisis!", "Doin a bamboozle fren.", "Your clicks per second are godly.", "What happens if I add chocolate milk to macaroni and cheese?", "Can you paint with all the colors of the wind", "Blue is greener than purple for sure", "I had something to say, then I forgot it.", "When nothing is right, go left.", "I need help, teach me how to play!", "Your personality shines brighter than the sun.", "You are very good at the game friend.", "I like pineapple on my pizza", "I like pasta, do you prefer nachos?", "I like Minecraft pvp but you are truly better than me!", "I have really enjoyed playing with you! <3", "ILY <3", "Pineapple doesn't go on pizza!", "Lets be friends instead of fighting okay?"]

@bot.event
async def on_message(message):
    if not message.author.bot:

        if not message.author.id in blackListed:
            await bot.process_commands(message)

        messageList = message.content.lower().split()

        if message.mentions and len(messageList) == 1:
            if message.mentions[0] == message.guild.me:
                try:
                    await message.channel.send(f"My prefix in this server is `{determine_prefix(bot, message)}`")
                except discord.errors.Forbidden:
                    pass

        if message.guild:

            if ("ez" in messageList or "kys" in messageList) and guildInfo[message.guild.id]['antiez']:
                webhooks = await message.channel.webhooks()
                webhook = get(webhooks, name="ezbot")
                if not webhook:
                    webhook = await message.channel.create_webhook(name="ezbot")
                if message.author.nick:
                    username = message.author.nick
                else:
                    username = message.author.name
                await webhook.send(ezmessages[random.randint(0, len(ezmessages))-1], username=username, avatar_url=message.author.avatar_url)
                await message.delete()


raiseErrors = (commands.CommandOnCooldown, commands.NoPrivateMessage, commands.BadArgument, commands.MissingRequiredArgument, commands.UnexpectedQuoteError, commands.DisabledCommand, commands.MissingPermissions, commands.MissingRole, commands.BotMissingPermissions, discord.errors.Forbidden)
passErrors = (commands.CommandNotFound, commands.NotOwner, commands.CheckFailure)

@bot.event
async def on_command_error(ctx, error):
    errorMessage = None

    if "TimeoutError" in str(error):
        errorMessage = ("Timed out.")

    if isinstance(error, raiseErrors):
        errorMessage = str(error)

    if errorMessage:
        return await ctx.send(errorMessage)

    if isinstance(error, passErrors):
        return

    if reports:
        await ctx.send("Error. This has been reported and will be reviewed shortly.")
        embed = discord.Embed(title="Error Report", description=None, color=0xff0000)
        embed.add_field(name="Guild Name:", value=ctx.guild.name, inline=True)
        embed.add_field(name="Guild ID:", value=ctx.guild.id, inline=True)
        embed.add_field(name="Guild Owner:", value=str(ctx.guild.owner), inline=True)
        embed.add_field(name="Channel:", value=ctx.channel.name, inline=True)
        embed.add_field(name="Error Victim:", value=str(ctx.author), inline=True)
        embed.add_field(name="Victim ID:", value=ctx.author.id, inline=True)
        embed.add_field(name="Error:", value=error, inline=False)
        await reports.send(botmaster.mention, embed=embed)
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
                else:
                    await reaction.remove(user)

        try:
            dic = reaction.message.embeds[0].to_dict()
            if dic['title'].startswith("(closed)"):
                await reaction.remove(user)
        except:
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
        except:
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


#-------------------------------------------------------------------------------COMMANDS---------------------------------------------------------------------------------------
#------------------------------------------------------------------------------OWNER ONLY--------------------------------------------------------------------------------------
@bot.command()
@commands.check(is_owner)
async def blacklist(ctx, member : discord.Member):
    if member.id in blackListed:
        raise commands.BadArgument(f"{str(member)} is already blacklisted")
    blackListed.append(member.id)
    r.lpush("blacklisted", member.id)
    await ctx.send(f"Blacklisted {str(member)}")


@bot.command()
@commands.check(is_owner)
async def unblacklist(ctx, member : discord.Member):
    if not member.id in blackListed:
        raise commands.BadArgument(f"{str(member)} is not blacklisted")
    blackListed.remove(member.id)
    r.lrem("blacklisted", 0, member.id)
    await ctx.send(f"Unblacklisted {str(member)}")


@bot.command()
@commands.check(is_owner)
async def setstatus(ctx, *, status):
    game = discord.Game(status)
    await bot.change_presence(activity=game)


@bot.command()
@commands.check(is_owner)
async def blacklisted(ctx):
    message = ""
    for x in blackListed:
        message = f"{message}\n{get(ctx.guild.members, id=x)}"
    await ctx.send(f"List of blacklisted members: {message}")


@bot.command()
@commands.check(is_owner)
async def disablecommand(ctx, commandName):
    command = get(bot.commands, name=commandName)
    if not command:
        raise commands.BadArgument(f'Command "{commandName}" not found.')
    command.update(enabled=False)
    await ctx.send(f"Disabled command {command}")


@bot.command()
@commands.check(is_owner)
async def enablecommand(ctx, commandName):
    command = get(bot.commands, name=commandName)
    if not command:
        raise commands.BadArgument(f'Command "{commandName}" not found.')
    command.update(enabled=True)
    await ctx.send(f"Enabled command {command}")


#THIS IS NOT MY EVAL COMMAND, I AM USING THIS: https://gist.github.com/nitros12/2c3c265813121492655bc95aa54da6b9
def insert_returns(body):
    if isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(body[-1].value)
        ast.fix_missing_locations(body[-1])

    if isinstance(body[-1], ast.If):
        insert_returns(body[-1].body)
        insert_returns(body[-1].orelse)

    if isinstance(body[-1], ast.With):
        insert_returns(body[-1].body)

@bot.command(aliases=['eval', 'exec', 'run'])
@commands.check(is_owner)
async def eval_fn(ctx, *, cmd):
    try:
        fn_name = "_eval_expr"

        cmd = cmd.strip("` ")

        cmd = "\n".join(f"    {i}" for i in cmd.splitlines())

        body = f"async def {fn_name}():\n{cmd}"

        parsed = ast.parse(body)
        body = parsed.body[0].body

        insert_returns(body)

        env = {
            'bot': ctx.bot,
            'discord': discord,
            'commands': commands,
            'ctx': ctx,
            '__import__': __import__,
            'get': get,
            'r': r,
            "os": os
        }
        exec(compile(parsed, filename="<ast>", mode="exec"), env)

        result = (await eval(f"{fn_name}()", env))
        if not result:
            result = "Done"
        await ctx.send(f"```{result}```")
    except Exception as err:
        raise commands.BadArgument(f"```{err}```")


@bot.command()
@commands.check(is_owner)
async def restart(ctx):
    await ctx.send("Confirm restart: (y/n)")
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and (m.content == "n" or m.content == "y")
    response = await bot.wait_for('message', timeout=60, check=check)
    response = response.content
    if response == "y":
        await bot.logout()
    if response == "n":
        await ctx.send("Cancelled")


@bot.command()
async def shutdown(ctx):
    await ctx.send("Confirm shutdown: (y/n)")
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and (m.content == "n" or m.content == "y")
    response = await bot.wait_for('message', timeout=60, check=check)
    response = response.content
    if response == "y":
        r.set("shutdown", "True")
        await bot.logout()
    if response == "n":
        await ctx.send("Cancelled")
#------------------------------------------------------------------------------MISCELLANEOUS--------------------------------------------------------------------------------------
@bot.command()
async def help(ctx, *category):
    prefix = determine_prefix(bot, ctx)
    if len(category) <= 0:
        embed = discord.Embed(title="Categories", description="This is a list of all the types of commands I can do!\nThe full code for GamerBot can be found at https://github.com/TanujKS/gamerbot", color=0xff0000)
        embed.set_thumbnail(url=bot.user.avatar_url)
        embed.add_field(name=f"VC Commands ({prefix}help VC):", value="Commands to help you manage your Voice Channels:", inline=False)
        embed.add_field(name=f"Team Commands ({prefix}help teams)", value="Commands that help you manage your teams for your game nights", inline=False)
        embed.add_field(name=f"Game Stats Commands ({prefix}help stats)", value="Commands to see Minecraft player's stats", inline=False)
        embed.add_field(name=f"Miscellaneous Commands ({prefix}help misc)", value="All other commands I can do!", inline=False)
        embed.add_field(name=f"APIs ({prefix}help apis)", value=f"APIs used by the {str(bot.user)}", inline=False)
        embed.set_footer(text=f"{str(bot.user)} is a bot created and maintained by {str(botmaster)}")
    elif category[0] == "VC":
        embed=discord.Embed(title="VC Commands", description="Commands I can do to help you manage your voice channels", color=0xff0000)
        embed.add_field(name=f"{prefix}mute (member or 'all' or 'channel-all')", value="Server mutes a member. 'channel-all' mutes all people in the channel you are currently in while 'all' mutes everyone a voice channel in the server. (Requires permission Mute Members)", inline=False)
        embed.add_field(name=f"{prefix}unmute (member or 'all' or 'channel-all')", value="Server unmutes a member (Requires permission Mute Members)", inline=False)
        embed.add_field(name=f"{prefix}deafen (member or 'all' or 'channel-all')", value="Server deafens a member (Requires permission Deafen Members)", inline=False)
        embed.add_field(name=f"{prefix}undeafen (member or 'all' or 'channel-all')", value="Server undeafens a member (Requires permission Deafen Members)", inline=False)
        embed.add_field(name=f"{prefix}dc (member or 'all' or 'channel-all')", value="Disconnects a member from their voice channel (Requires permission Move Members)", inline=False)
        embed.add_field(name=f"{prefix}move (member or 'all' or 'channel-all')", value="Moves member to another voice channel (Requires permission Move Members)", inline=False)
        embed.add_field(name=f"{prefix}moveteams", value="Moves all people who are in main Voice Channel back to their Team Voice Channel (Requires permission Move Members)", inline=False)
        embed.add_field(name=f"{prefix}moveevents", value="Moves all people who are in Team Voice Channels to the Event Voice Channel (Requires permission Move Members)", inline=False)
        embed.add_field(name=f"{prefix}speak (message)", value="Joins a voicechannel and uses TTS to speak a message. Useful if you are unable to unmute", inline=False)
    elif category[0] == "teams":
        embed=discord.Embed(title="Team Commands", description="Commands I can do to manage your teams for game nights", color=0xff0000)
        embed.add_field(name=f"{prefix}createteams", value="Creates a team menu where people can react to join teams (max limit of 2 and member can only be in 1 team) (Requires permission Manage Roles)", inline=False)
        embed.add_field(name=f"{prefix}closeteams", value="Close a team menu so people can no longer react (Requires permission Manage Roles)", inline=False)
        embed.add_field(name=f"{prefix}checkteams", value="Checks to make sure no one has somehow got into 2 teams (Requires permission Manage Roles)", inline=False)
        embed.add_field(name=f"{prefix}clearteams", value="Removes all the team roles from all members (Requires permission Manage Roles)", inline=False)
        embed.add_field(name=f"{prefix}clearteam (team)", value="Removes the specified team role from all members", inline=False)
        embed.add_field(name=f"{prefix}setteam (team) (*member)", value="Gives the specified member(s) the specified team role (first clears the members other teams) (Requires permission Manage Roles)", inline=False)
        embed.add_field(name=f"{prefix}eventban (user or 'all')", value="Prevents a user from joining teams or using team text/voice channels (Requires permission Manage Roles)", inline=False)
        embed.add_field(name=f"{prefix}eventunban (user or 'all')", value="Allows a user to join teams and use team text/voice channels (Requires permission Manage Roles)", inline=False)
        embed.add_field(name=f"{prefix}lockevents", value="Locks the team voice channels so that ONLY people with the team role can join", inline=False)
        embed.add_field(name=f"{prefix}unlockevents", value="Unlocks the team voice channels so that ANYONE can join them", inline=False)
    elif category[0] == "misc":
        embed=discord.Embed(title="Miscellaneous Commands", description="All other commands I can do!", color=0xff0000)
        embed.add_field(name=f"{prefix}nick (user)", value="Changes the nickname of a member (Requires permission Manage Nicknames)", inline=False)
        embed.add_field(name=f"{prefix}poll (Poll) (*options)", value="Creates a poll where you can only vote once", inline=False)
        embed.add_field(name=f"{prefix}closepoll", value="Closes a poll and shows the final results", inline=False)
        embed.add_field(name=f"{prefix}ping", value="Checks the bots ping in ms", inline=False)
        embed.add_field(name=f"{prefix}quote (@user) (quote)", value="Quotes a user using a webhook", inline=False)
        embed.add_field(name=f"{prefix}avatar (@user) (format)", value="Returns the avatar of a member in the specified format(‘webp’, ‘jpeg’, ‘jpg’, ‘png’ or ‘gif’)", inline=False)
        embed.add_field(name=f"{prefix}perms (@user)", value="Sends the server permissions for a certain member", inline=False)
        embed.add_field(name=f"{prefix}invite (*(max_age) (max_uses) (reason))", value="Generates a invite to the channel with the specified maximum age, uses, and reason. If no args are provided, it will default to infinite uses, infinite age, and no reason", inline=False)
        embed.add_field(name=f"{prefix}report", value="Report a problem to the bot developers", inline=False)
        embed.add_field(name=f"{prefix}settings", value="Tweak settings for your guild", inline=False)
        embed.add_field(name=f"{prefix}rps (user or 'bot')", value="Challenges a member (or the bot) to Rock Paper Scissors", inline=False)
        embed.add_field(name=f"{prefix}dm (user or role)", value="Useful if you need to DM a large amount of members a message", inline=False)
        embed.add_field(name=f"{prefix}donate", value="Information about donating to GamerBot", inline=False)
        embed.add_field(name=f"{prefix}starttimer", value="Starts a stopwatch", inline=False)
        embed.add_field(name=f"{prefix}stoptimer", value="Stops a stopwatch", inline=False)
        embed.add_field(name=f"{prefix}unpinall", value="Unpins all messages in a channel", inline=False)
        embed.add_field(name=f"{prefix}translate (sentence)", value="Uses Google Translate to translate a message into English", inline=False)
        embed.add_field(name=f"{prefix}define (word)", value="Returns the defintion of an English word", inline=False)
    elif category[0] == "stats":
        embed=discord.Embed(title="Game Stat Commands", description="Commands to see a player's stats in various games", color=0xff0000)
        embed.add_field(name=f"{prefix}minecraft (minecraft_player)", value="Shows stats about a Minecraft player", inline=False)
        embed.add_field(name=f"{prefix}mcverify (your_minecraft_username)", value="Allows you to link your Discord account to your Minecraft account using the Hypixel Social Media Link system", inline=False)
        embed.add_field(name=f"{prefix}skin (minecraft_player)", value="Shows the skin of a Minecraft player", inline=False)
        embed.add_field(name=f"{prefix}hypixel (minecraft_player)", value="Shows Hypixel stats about a Minecraft player", inline=False)
        embed.add_field(name=f"{prefix}bedwars (minecraft_player) (optional_mode)", value="Shows stats about a Hypixel Bedwars player \nOptional modes are: solos, doubles, 3v3v3v3, 4v4v4v4, 4v4", inline=False)
        embed.add_field(name=f"{prefix}hypixelguild (minecraft_player)", value="Shows Hypixel Guild stats about a Minecraft player", inline=False)
        embed.add_field(name=f"{prefix}skywars (minecraft_player) (optional_mode)", value="Shows stats about a Hypixel Skywars player \nOptional modes are: solos normal, solos insane, teams normal, teams insane", inline=False)
        embed.add_field(name=f"{prefix}duels (minecraft_player) (optional_mode)", value="Shows stats about a Hypixel Duels player \nOptional modes are classic, uhc, op, sumo, skywars, uhc doubles, combo, bridge", inline=False)
        embed.add_field(name=f"{prefix}fortnite (fortnite_player)", value="Shows stats about a Fortnite player", inline=False)
        embed.add_field(name=f"{prefix}twitch (channel)", value="Shows stats of a Twitch streamer", inline=False)
        embed.add_field(name=f"{prefix}twitchtrack (twitch_channel) (message to send when streamer goes live)", value="Track Twitch streamers and get notified whenever they stream", inline=False)
        embed.add_field(name=f"{prefix}deltrack (twitch_channel)", value="Stop tracking a Twitch streamer", inline=False)
        embed.add_field(name=f"{prefix}twitchtracklist", value="Shows all Twitch streamers that are being tracked", inline=False)
        embed.add_field(name=f"{prefix}youtube (channel)", value="Shows stats of a YouTube channel", inline=False)
        embed.add_field(name=f"{prefix}csgo (id)", value="Shows stats of a CS:GO player", inline=False)
        embed.add_field(name=f"{prefix}csgolink (id)", value="Links your account to a CS:GO ID", inline=False)
    elif category[0] == "apis":
        embed = discord.Embed(title=f"APIs used by {str(bot.user)}", description=f"All APIs used by {str(bot.user)}", color=0xff0000)
        embed.add_field(name=f"Hypixel API", value="https://api.hypixel.net/", inline=False)
        embed.add_field(name=f"Mojang API", value="https://mojang.readthedocs.io/en/latest/", inline=False)
        embed.add_field(name=f"Crafatar API", value="https://crafatar.com/", inline=False)
        embed.add_field(name=f"Fortnite API", value="https://fortnite-api.com/", inline=False)
        embed.add_field(name=f"Twitch API", value="https://dev.twitch.tv/docs/api/", inline=False)
        embed.add_field(name=f"YouTube API", value="https://developers.google.com/youtube/", inline=False)
        embed.add_field(name="Tracker.gg API", value="https://tracker.gg", inline=False)
        embed.add_field(name="Google Translate API", value="https://pypi.org/project/googletrans/", inline=False)
    else:
        raise commands.BadArgument(f'Category "{category[0]}" not found.')
    await ctx.send(embed=embed)


@bot.command()
@commands.has_guild_permissions(manage_messages=True)
@commands.bot_has_guild_permissions(manage_messages=True)
async def unpinall(ctx):
    await ctx.send(f"Are you sure you want me too unpin {len(await ctx.channel.pins())} messages? (y/n)")
    def check(m):
        responses = ['y', 'n']
        return ctx.author == m.author and ctx.channel == m.channel and msg.content in responses
    msg = await bot.wait_for('message', timeout=60.0, check=check)
    if msg.content == "y":
        for message in await ctx.channel.pins():
            await message.unpin()
        await ctx.send(f"Unpinned all messages")
    elif msg.content == "n":
        await ctx.send("Cancelled")


@bot.command()
async def settings(ctx, *setting):
    if len(setting) == 0:
        embed = discord.Embed(title=f"Settings for {ctx.guild.name}", description="To edit a setting use '?settings (setting) (on/off, 1/2/3, etc)", color=0xff0000)
        embed.add_field(name=f"Anti-Ez: `{convertBooltoStr(guildInfo[ctx.guild.id]['antiez'])}`", value="?settings antiez on/off")
        embed.add_field(name=f"Maximum members allowed on one team: `{guildInfo[ctx.guild.id]['teamLimit']}`", value="?settings teamlimit 1/2/3...")
        embed.add_field(name=f"Role required to use ?speak (Text to Voice Channel): `{guildInfo[ctx.guild.id]['TTVCrole']}`", value="?settings TTVCrole some_role")
        embed.add_field(name=f"Prefix for {str(bot.user)} in this server: `{guildInfo[ctx.guild.id]['prefix']}`", value="?settings prefix some_prefix")
    elif len(setting) == 2:
        if not ctx.author.guild_permissions.administrator:
            raise commands.MissingPermissions(['administrator'])
        if setting[0] == "antiez":
            if setting[1] == "on":
                guildInfo[ctx.guild.id]['antiez'] = True
            elif setting [1] == "off":
                guildInfo[ctx.guild.id]['antiez'] = False
            else:
                raise commands.BadArgument("Argument must be 'on' or 'off'")
            embed = discord.Embed(title=f"Anti-EZ is now {convertBooltoStr(guildInfo[ctx.guild.id]['antiez'])}", description=None, color=0xff0000)
        elif setting[0] == "teamlimit":
            try:
                setting = int(setting[1])
            except ValueError:
                raise commands.BadArgument("Argument must be a number")
            guildInfo[ctx.guild.id]['teamLimit'] = setting
            embed = discord.Embed(title=f"Maximum members allowed in one team is now {guildInfo[ctx.guild.id]['teamLimit']}", description=None, color=0xff0000)
        elif setting[0] == "TTVCrole":
            if setting[1] == "everyone":
                setting1 = "@everyone"
            else:
                setting1 = setting[1]
            if not get(ctx.guild.roles, name=setting1):
                raise commands.RoleNotFound(setting1)
            guildInfo[ctx.guild.id]['TTVCrole'] = setting1
            embed = discord.Embed(title=f"TTVC Role is now set to {guildInfo[ctx.guild.id]['TTVCrole']}", description=None, color=0xff0000)
        elif setting[0] == "prefix":
            guildInfo[ctx.guild.id]['prefix'] = setting[1]
            embed = discord.Embed(title=f"Prefix for {str(bot.user)} in {ctx.guild.name} is now {guildInfo[ctx.guild.id]['prefix']}")
        else:
            raise commands.BadArgument(f'Setting "{setting[0]}" not found.')
        rval = json.dumps(guildInfo)
        r.set("guildInfo", rval)
    else:
        raise commands.BadArgument("Invalid arguments")
    await ctx.send(embed=embed)


@bot.command()
async def translate(ctx, *, message):
    await ctx.send(f"Translating {message}")
    translation = translator.translate(message, dest='en')
    await ctx.send(f"```{LANGUAGES[translation.src.lower()]} -----> {LANGUAGES[translation.dest]} \n{message} -----> {translation.text}```")


@bot.command()
async def define(ctx, word):
    message = ""
    meanings = dictionary.meaning(word)
    if not meanings:
        raise commands.BadArgument(f"{word} is not a recognized word")
    for item in meanings:
        message += f"\n{item}:"
        for meaning in meanings[item]:
            message += f"\n     {meaning}"

    await ctx.send(f'Defintion of {word}: ```{message}```')


@bot.command()
@commands.has_guild_permissions(use_voice_activation=True, connect=True, speak=True)
@commands.bot_has_guild_permissions(use_voice_activation=True, connect=True, speak=True)
async def join(ctx):
    if ctx.author.voice:
        await ctx.author.voice.channel.connect()
    else:
        raise commands.BadArgument("You are not in a voice channel.")


@bot.command()
@commands.has_guild_permissions(use_voice_activation=True, connect=True, speak=True)
@commands.bot_has_guild_permissions(use_voice_activation=True, connect=True, speak=True)
@commands.cooldown(5, 60, commands.BucketType.member)
async def speak(ctx, *, message):
    role = get(ctx.author.roles, name=guildInfo[ctx.guild.id]['TTVCrole'])
    if not role:
        raise commands.MissingPermissions([f"role {guildInfo[ctx.guild.id]['TTVCrole']} which is required to use Text to Voice Channel."])
    fullmessage = f"{ctx.author.name} says {message}"
    if ctx.guild.me.voice:
        vc = ctx.guild.voice_client
    elif ctx.author.voice:
        try:
            vc = await ctx.author.voice.channel.connect()
        except discord.ClientException:
            pass
    else:
        raise commands.BadArgument("You are not in a voice channel.")
    await ctx.guild.me.edit(deafen=True)
    tts = gtts.gTTS(fullmessage, lang="en")
    tts.save("text.mp3")
    while True:
        vc = ctx.guild.voice_client
        if not vc:
            return
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
            raise commands.BadArgument("Invalid arguments. Arguments must have 'max_age', 'max_uses', 'reason'")
    await ctx.send(f"Created invite with a maximum age of {max_age} seconds, {max_uses} maximum uses, and with reason: {reason}. \n{await ctx.channel.create_invite(max_age=max_age, max_uses=max_uses, reason=reason)}")


def convertPermtoEmoji(member, perm):
    if getattr(member.guild_permissions, perm) is True:
        return "✅"
    if getattr(member.guild_permissions, perm) is False:
        return "❌"

@bot.command()
@commands.guild_only()
async def perms(ctx, *member : discord.Member):
    if len(member) == 0:
      member = ctx.author
    else:
      member = member[0]
    embed = discord.Embed(title=f"Perms for {str(member)} in {ctx.guild.name}", description=None, color=0xff0000)
    for perm in member.guild_permissions:
        embed.add_field(name=perm[0].replace('_', ' ').title(), value=convertPermtoEmoji(member, perm[0]))
    await ctx.send(embed=embed)


@bot.command(aliases=['pfp', 'profile'])
async def avatar(ctx, *member : discord.Member):
    if len(member) == 0:
        member = ctx.author
    elif ctx.message.mentions:
        member = ctx.message.mentions[0]
    await ctx.send(member.avatar_url_as(format=None, size=1024))


@bot.command()
async def emoji(ctx, *, emoji : discord.Emoji):
    await ctx.send(emoji.url)


@bot.command()
@commands.bot_has_guild_permissions(manage_emojis=True)
@commands.has_guild_permissions(manage_emojis=True)
async def addemoji(ctx, emojiName, url):
    try:
        response = requests.get(url)
    except requests.exceptions.MissingSchema as err:
        raise commands.BadArgument(err)
    img = BytesIO(response.content)
    emoji = await ctx.guild.create_custom_emoji(name=emojiName, image=img.read())
    await ctx.send(f"Created {emojiName}: \n{emoji}")


@bot.command()
@commands.bot_has_guild_permissions(add_reactions=True, manage_messages=True)
async def poll(ctx, poll, *options):
    if len(options) > 8:
        raise commands.BadArgument("Maximum of 8 options")
    if len(options) < 2:
        raise commands.BadArgument("Minimum of 2 options")
    try:
        embed = discord.Embed(title=poll, description=None, color=0xff0000)
    except discord.HTTPException:
        raise commands.BadArgument("Poll title must be less than 256 characters")
    index = 0
    for option in options:
        embed.add_field(name=emojis[index], value="\u200b", inline=True)
        embed.add_field(name=option, value="\u200b", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        index += 1
    embed.set_footer(text=f"Poll by {str(ctx.author)}")
    msg = await ctx.send(embed=embed)
    await ctx.message.delete()
    for i in range(0, len(options)):
        await msg.add_reaction(emojis[i])


@bot.command()
@commands.bot_has_guild_permissions(add_reactions=True, manage_messages=True)
async def closepoll(ctx):
        def closePollCheck(reaction, user):
            return user == ctx.author and str(reaction) == "❌"
        close = await ctx.send("React to the poll I must close with an ❌")
        reaction, user = await bot.wait_for('reaction_add', timeout=120.0, check=closePollCheck)
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
            raise commands.BadArgument(f"Only {dic} can close that poll")


@bot.command()
@commands.bot_has_guild_permissions(manage_nicknames=True)
@commands.has_permissions(manage_nicknames=True)
async def nick(ctx, member : discord.Member, *nick):
    if member.nick:
        oldNick = member.nick
    else:
        oldNick = member.name
    if len(nick) == 0:
        nick = None
    else:
        nick = " ".join(nick)
    try:
        await member.edit(nick=nick)
    except discord.Forbidden:
        raise commands.BadArgument(f"Could not change {str(member)}'s nickname because their highest role is higher than mine.")
    except discord.HTTPException:
        raise commands.BadArgument("Nickname must be fewer than 32 characters")
    if nick is None:
        nick = member.name
    await ctx.send(f"Changed {member.name}'s nickname from {oldNick} to {nick}")


@bot.command()
@commands.cooldown(1, 5, commands.BucketType.channel)
async def ping(ctx):
    t = await ctx.send("Pong!")
    await t.edit(content=f'Pong! `{(t.created_at-ctx.message.created_at).total_seconds() * 1000}ms`')


@bot.command()
@commands.bot_has_guild_permissions(manage_webhooks=True, manage_messages=True)
async def quote(ctx, member : discord.Member, *, message):
    message = message.replace("@", "")
    if not message:
        raise commands.BadArgument("No message provided")
    webhooks = await ctx.channel.webhooks()
    webhook = None
    for webhookVar in webhooks:
        if webhookVar.name == "quotebot":
            webhook = webhookVar
            break
    if not webhook:
        webhook = await ctx.channel.create_webhook(name="quotebot")
    if member.nick:
        username = member.nick
    else:
        username = member.name
    await webhook.send(message, username=username, avatar_url=member.avatar_url)
    await ctx.message.delete()


@bot.command()
@commands.cooldown(1, 600, commands.BucketType.guild)
async def report(ctx):
    def check(m):
        return m.channel == ctx.channel and m.author == ctx.author
    await ctx.send("Please write your message as to what errors/problems you are experiencing. This will timeout in 3 minutes")
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


@bot.command()
async def starttimer(ctx):
    if stopWatches.get(ctx.author.id):
        raise commands.BadArgument("Stop watch already in use")
    await ctx.send("Starting stopwatch")
    stopWatches[ctx.author.id] = datetime.utcnow()


@bot.command()
async def stoptimer(ctx):
    startTime = stopWatches.get(ctx.author.id)
    if not startTime:
        raise commands.BadArgument("No active stopwatches")
    seconds = round((datetime.utcnow() - startTime).total_seconds())
    await ctx.send(f"""Ended timer. Timer ran for:
{seconds} seconds
{round(seconds/60)} minutes
{round((seconds/60)/60)} hours
""")
    del stopWatches[ctx.author.id]


@bot.command()
@commands.has_guild_permissions(administrator=True)
async def dm(ctx, message):
    dmedMessage = "Succesfuly DMed:"
    for role in ctx.message.role_mentions:
        dmedMessage += f"\nAll members with {role.name}"
        for member in role.members:
            dm = await member.create_dm()
            await dm.send(message)
    for member in ctx.message.mentions:
        dmedMessage += f"\n{member.name}"
        dm = await member.create_dm()
        await dm.send(message)
    await ctx.send(dmedMessage)


@bot.command()
async def donate(ctx):
    embed = discord.Embed(title="Donate to GamerBot", description=f"Donations help pay for the server required to run GamerBot and to pay for premium APIs to deliver faster stats. Donating perks can include custom commands or a custom bot for your own server. Please contact {str(botmaster)} for more info.", color=0xff0000)
    await ctx.send(embed=embed)
#------------------------------------------------------------------------------VOICE CHANNEL MANAGEMENT--------------------------------------------------------------------------------------
@bot.command()
@commands.guild_only()
@commands.bot_has_guild_permissions(move_members=True)
@commands.has_guild_permissions(move_members=True)
async def move(ctx, member, *, channelName):
    if channelName == "me":
        if not ctx.author.voice:
            raise commands.BadArgument("You are not in a voice channel")
        channel = ctx.author.voice.channel
    else:
        channel = get(ctx.guild.voice_channels, name=channelName)
    if not channel:
        raise commands.ChannelNotFound(channelName)
    if member == "channel-all":
        if not ctx.author.voice:
            raise commands.BadArgument("You are not in a voice channel")
        oldVC = ctx.author.voice.channel
        for member in oldVC.members:
            try:
                await member.move_to(channel)
            except (discord.HTTPException, commands.errors.CommandInvokeError):
                raise commands.BotMissingPermissions(['view channel', 'connect', 'or move members'])
        await ctx.send(f"Moved all in {oldVC.name} to {channel.name}")
    elif member == "all":
        for voice_channel in ctx.guild.voice_channels:
            for member in voice_channel.members:
                try:
                    await member.move_to(channel)
                except (discord.HTTPException, commands.errors.CommandInvokeError):
                    raise commands.BotMissingPermissions(['view channel', 'connect', 'or move members'])
        await ctx.send(f"Moved all members to {channel.name}")
    else:
        try:
            member = ctx.message.mentions[0]
        except IndexError:
            raise commands.MemberNotFound(member)
        if not member.voice:
            raise commands.BadArgument(f"{str(member)} is not in a voice channel")
        try:
            await member.move_to(channel)
        except (discord.HTTPException, commands.errors.CommandInvokeError):
            raise commands.BotMissingPermissions(['view channel', 'connect', 'or move members'])
        await ctx.send(f"Moved {str(member)} to {str(channel)}")


@bot.command()
@commands.bot_has_guild_permissions(mute_members=True)
@commands.has_guild_permissions(mute_members=True)
async def mute(ctx, member):
        if member == "channel-all":
            if not ctx.author.voice.channel:
                raise commands.BadArgument("You are not in a voice channel")
            for member in ctx.author.voice.channel.members:
                await member.edit(mute=True)
            await ctx.send(f"Muted all in {ctx.author.voice.channel.name}")
        elif member == "all":
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
                raise commands.BadArgument(f"{str(member)} is not in a voice channel")
            except IndexError:
                raise commands.MemberNotFound(member)


@bot.command()
@commands.bot_has_guild_permissions(deafen_members=True)
@commands.has_guild_permissions(deafen_members=True)
async def deafen(ctx, member):
        if member == "channel-all":
            if not ctx.author.voice.channel:
                raise commands.BadArgument("You are not in a voice channel")
            for member in ctx.author.voice.channel.members:
                await member.edit(deafen=True)
            await ctx.send(f"Deafened all in {ctx.author.voice.channel.name}")
        elif member == "all":
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
                raise commands.BadArgument(f"{str(member)} is not in a voice channel")
            except IndexError:
                raise commands.MemberNotFound(member)


@bot.command()
@commands.bot_has_guild_permissions(mute_members=True)
@commands.has_guild_permissions(mute_members=True)
async def unmute(ctx, member):
        if member == "channel-all":
            if not ctx.author.voice:
                raise commands.BadArgument("You are not in a voice channel")
            for member in ctx.author.voice.channel.members:
                await member.edit(mute=False)
            await ctx.send(f"Unmuted all in {ctx.author.voice.channel.name}")
        elif member == "all":
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
                raise commands.BadArgument(f"{str(member)} is not in a voice channel")
            except IndexError:
                raise commands.MemberNotFound(member)


@bot.command()
@commands.bot_has_guild_permissions(deafen_members=True)
@commands.has_guild_permissions(deafen_members=True)
async def undeafen(ctx, member):
        if member == "channel-all":
            if not ctx.author.voice:
                raise commands.ChannelNotFound("You are not in a voice channel")
            for member in ctx.author.voice.channel.members:
                await member.edit(deafen=False)
            await ctx.send(f"Undeafened all in {ctx.author.voice.channel.name}")
        if member == "all":
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
                raise commands.BadArgument(f"{str(member)} is not in a voice channel")
            except IndexError:
                raise commands.MemberNotFound(member)


@bot.command()
@commands.bot_has_guild_permissions(move_members=True)
@commands.has_guild_permissions(move_members=True)
async def dc(ctx, member):
    if member == "channel-all":
        if not ctx.author.voice:
            raise commands.ChannelNotFound("You are not in a voice channel")
        for member in ctx.author.voice.channel.members:
            await member.move_to(None)
        await ctx.send(f"Disconnected all in {ctx.author.voice.channel.name}")
    elif member == "all":
        for voicechannel in ctx.guild.voice_channels:
            for member in voicechannel.members:
                await member.move_to(None)
        await ctx.send("Disconnected all")
    else:
        try:
            member = ctx.message.mentions[0]
        except IndexError:
            raise commands.MemberNotFound(member)
        if not member.voice:
            raise commands.BadArgument(f"{str(member)} is not in a voice channel")
        await member.edit(voice_channel=None)
        await ctx.send(f"Disconnected {str(member)}")


@bot.command()
@commands.bot_has_guild_permissions(move_members=True)
@commands.has_guild_permissions(move_members=True)
async def moveteams(ctx):
        if not any("Events" in voicechannel.name for voicechannel in ctx.guild.voice_channels):
            raise commands.BadArgument("Could not find voice channel, your server may not be setup for Game Events yet. Run ?setup")
        if not all(get(ctx.guild.roles, name=team) for team in teams):
            raise commands.BadArgument("Could not find team roles, your server may not be setup for Game Events yet. Run ?setup")
        if not all(get(ctx.guild.voice_channels, name=team) for team in teams):
            raise commands.BadArgument("Could not find team channels, your server may not be setup for Game Events yet. Run ?setup")
        for voicechannel in ctx.guild.voice_channels:
            if "Events" in str(voicechannel):
                for member in voicechannel.members:
                    for team in teams:
                        if get(member.roles, name=team):
                            await member.edit(voice_channel=get(ctx.guild.voice_channels, name=team))
                return await ctx.send(f"Moved all members to their team voice channels")


@bot.command()
@commands.bot_has_guild_permissions(move_members=True)
@commands.has_guild_permissions(move_members=True)
async def moveevents(ctx):
    if not any("Events" in voicechannel.name for voicechannel in ctx.guild.voice_channels):
        raise commands.BadArgument("Could not find voice channel, your server may not be setup for Game Events yet. Run ?setup")
    for vc in ctx.guild.voice_channels:
        if "Events" in str(vc):
            events = vc
            break
    for team in teams:
        voicechannel = get(ctx.guild.voice_channels, name=team)
        if not voicechannel:
            raise commands.BadArgument(f"Could not find {team} voicechannel. Make sure your server is setup for gaming events using ?setup.")
        for member in voicechannel.members:
            await member.edit(voice_channel=events)
    await ctx.send(f"Moved all members to {events.name}")


#------------------------------------------------------------------------------TEAM/EVENT MANAGEMENT--------------------------------------------------------------------------------------
@bot.command()
@commands.bot_has_guild_permissions(manage_channels=True)
@commands.has_permissions(manage_channels=True)
async def lockevents(ctx):
        for team in teams:
            channel = get(ctx.guild.voice_channels, name=team)
            if not channel:
                raise commands.BadArgument("Could not find voice channel, your server may not be setup for Game Events yet. Run ?setup")
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
                raise commands.BadArgument("Could not find voice channel, your server may not be setup for Game Events yet. Run ?setup")
            await voicechannel.set_permissions(ctx.guild.default_role, connect=True)
            await voicechannel.edit(user_limit=None)
        await ctx.send("Unlocked all voice channels")


@bot.command()
@commands.bot_has_guild_permissions(manage_roles=True)
@commands.has_guild_permissions(manage_roles=True)
async def eventban(ctx, member : discord.Member):
        role = get(ctx.guild.roles, name="Banned from event")
        if not role:
            raise commands.BadArgument("Could not find role, your server may not be setup for Game Events yet. Run ?setup")
        if role in member.roles:
            await ctx.send(f"{str(member)} is already banned")
        else:
            await member.add_roles(role)
            await ctx.send(f"Banned {str(member)} from events")


@bot.command()
@commands.bot_has_guild_permissions(manage_roles=True)
@commands.has_guild_permissions(manage_roles=True)
async def eventunban(ctx, member):
        role = get(ctx.guild.roles, name="Banned from event")
        if not role:
            raise commands.BadArgument("Could not find role, your server may not be setup for Game Events yet. Run ?setup")
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
                    raise commands.BadArgument(f"{str(member)} is not banned")
            except IndexError:
                raise commands.MemberNotFound(member)


@bot.command()
@commands.bot_has_guild_permissions(manage_roles=True, manage_messages=True)
@commands.has_guild_permissions(manage_roles=True, manage_messages=True)
async def createteams(ctx):
        for team in teams:
            role = get(ctx.guild.roles, name=team)
            if not role:
                raise commands.BadArgument("Could not find the team roles, your server may not be setup for Game Events yet. Run ?setup")
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
            raise commands.BadArgument("Could not find team roles, your server may not be setup for Game Events yet. Run ?setup")
        for member in role.members:
            await member.remove_roles(role)
            await ctx.send(f"Cleared {str(role)}")
    else:
        raise commands.BadArgument(f'Team "{team}" not found.')


@bot.command()
@commands.bot_has_guild_permissions(manage_roles=True)
@commands.has_guild_permissions(manage_roles=True)
async def clearteams(ctx):
        for team in teams:
            role = get(ctx.guild.roles, name=team)
            if not role:
                raise commands.BadArgument("Could not find team roles, your server may not be setup for Game Events yet. Run ?setup")
            for member in role.members:
                await member.remove_roles(role)
        await ctx.send("Cleared all teams")


@bot.command()
@commands.bot_has_guild_permissions(manage_channels=True, manage_roles=True)
@commands.has_guild_permissions(manage_channels=True, manage_roles=True)
@commands.cooldown(1, 120, commands.BucketType.guild)
async def setup(ctx):
    def check(m):
        return m.channel == ctx.channel and m.author == ctx.author
    await ctx.send("Alright lets get started setting up your server! What game are you going to be playing on your server? (Or type `cancel`)")
    msg = await bot.wait_for('message', check=check)
    if msg.content == "cancel":
        await ctx.send("Cancelled.")
        return
    await ctx.send(f"Setting up your server for {msg.content} Events. \nThis make take a little while...")
    category = await ctx.guild.create_category(msg.content + " Events")
    announcement = await ctx.guild.create_text_channel(f"{msg.content}-announcement", overwrites=None, category=category)
    await asyncio.sleep(5)
    rules = await ctx.guild.create_text_channel(f"{msg.content}-rules", overwrites=None, category=category)
    await asyncio.sleep(5)
    logs = await ctx.guild.create_text_channel(f"{msg.content}-event-logs", overwrites=None, category=category)
    await asyncio.sleep(5)
    await announcement.set_permissions(ctx.guild.default_role, send_messages=False)
    await rules.set_permissions(ctx.guild.default_role, send_messages=False)
    await logs.set_permissions(ctx.guild.default_role, send_messages=False)
    lounge = await ctx.guild.create_text_channel(f"{msg.content}-lounge", overwrites=None, category=category)
    await asyncio.sleep(5)
    banned = await ctx.guild.create_role(name="Banned from event")
    await asyncio.sleep(5)
    perms = lounge.overwrites_for(banned)
    perms.send_messages = False
    await lounge.set_permissions(banned, overwrite=perms)
    channel1 = await ctx.guild.create_voice_channel(f"{msg.content} Events", overwrites=None, category=category)
    await asyncio.sleep(5)
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
        await asyncio.sleep(5)
    await ctx.send("Your server is setup! \nIMPORTANT: **DO NOT change the name of the voicechannels or the roles that I created it may mess up certain commands.**")


@bot.command()
@commands.bot_has_guild_permissions(manage_messages=True)
@commands.has_guild_permissions(manage_messages=True)
async def closeteams(ctx):
        def closeTeamsCheck(reaction, user):
            return user == ctx.author and reaction.message.content == "React to get into your teams"
        close = await ctx.send("React to the message I must close")
        reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=closeTeamsCheck)
        await close.delete()
        await ctx.message.delete()
        await reaction.message.edit(content="Teams are now closed.")


@bot.command()
@commands.bot_has_guild_permissions(manage_channels=True, manage_roles=True)
@commands.has_guild_permissions(manage_channels=True, manage_roles=True)
async def wipe(ctx):
        def wipeCheck(m):
            return m.channel == ctx.channel and m.author == ctx.author and (m.content == "n" or m.content == "y")
        await ctx.send("Are you sure you want to wipe the server of all event channels? This will delete ALL channels and ALL roles I have created (y/n)")
        response = await bot.wait_for('message', timeout=60, check=wipeCheck)
        if response.content == "y":
            for category in ctx.guild.categories:
                if "Events" in str(category):
                    for channel in category.channels:
                        await channel.delete()
                    await category.delete()
            for team in teams:
                role = get(ctx.guild.roles, name=team)
                if role:
                    await role.delete()
            role = get(ctx.guild.roles, name="Banned from event")
            if role:
                await role.delete()
            await ctx.send("Wiped all event channels")
        if response.content == "n":
            await ctx.send("Ok, cancelled the wipe")


@bot.command()
@commands.bot_has_guild_permissions(manage_roles=True)
@commands.has_guild_permissions(manage_roles=True)
async def setteam(ctx, team : discord.Role, member : discord.Member):
        if team.name in teams:
                for roles in ctx.author.roles:
                    if roles.name in teams:
                        await ctx.author.remove_roles(roles)
                try:
                    for member in ctx.message.mentions:
                        await member.add_roles(team)
                        await ctx.send(f"Added {str(member)} to {str(team)}")
                except IndexError:
                    raise commands.MemberNotFound(member)
        else:
            raise commands.BadArgument(f'Team "{team}" not found.')


#------------------------------------------------------------------------------MINI-GAMES--------------------------------------------------------------------------------------
moves = ["rock", "paper", "scissors"]

@bot.command()
@commands.guild_only()
async def rps(ctx, member):
    if member == "bot":
        def rpsBotCheck(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content in moves
        await ctx.send("Please choose from `rock`, `paper`, or `scissors`")
        move1 = await bot.wait_for('message', timeout = 60.0, check=rpsBotCheck)
        botmove = moves[random.randint(0,2)]
        move2 = await ctx.send(botmove)
    else:
        def rpsCheck2(m):
            return m.author == member and m.guild == None and m.content in moves
        def rpsCheck1(m):
            return m.author == ctx.author and m.guild == None and m.content in moves
        member = ctx.message.mentions[0]
        await ctx.send(f"{member.mention}! {ctx.author.mention} challenges you to rock paper scissors!")
        await ctx.send(f"{ctx.author.mention} DM me your move")
        dm = await ctx.author.create_dm()
        await dm.send("Please choose from `rock`, `paper`, or `scissors`")
        move1 = await bot.wait_for('message', timeout = 60.0, check=rpsCheck1)
        await ctx.send(f"{member.mention} DM me your move")
        dm = await member.create_dm()
        await dm.send("Please choose from `rock`, `paper`, or `scissors`")
        move2 = await bot.wait_for('message', timeout = 60.0, check=rpsCheck2)
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
def hasLink(ctx, player):
    if len(player) == 0:
        member = ctx.author
    elif ctx.message.mentions:
        member = ctx.message.mentions[0]
    else:
        member = None
        player = player[0]
    if member:
        player = r.get(member.id)
        if player is None:
            raise commands.BadArgument(f"{str(member)} has not linked their Discord to their Minecraft account")
        player = player.decode('utf-8')
    return player


@bot.command(aliases=['mc'])
async def minecraft(ctx, *player):
    player = hasLink(ctx, player)
    uuid = MojangAPI.get_uuid(player)
    if not uuid:
        raise commands.BadArgument(f'Player "{player}" not found.')
    info = MojangAPI.get_profile(uuid)
    name_history = MojangAPI.get_name_history(uuid)
    history = ""
    for name in name_history:
        history += f"\n{name['name']}"
    embed = discord.Embed(title=f"{info.name}'s Minecraft Profile", description=f"Stats for {info.name}", color=0xff0000)
    embed.set_thumbnail(url=f"https://crafatar.com/renders/head/{uuid}?overlay")
    embed.set_footer(text="Stats provided using the Mojang APIs \nAvatars and skins from Crafatar")
    embed.add_field(name="Username:", value=info.name, inline=True)
    embed.add_field(name="UUID:", value=info.id, inline=True)
    embed.add_field(name="Past Usernames (From oldest down to latest):", value=history, inline=False)
    await ctx.send(embed=embed)


@bot.command(aliases=['mclink'])
async def mcverify(ctx, player):
    uuid = MojangAPI.get_uuid(player)
    if not uuid:
        raise commands.BadArgument(f'Player "{player}" not found.')
    data = requests.get(f"https://api.hypixel.net/player?key={HYPIXEL_KEY}&uuid={uuid}").json()
    if not data.get('player') or not data['player'].get('socialMedia'):
        raise commands.BadArgument(f"{player} has not played Hypixel or has not linked Discord and cannot verify their account")
    link = data['player']['socialMedia']['links'].get('DISCORD')
    if link is None:
        raise commands.BadArgument(f"{data['player']['displayname']} has no Discord user linked to their Hypixel account")
    if link == str(ctx.author):
        await ctx.send(f"Your Discord account is now linked to {data['player']['displayname']}. Anyone can see your Minecraft and Hypixel stats by doing '?mc {ctx.author.mention}' and running '?hypixel' will bring up your own Hypixel stats")
        r.set(ctx.author.id, data['player']['displayname'])
    else:
        raise commands.BadArgument(f"{data['player']['displayname']} can only be linked to {data['player']['socialMedia']['links']['DISCORD']}")


@bot.command()
async def skin(ctx, *player):
    player = hasLink(ctx, player)
    uuid = MojangAPI.get_uuid(player)
    if not uuid:
        raise commands.BadArgument(f'Player "{player}" not found.')
    info = MojangAPI.get_profile(uuid)
    embed=discord.Embed(title=f"{info.name}'s Skin", description=f"Full render of {info.name}'s skin", color=0xff0000)
    embed.set_footer(text="Stats provided using the Mojang API \nAvatars and skins from Crafatar")
    embed.set_image(url=f"https://crafatar.com/renders/body/{uuid}?overlay")
    await ctx.send(embed=embed)


@bot.command()
async def hypixel(ctx, *player):
    player = hasLink(ctx, player)
    uuid = MojangAPI.get_uuid(player)
    if not uuid:
        raise commands.BadArgument(f'Player "{player}" not found.')
    data = requests.get(f"https://api.hypixel.net/player?key={HYPIXEL_KEY}&uuid={uuid}").json()
    if not data.get('player') or not data['player'].get('displayname'):
        raise commands.BadArgument(f"{player} has not played Hypixel")
    embed = discord.Embed(title=f"{data['player']['displayname']}'s Hypixel Profile", description=f"Hypixel stats for {data['player']['displayname']}", color=0xff0000)
    embed.set_thumbnail(url=f"https://crafatar.com/renders/head/{data['player']['uuid']}?overlay")
    embed.set_footer(text=f"Stats provided using the Mojang and Hypixel APIs \nAvatars from Crafatar \nStats requested by {str(ctx.author)}")
    status = None
    ts = data['player'].get('lastLogin')
    if ts is None:
        d = "Never"
        status = "Offline"
    else:
        ts /= 1000
        d = ((datetime.fromtimestamp(ts)).astimezone(timezone('US/Pacific'))).strftime('%H:%M:%S %m/%d/%Y')
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
            rank = data['player'].get('newPackageRank', "None")

    rank = rank.replace("_PLUS","+")
    embed.add_field(name="Status:", value=status, inline=True)
    embed.add_field(name="Rank:", value=rank, inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    embed.add_field(name="Last Logged In:", value=(d), inline=True)
    embed.add_field(name="Last Logged Off:", value=(d1), inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    mostRecentGameType = data['player'].get('mostRecentGameType', "None").lower().capitalize()
    embed.add_field(name="Last Game Played:", value=(mostRecentGameType))
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    EXP = round(data['player'].get("networkExp", 0), 0)
    level = math.floor(1 + (-8750. + (8750**2 + 5000*EXP)**.5) / 2500)
    karma = data['player'].get("karma", 0)
    embed.add_field(name="EXP:", value=EXP, inline=True)
    embed.add_field(name="Level:", value=level, inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    embed.add_field(name="Karma:", value=karma, inline=True)
    friends = requests.get(f"https://api.hypixel.net/friends?key={HYPIXEL_KEY}&uuid={data['player']['uuid']}").json()
    friends = str(len(friends.get('records', [])))
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
    if data['player'].get("socialMedia") and data['player']['socialMedia'].get('links'):
        for link in data['player']['socialMedia']['links']:
            embed.add_field(name=link, value=data['player']['socialMedia']['links'][link], inline=False)

    await ctx.send(embed=embed)


EXP_NEEDED = [100000, 150000, 250000, 500000, 750000, 1000000, 1250000, 1500000, 2000000, 2500000, 2500000, 2500000, 2500000, 2500000, 3000000]

def getGuildLevel(exp):
    level = 0

    for i in range(1000):

        need = 0
        if  i >= len(EXP_NEEDED):
            need = EXP_NEEDED[len(EXP_NEEDED) - 1]
        else:
            need = EXP_NEEDED[i]

        if (exp - need) < 0:
            return math.floor(((level + (exp / need)) * 100) / 100)

        level += 1
        exp -= need

    return 1000

@bot.command()
async def hypixelguild(ctx, *player):
    player = hasLink(ctx, player)
    uuid = MojangAPI.get_uuid(player)
    if not uuid:
        raise commands.BadArgument(f'Player "{player}" not found.')
    id = requests.get(f"https://api.hypixel.net/findGuild?key={HYPIXEL_KEY}&byUuid={uuid}").json()
    guild = requests.get(f"https://api.hypixel.net/guild?key={HYPIXEL_KEY}&id={id['guild']}").json()
    if guild.get("success") is False:
        raise commands.BadArgument(f"{player} is not in a guild.")
    embed = discord.Embed(title=f"{guild['guild']['name']}'s Guild Profile",description=f"Guild stats for {guild['guild']['name']}", color=0xff0000)
    embed.set_thumbnail(url=f"https://crafatar.com/renders/head/{uuid}?overlay")
    embed.set_footer(text=f"Stats provided using the Mojang and Hypixel APIs \nAvatars from Crafatar \nStats requested by {str(ctx.author)}")
    embed.add_field(name="Guild:", value=guild['guild']['name'], inline=True)
    embed.add_field(name="ID:", value=len(guild['guild']['_id']), inline=True)
    embed.add_field(name="Members:", value=len(guild['guild']['members']), inline=True)
    embed.add_field(name="EXP:", value=guild['guild']['exp'], inline=True)
    embed.add_field(name="Level:", value=getGuildLevel(guild['guild']['exp']))
    embed.add_field(name="Public:", value=convertBooltoExpress(guild['guild'].get('publiclyListed')))
    embed.add_field(name="Winners:", value=guild['guild']['achievements']['WINNERS'])
    embed.add_field(name="Experience Kings:", value=guild['guild']['achievements']['EXPERIENCE_KINGS'])
    embed.add_field(name="Online Players:", value=guild['guild']['achievements']['ONLINE_PLAYERS'])
    for member in guild['guild']['members']:
        if member['uuid'] == uuid:
            embed.add_field(name="\u200b", value="\u200b", inline=False)
            embed.add_field(name="Player Stats:", value="\u200b", inline=False)
            embed.add_field(name="Rank", value=member['rank'])
            embed.add_field(name="Quest Participation", value=member.get('questParticipation', 0))
            return await ctx.send(embed=embed)


bedwarsModes = {("solos", "solo", "ones"): "eight_one", ("doubles", "double", "twos"): "eight_two", ("3s", "triples", "threes", "3v3v3v3"): "four_three", ("4s", "4v4v4v4", "quadruples", "fours"): "four_four", "4v4": "two_four"}

@bot.command(aliases=['bw'])
async def bedwars(ctx, *player_and_mode):
    if len(player_and_mode) == 0 or multi_key_dict_get(bedwarsModes, player_and_mode[0]) is not None:
        member = ctx.author
        if len(player_and_mode) == 1:
            player_and_mode = list(player_and_mode)
            player_and_mode.insert(0, "")
            player_and_mode = tuple(player_and_mode)
    elif ctx.message.mentions:
        member = ctx.message.mentions[0]
    else:
        member = None
        player = player_and_mode[0]
    if member:
        player = r.get(member.id)
        if not player:
            raise commands.BadArgument(f"{str(member)} has not linked their Discord to their Minecraft account")
        player = player.decode("utf-8")
    uuid = MojangAPI.get_uuid(player)
    if not uuid:
        raise commands.BadArgument(f'Player "{player}" not found.')
    rawData = requests.get(f"https://api.hypixel.net/player?key={HYPIXEL_KEY}&uuid={uuid}").json()
    if rawData.get("success") is False:
        raise commands.BadArgument(rawData.get('cause'))
    if not rawData.get('player') or not rawData['player'].get('stats') or not rawData['player']['stats'].get("Bedwars"):
        raise commands.BadArgument(f"{player} has not played Bedwars")
    data = rawData['player']['stats']['Bedwars']
    if len(player_and_mode) < 2:
            embed=discord.Embed(title=f"{rawData['player']['displayname']}'s Hypixel Bedwars Profile", description=f"Bedwars stats for {rawData['player']['displayname']}", color=0xff0000)
            embed.add_field(name="Coins:", value=data.get("coins", 0), inline=True)
            embed.add_field(name="EXP:", value=data.get("Experience", 0), inline=True)
            embed.add_field(name="Level:", value=rawData['player']['achievements'].get("bedwars_level", 0), inline=True)
            embed.add_field(name="Games Played:", value=data.get("games_played_bedwars", 0), inline=True)
            embed.add_field(name="Current Winstreak:", value=data.get("winstreak", 0), inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            embed.add_field(name="Wins:", value=data.get("wins_bedwars", 0), inline=True)
            embed.add_field(name="Losses:", value=data.get("losses_bedwars", 0), inline=True)
            embed.add_field(name="W/L Rate:", value=getrate(data.get('wins_bedwars', 0), data.get("losses_bedwars", 0)), inline=True)
            embed.add_field(name="Kills:", value=data.get("kills_bedwars", 0), inline=True)
            embed.add_field(name="Deaths:", value=data.get("deaths_bedwars", 0), inline=True)
            embed.add_field(name="K/D Rate:", value=getrate(data.get("kills_bedwars", 0), data.get("deaths_bedwars", 0)), inline=True)
            embed.add_field(name="Final Kills:", value=data.get("final_kills_bedwars", 0), inline=True)
            embed.add_field(name="Final Deaths:", value=data.get("final_deaths_bedwars", 0), inline=True)
            embed.add_field(name="Final K/D Rate:", value=getrate(data.get("final_kills_bedwars", 0), data.get("final_deaths_bedwars", 0)), inline=True)

            ceilingRate = math.ceil(getrate(data.get("final_kills_bedwars", 0), data.get("final_deaths_bedwars", 0)))
            total = ceilingRate * data.get("final_deaths_bedwars", 0)
            res = total - data.get("final_kills_bedwars", 0)

            embed.add_field(name=f"Final Kills needed for a Final K/D Rate of {ceilingRate}", value=f"{res} ({total} total)", inline=False)
            embed.add_field(name="Beds Broken:", value=data.get("beds_broken_bedwars", 0), inline=True)
            embed.add_field(name="Beds Lost:", value=data.get("beds_lost_bedwars", 0), inline=True)
            embed.add_field(name="B/L Rate:", value=getrate(data.get("beds_broken_bedwars", 0), data.get("beds_lost_bedwars", 0)), inline=True)
    else:
        mode = multi_key_dict_get(bedwarsModes, player_and_mode[1])
        if mode is None:
            raise commands.BadArgument("Invalid mode")
        embed = discord.Embed(title=f"{rawData['player']['displayname']}'s Hypixel {player_and_mode[1].capitalize()} Bedwars Profile", description=f"{player_and_mode[1].capitalize()} Bedwars stats for {rawData['player']['displayname']}", color=0xff0000)
        embed.add_field(name="Games Played:", value=data.get(f"{mode}_games_played_bedwars", 0), inline=True)
        embed.add_field(name="Current Winstreak:", value=data.get(f"{mode}_winstreak", 0), inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="Kills:", value=data.get(f"{mode}_kills_bedwars", 0), inline=True)
        embed.add_field(name="Deaths:", value=data.get(f"{mode}_deaths_bedwars", 0), inline=True)
        embed.add_field(name="K/D Rate:", value=getrate(data.get(f"{mode}_kills_bedwars", 0), data.get(f"{mode}_deaths_bedwars", 0)), inline=True)
        embed.add_field(name="Final Kills:", value=data.get(f"{mode}_final_kills_bedwars", 0), inline=True)
        embed.add_field(name="Final Deaths:", value=data.get(f"{mode}_final_deaths_bedwars", 0), inline=True)
        embed.add_field(name="Final K/D Rate:", value=getrate(data.get(f"{mode}_final_kills_bedwars", 0), data.get(f"{mode}_final_deaths_bedwars", 0)), inline=True)
        embed.add_field(name="Wins:", value=data.get(f"{mode}_wins_bedwars", 0), inline=True)
        embed.add_field(name="Losses:", value=data.get(f"{mode}_losses_bedwars", 0), inline=True)
        embed.add_field(name="W/L Rate", value=getrate(data.get(f"{mode}_wins_bedwars", 0), data.get(f"{mode}_losses_bedwars", 0)), inline=True)
        embed.add_field(name="Beds Broken:", value=data.get(f"{mode}_beds_broken_bedwars", 0), inline=True)
        embed.add_field(name="Beds Lost:", value=data.get(f"{mode}_beds_lost_bedwars", 0), inline=True)
        embed.add_field(name="B/L Rate:", value=getrate(data.get(f"{mode}_beds_broken_bedwars", 0), data.get(f"{mode}_beds_lost_bedwars", 0)), inline=True)
    embed.set_thumbnail(url=f"https://crafatar.com/renders/head/{rawData['player']['uuid']}?overlay")
    embed.set_footer(text=f"Stats provided using the Mojang and Hypixel APIs \nAvatars from Crafatar \nStats requested by {str(ctx.author)}")
    await ctx.send(embed=embed)


def write_roman(num : int):
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
    def roman_num(num : int):
        for r in roman.keys():
            x, y = divmod(num, r)
            yield roman[r] * x
            num -= (r * x)
            if num <= 0:
                break
    return "".join([a for a in roman_num(num)])

def getrate(stat1 : int, stat2 : int):
    try:
        return round(stat1/stat2, 2)
    except ZeroDivisionError:
        return 0

def getSkyWarsLevel(xp : int):
    if xp >= 15000:
        return (xp - 15000) / 10000. + 12
    else:
        for number in xps:
            if not xp > number:
                closestnumber = xps[xps.index(number)-1]
                break
        return math.floor(xps.index(closestnumber) + 1)

skywarsModes = {("solo normal", "solos normal"): "solos normal", ("solo insane", "solos insane"): "solos insane", ("teams normal", "team normal", "doubles normal", "double normal"): "teams normal", ("teams insane", "team insane", "doubles insane", "double insane"): "teams insane"}
xps = [0, 20, 70, 150, 250, 500, 1000, 2000, 3500, 6000, 10000, 15000]

@bot.command(aliases=["sw"])
async def skywars(ctx, *player_and_mode):
    mode = " ".join(player_and_mode)
    if len(player_and_mode) == 0 or multi_key_dict_get(skywarsModes, mode) is not None:
        member = ctx.author
        if len(player_and_mode) > 0:
            player_and_mode = list(player_and_mode)
            player_and_mode.insert(0, "")
            player_and_mode = tuple(player_and_mode)
    elif ctx.message.mentions:
        member = ctx.message.mentions[0]
    else:
        member = None
        player = player_and_mode[0]
    if member:
        player = r.get(member.id)
        if player is None:
            raise commands.BadArgument(f"{str(member)} has not linked their Discord to their Minecraft account")
        player = player.decode("utf-8")
    uuid = MojangAPI.get_uuid(player)
    if not uuid:
        raise commands.BadArgument(f'Player "{player}" not found.')
    rawData = requests.get(f"https://api.hypixel.net/player?key={HYPIXEL_KEY}&uuid={uuid}").json()
    if not rawData.get('player') or not rawData['player'].get('stats') or not   rawData['player']['stats'].get("SkyWars"):
        raise commands.BadArgument(f"{player} has not played SkyWars")
    data = rawData['player']['stats']['SkyWars']
    if len(player_and_mode) <= 1:
        embed=discord.Embed(title=f"{rawData['player']['displayname']}'s Hypixel Skywars Profile", description=f"Skywars stats for {rawData['player']['displayname']}", color=0xff0000)
        embed.add_field(name="Coins:", value=data.get('coins', 0), inline=True)
        embed.add_field(name="EXP:", value=data.get('skywars_experience', 0), inline=True)
        embed.add_field(name="Level:", value=getSkyWarsLevel(data.get('skywars_experience', 0)), inline=True)
        embed.add_field(name="Games Played:", value=data.get('wins', 0) + data.get('losses', 0), inline=True)
        embed.add_field(name="Current Winstreak:", value=data.get('win_streak', 0), inline=True)
        embed.add_field(name="Assists:", value=data.get('assists', 0), inline=True)
        embed.add_field(name="Kills:", value=data.get('kills', 0), inline=True)
        embed.add_field(name="Deaths:", value=data.get('deaths', 0), inline=True)
        embed.add_field(name="K/D Rate:", value=getrate(data.get('kills', 0), data.get('deaths', 0)), inline=True)
        embed.add_field(name="Wins:", value=data.get('wins', 0), inline=True)
        embed.add_field(name="Losses:", value=data.get('losses', 0), inline=True)
        embed.add_field(name="W/L Rate:", value=getrate(data.get('wins', 0), data.get('losses', 0)), inline=True)
    else:
        player_and_mode = list(player_and_mode)
        player_and_mode.pop(0)
        joinedmode = " ".join(player_and_mode)
        joinedmode = (multi_key_dict_get(skywarsModes, joinedmode))
        if joinedmode == "solos normal":
            embed = discord.Embed(title=f"{rawData['player']['displayname']}'s Hypixel Solos Normal Skywars Profile", description=f"Solo Normal Skywars stats for {rawData['player']['displayname']}", color=0xff0000)
            embed.add_field(name="EXP:", value=data.get('skywars_experience', 0), inline=True)
            embed.add_field(name="Level:", value=getSkyWarsLevel(data.get('skywars_experience', 0)), inline=True)
            embed.add_field(name="Games Played:", value=(data.get('wins_solo', 0) - data.get('losses', 0)) + (data.get('losses_solo', 0) - data.get('losses_solo_insane', 0)), inline=True)
            embed.add_field(name="Kills:", value=data.get('kills_solo', 0) - data.get('kills_solo_insane', 0), inline=True)
            embed.add_field(name="Deaths:", value=data.get('deaths_solo', 0) - data.get('deaths_solo_insane', 0), inline=True)
            embed.add_field(name="K/D Rate:", value=getrate(data.get('kills_solo', 0) - data.get('kills_solo_insane', 0), data.get('deaths_solo', 0) - data.get('deaths_solo_insane', 0)), inline=True)
            embed.add_field(name="Wins:", value=data.get('wins_solo', 0) - data.get('wins_solo_insane', 0), inline=True)
            embed.add_field(name="Losses:", value=data.get('losses_solo', 0) - data.get('losses_solo_insane', 0), inline=True)
            embed.add_field(name="W/L Rate:", value=getrate(data.get('wins_solo', 0) - data.get('wins_solo_insane', 0), data.get('losses_solo', 0) - data.get('losses_solo_insane', 0)), inline=True)
        elif joinedmode == "solos insane":
            embed = discord.Embed(title=f"{rawData['player']['displayname']}'s Hypixel Solos Insane Skywars Profile", description=f"Solo Insane Skywars stats for {rawData['player']['displayname']}", color=0xff0000)
            embed.add_field(name="EXP:", value=data.get('skywars_experience', 0), inline=True)
            embed.add_field(name="Level:", value=getSkyWarsLevel(data.get('skywars_experience', 0)), inline=True)
            embed.add_field(name="Games Played:", value=data.get('wins_solo_insane', 0) + data.get('losses_solo_insane', 0), inline=True)
            embed.add_field(name="Kills:", value=data.get('kills_solo_insane', 0), inline=True)
            embed.add_field(name="Deaths:", value=data.get('deaths_solo_insane', 0), inline=True)
            embed.add_field(name="K/D Rate:", value=getrate(data.get("kills_solo_insane", 0), data.get("deaths_solo_insane", 0)), inline=True)
            embed.add_field(name="Wins:", value=data.get("wins_solo_insane", 0), inline=True)
            embed.add_field(name="Losses:", value=data.get("losses_solo_insane", 0), inline=True)
            embed.add_field(name="W/L Rate:", value=getrate(data.get("wins_solo_insane", 0), data.get("losses_solo_insane", 0)), inline=True)
        elif joinedmode == "teams normal":
            embed = discord.Embed(title=f"{rawData['player']['displayname']}'s Hypixel Teams Normal Skywars Profile", description=f"Teams Normal Skywars stats for {rawData['player']['displayname']}", color=0xff0000)
            embed.add_field(name="EXP:", value=data.get("skywars_experience", 0), inline=True)
            embed.add_field(name="Level:", value=getSkyWarsLevel(data.get("skywars_experience", 0)), inline=True)
            embed.add_field(name="Games Played:", value=(data.get("wins_team", 0) - data.get("wins_team_insane", 0)) + (data.get("losses_team", 0) - data.get("losses_team_insane", 0)), inline=True)
            embed.add_field(name="Kills:", value=data.get("kills_team", 0) - data.get("kills_team_insane", 0), inline=True)
            embed.add_field(name="Deaths:", value=data.get("deaths_team", 0) - data.get("deaths_team_insane", 0), inline=True)
            embed.add_field(name="K/D Rate:", value=getrate(data.get("kills_team", 0) - data.get("kills_team_insane", 0), data.get("deaths_team", 0) - data.get("deaths_team_insane", 0)), inline=True)
            embed.add_field(name="Wins:", value=data.get("wins_team", 0) - data.get("wins_team_insane", 0), inline=True)
            embed.add_field(name="Losses:", value=data.get("losses_team", 0) - data.get("losses_team_insane", 0), inline=True)
            embed.add_field(name="W/L Rate:", value=getrate(data.get("wins_team", 0) - data.get("wins_team_insane", 0), data.get("losses_team", 0) - data.get("losses_team_insane", 0)), inline=True)
        elif joinedmode == "teams insane":
            embed = discord.Embed(title=f"{rawData['player']['displayname']}'s Hypixel Teams Insane Skywars Profile", description=f"Teams Insane Skywars stats for {rawData['player']['displayname']}", color=0xff0000)
            embed.add_field(name="EXP:", value=data.get('skywars_experience', 0), inline=True)
            embed.add_field(name="Level:", value=getSkyWarsLevel(data.get("skywars_experience", 0)), inline=True)
            embed.add_field(name="Games Played:", value=data.get("wins_team_insane", 0) + data.get("losses_team_insane", 0), inline=True)
            embed.add_field(name="Kills:", value=data.get("kills_team_insane", 0), inline=True)
            embed.add_field(name="Deaths:", value=data.get("deaths_team_insane", 0), inline=True)
            embed.add_field(name="K/D Rate:", value=getrate(data.get("kills_team_insane", 0), data.get("deaths_team_insane", 0)), inline=True)
            embed.add_field(name="Wins:", value=data.get("wins_team_insane", 0), inline=True)
            embed.add_field(name="Losses:", value=data.get("losses_team_insane", 0), inline=True)
            embed.add_field(name="W/L Rate:", value=getrate(data.get("wins_team_insane", 0), data.get("losses_team_insane", 0)), inline=True)
        else:
            raise commands.BadArgument("Invalid mode")
    embed.set_thumbnail(url=f"https://crafatar.com/renders/head/{rawData['player']['uuid']}?overlay")
    embed.set_footer(text=f"Stats provided using the Mojang and Hypixel APIs \nAvatars from Crafatar \nStats requested by {str(ctx.author)}")
    await ctx.send(embed=embed)


duelModes = {"classic": "classic_duel", "uhc": "uhc_duel", "op": "op_duel", "combo": "combo_duel", "skywars": "sw_duel", "sumo": "sumo_duel", "uhc doubles": "uhc_doubles", "bridge": "bridge",}
ranks = ['godlike', 'grandmaster', 'legend', 'master', 'diamond', 'gold', 'iron', 'rookie']

@bot.command()
async def duels(ctx, *player_and_mode):
    prestige = None
    mode = " ".join(player_and_mode)
    if len(player_and_mode) == 0 or multi_key_dict_get(duelModes, mode) is not None:
        member = ctx.author
        if len(player_and_mode) > 0:
            player_and_mode = list(player_and_mode)
            player_and_mode.insert(0, "")
            player_and_mode = tuple(player_and_mode)
    elif ctx.message.mentions:
        member = ctx.message.mentions[0]
    else:
        member = None
        player = player_and_mode[0]
    if member:
        player = r.get(member.id)
        if player is None:
            raise commands.BadArgument(f"{str(member)} has not linked their Discord to their Minecraft account")
        player = player.decode("utf-8")
    uuid = MojangAPI.get_uuid(player)
    if not uuid:
        raise commands.BadArgument(f'Player "{player}" not found.')
    rawData = requests.get(f"https://api.hypixel.net/player?key={HYPIXEL_KEY}&uuid={uuid}").json()
    if rawData.get("success") is False:
        raise commands.BadArgument(f"Hypixel API returned an error: {rawData.get('cause')}")
    if not rawData.get('player') or not rawData['player'].get('stats') or not rawData['player']['stats'].get('Duels'):
        raise commands.BadArgument(f"{player} has not played Duels")
    data = rawData['player']['stats']['Duels']
    if len(player_and_mode) < 2:
        embed=discord.Embed(title=f"{rawData['player']['displayname']}'s Hypixel Duels Profile", description=f"Duels stats for {rawData['player']['displayname']}", color=0xff0000)
        mode = "all_modes"
        for ra in ranks:
            prestigeNumber = data.get(f'{mode}_{ra}_title_prestige', None)
            if prestigeNumber:
                if ra == "rookie" and prestigeNumber == 1:
                    break
                prestige = f'{ra.capitalize()} {write_roman(prestigeNumber)}'
                break
        embed.add_field(name="Games Played:", value=data.get('wins', 0) + data.get('losses', 0), inline=True)
        embed.add_field(name="Winstreak:", value=data.get('current_winstreak', 0), inline=True)
        embed.add_field(name="Best Winstreak:", value=data.get('best_overall_winstreak', 0), inline=True)
        embed.add_field(name="Coins:", value=data.get('coins', 0), inline=True)
        embed.add_field(name="Prestige:", value=prestige, inline=True)
        embed.add_field(name="\u200b", value="\u200b")
        embed.add_field(name="Kills:", value=data.get('kills', 0), inline=True)
        embed.add_field(name="Deaths:", value=data.get('deaths', 0), inline=True)
        embed.add_field(name="K/D Rate:", value=getrate(data.get('kills', 0), data.get('deaths', 0)), inline=True)
        embed.add_field(name="Wins:", value=data.get('wins', 0), inline=True)
        embed.add_field(name="Losses:", value=data.get('losses', 0), inline=True)
        embed.add_field(name="W/L Rate:", value=getrate(data.get('wins', 0), data.get('losses', 0)), inline=True)
        embed.add_field(name="Arrows Shot:", value=data.get('bow_shots', 0), inline=True)
        embed.add_field(name="Arrows Hit:", value=data.get('bow_hits', 0), inline=True)
        embed.add_field(name="Arrows Missed:", value=data.get('bow_shots', 0) - data.get('bow_hits', 0), inline=True)
        embed.add_field(name="Arrow H/S Rate:", value=getrate(data.get('bow_hits', 0), data.get('bow_shots', 0)), inline=False)
        embed.add_field(name="Melee Swings:", value=data.get('melee_swings', 0), inline=True)
        embed.add_field(name="Melee Hits:", value=data.get('melee_hits', 0), inline=True)
        embed.add_field(name="Melee Missed:", value=data.get('melee_swings', 0) - data.get('melee_hits', 0), inline=True)
        embed.add_field(name="Melee H/S Rate:", value=getrate(data.get('melee_hits', 0), data.get('melee_swings', 0)), inline=True)
    else:
        player_and_mode = list(player_and_mode)
        player_and_mode.pop(0)
        mode = " ".join(player_and_mode)
        if not mode in duelModes:
            raise commands.BadArgument(f'Mode "{mode}" not found.')
        embed = discord.Embed(title=f"{rawData['player']['displayname']}'s Hypixel {mode.capitalize()} Duel Profile", description=f"{mode.capitalize()} duel stats for {rawData['player']['displayname']}", color=0xff0000)
        for ra in ranks:
            prestigeNumber = data.get(f'{mode.split()[0]}_{ra}_title_prestige', None)
            if prestigeNumber:
                if ra == "rookie" and prestigeNumber == 1:
                    break
                prestige = f'{ra.capitalize()} {write_roman(prestigeNumber)}'
                break
        mode = duelModes[mode]
        embed.add_field(name="Prestige", value=prestige, inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="Kills:", value=data.get(f'{mode}_kills', 0), inline=True)
        embed.add_field(name="Deaths:", value=data.get(f'{mode}_deaths', 0), inline=True)
        embed.add_field(name="K/D Rate:", value=getrate(data.get(f'{mode}_kills', 0), data.get(f'{mode}_deaths', 0)), inline=True)
        if mode == "bridge":
            mode = "bridge_duel"
        embed.add_field(name="Wins:", value=data.get(f'{mode}_wins', 0), inline=True)
        embed.add_field(name="Losses:", value=data.get(f'{mode}_losses', 0), inline=True)
        embed.add_field(name="W/L Rate:", value=getrate(data.get(f'{mode}_wins', 0), data.get(f'{mode}_losses', 0)), inline=True)
    embed.set_thumbnail(url=f"https://crafatar.com/renders/head/{rawData['player']['uuid']}?overlay")
    embed.set_footer(text=f"Stats provided using the Mojang and Hypixel APIs \nAvatars from Crafatar \nStats requested by {str(ctx.author)}")
    await ctx.send(embed=embed)


@bot.command()
async def fortnite(ctx, player):
    player = player.replace(" ", "%20")
    data = requests.get(f"https://fortnite-api.com/v1/stats/br/v2?name={player}").json()
    if data['status'] != 200:
        raise commands.BadArgument(f'Player "{player}" not found.')
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
    if not user.get('data'):
        raise commands.ChannelNotFound(channel)
    data = (user['data'])[0]
    embed = discord.Embed(title=f"{data['display_name']}'s' Twitch Stats", description=f"https://twitch.tv/{channel}", color=0xff0000)
    embed.set_thumbnail(url=data['profile_image_url'])
    embed.add_field(name="Username:", value=data['display_name'], inline=True)
    embed.add_field(name="Login Name:", value=data['login'], inline=True)
    embed.add_field(name="ID", value=data['id'], inline=True)
    channelType = data['broadcaster_type'].capitalize()
    if not channelType:
        channelType = "None"
    embed.add_field(name="Channel Type", value=channelType, inline=False)
    description = data['description']
    if not description:
        description = "None"
    embed.add_field(name="Channel Description", value=description, inline=False)
    embed.add_field(name="Views", value=data['view_count'], inline=True)
    followers = requests.get(f"https://api.twitch.tv/helix/users/follows?to_id={data['id']}", headers={"client-id":f"{TWITCH_CLIENT_ID}", "Authorization":f"{TWITCH_AUTH}"}).json()
    embed.add_field(name="Followers", value=followers['total'], inline=True)
    await ctx.send(embed=embed)


async def checkIfLive():
    while True:
        for guild in trackingGuilds:
            for track in trackingGuilds[guild]:
                    index = trackingGuilds[guild].index(track)
                    data = requests.get(f'https://api.twitch.tv/helix/search/channels?query={trackingGuilds[guild][index]["streamer"]}/', headers={"client-id":TWITCH_CLIENT_ID, "Authorization": TWITCH_AUTH}).json()
                    x = list(data['data'])[0]
                    is_live = x['is_live']
                    if is_live:
                        if trackingGuilds[guild][index]['pinged'] == "False":
                            embed = discord.Embed(title=trackingGuilds[guild][index]['message'], description=f"https://twitch.tv/{trackingGuilds[guild][index]['streamer']}", color=0xff0000)
                            embed.set_thumbnail(url=x['thumbnail_url'])
                            embed.add_field(name=x['title'], value="\u200b", inline=False)
                            guildSend = bot.get_guild(guild)
                            channel = guildSend.get_channel(trackingGuilds[guild][index]['channel-id'])
                            await channel.send(embed=embed)
                            trackingGuilds[guild][index]['pinged'] = "True"
                    else:
                        trackingGuilds[guild][index]['pinged'] = "False"
        rval = json.dumps(trackingGuilds)
        r.set("trackingGuilds", rval)
        await asyncio.sleep(60)


@bot.command()
async def twitchtrack(ctx, channel, *, message):
    user = requests.get(f"https://api.twitch.tv/helix/users?login={channel}", headers={"client-id":f"{TWITCH_CLIENT_ID}", "Authorization":f"{TWITCH_AUTH}"}).json()
    if not user:
        raise commands.ChannelNotFound(channel)
    x = (user['data'])[0]
    trackingGuilds[ctx.guild.id].append({})
    index = len(trackingGuilds[ctx.guild.id]) - 1
    trackingGuilds[ctx.guild.id][index]['channel-id'] = ctx.channel.id
    trackingGuilds[ctx.guild.id][index]['streamer'] = channel
    trackingGuilds[ctx.guild.id][index]['pinged'] = "False"
    trackingGuilds[ctx.guild.id][index]['message'] = message
    embed = discord.Embed(title=f"THIS IS AN EXAMPLE STREAM: {trackingGuilds[ctx.guild.id][index]['message']}", description=f"https://twitch.tv/{trackingGuilds[ctx.guild.id][index]['streamer']}", color=0xff0000)
    embed.set_thumbnail(url=x['profile_image_url'])
    embed.add_field(name="This is an example stream", value="\u200b", inline=False)
    channelSend = ctx.guild.get_channel(trackingGuilds[ctx.guild.id][index]["channel-id"])
    await channelSend.send(embed=embed)
    rval = json.dumps(trackingGuilds)
    r.set("trackingGuilds", rval)


def findTwitchTrack(ctx, streamer):
    for track in trackingGuilds[ctx.guild.id]:
        if trackingGuilds[ctx.guild.id][trackingGuilds[ctx.guild.id].index(track)]['streamer'] == streamer:
            return trackingGuilds[ctx.guild.id].index(track)
    return None

@bot.command()
async def deltrack(ctx, *, streamer):
    track = findTwitchTrack(ctx, streamer)
    if track is None:
        raise commands.ChannelNotFound(channel)
    trackingGuilds[ctx.guild.id].pop(track)
    await ctx.send(f"No longer tracking {streamer}")
    rval = json.dumps(trackingGuilds)
    r.set("trackingGuilds", rval)


@bot.command()
async def twitchtracklist(ctx):
    embed = discord.Embed(title=f"All Twitch Tracks in {ctx.guild.name}", description=None, color=0xff0000)
    for track in trackingGuilds[ctx.guild.id]:
        index = trackingGuilds[ctx.guild.id].index(track)
        embed.add_field(name=trackingGuilds[ctx.guild.id][index]['streamer'], value=f"Tracking to channel: {ctx.guild.get_channel(trackingGuilds[ctx.guild.id][index]['channel-id'])}")
    await ctx.send(embed=embed)


@bot.command(aliases=['yt'])
async def youtube(ctx, *, channel):
    channel = channel.replace(" ", "%20")
    data = requests.get(f"https://youtube.googleapis.com/youtube/v3/search?part=snippet&q={channel}&type=channel&key={YT_KEY}").json()
    errors = data.get('error')
    if errors:
        raise commands.BadArgument("YouTube returned an error!")
    if not data.get('items'):
        raise commands.ChannelNotFound(channel)
    channel_id = data['items'][0]['snippet']['channelId']
    stats = requests.get(f"https://www.googleapis.com/youtube/v3/channels?part=statistics&id={channel_id}&key={YT_KEY}").json()
    embed = discord.Embed(title=f"YouTube statistics for {data['items'][0]['snippet']['title']}", description=f"https://www.youtube.com/channel/{channel_id}", color=0xff0000)
    embed.add_field(name="Channel Name:", value=data['items'][0]['snippet']['title'], inline=True)
    embed.add_field(name="Channel ID:", value=channel_id, inline=True)
    description = (data['items'][0]['snippet'])['description']
    if not description:
        description = "None"
    embed.add_field(name="Channel Description:", value=description, inline=False)
    embed.add_field(name="Views:", value=stats['items'][0]['statistics']['viewCount'], inline=True)
    embed.add_field(name="Subscribers:", value=stats['items'][0]['statistics']['subscriberCount'], inline=True)
    embed.add_field(name="Videos:", value=stats['items'][0]['statistics']['videoCount'], inline=True)
    embed.set_thumbnail(url=(data['items'][0])['snippet']['thumbnails']['default']['url'])
    embed.set_footer(text=f"Stats provided by the YouTube API \nNot the Youtuber your looking for? Type 'see more' to see more {channel.replace('%20', ' ')}s and then run '?youtube (id_of_the_channel_you_want)'")
    await ctx.send(embed=embed)

    def ytCheck(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content == "see more"
    try:
        seemore = await bot.wait_for('message', timeout=30, check=ytCheck)
    except asyncio.TimeoutError:
        return
    for item in data['items']:
        if item != data['items'][0]:
            embed = discord.Embed(title=f"YouTube statistics for {item['snippet']['title']}", description=f"https://www.youtube.com/channel/{item['snippet']['channelId']}", color=0xff0000)
            embed.add_field(name="Name:", value=item['snippet']['title'], inline=True)
            embed.add_field(name="ID:", value=item['snippet']['channelId'], inline=True)
            description = item['snippet']['description']
            if not description:
                description = "None"
            embed.add_field(name="Description:", value=description, inline=True)
            embed.set_thumbnail(url=item['snippet']['thumbnails']['default']['url'])
            await ctx.send(embed=embed)


@bot.command()
async def csgolink(ctx, id):
    rawData = requests.get(f"https://public-api.tracker.gg/v2/csgo/standard/profile/steam/{id}", headers={"TRN-Api-Key": TRN_API_KEY}).json()
    data = rawData.get('data')
    if not data:
        raise commands.BadArgument(rawData['errors'][0]['message'])
    await ctx.send(f"{str(ctx.author)} is now linked to {data['platformInfo']['platformUserHandle']} \n**NOTE: There is no way to verify you are actually {data['platformInfo']['platformUserHandle']}, this is purely for convenience so you do not have to memorize your ID**")
    csgoLinks[ctx.author.id] = data['platformInfo']['platformUserId']
    rval = json.dumps(csgoLinks)
    r.set("csgoLinks", rval)


@bot.command()
async def csgo(ctx, *player):
    if len(player) == 0:
        member = ctx.author.id
    elif ctx.message.mentions:
        member = ctx.message.mentions[0].id
    else:
        member = None
        player = player[0]
    if member:
        player = csgoLinks.get(member)
        if not player:
            raise commands.BadArgument(f"There is no CS:GO ID linked to {str(ctx.guild.get_member(member))}. Run ?csgolink")
    rawData = requests.get(f"https://public-api.tracker.gg/v2/csgo/standard/profile/steam/{player}", headers={"TRN-Api-Key": TRN_API_KEY}).json()
    data = rawData.get('data')
    if not data:
        raise commands.BadArgument(rawData['errors'][0]['message'])
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




if len(sys.argv) < 2 or not sys.argv[1] in keys:
    raise Exception("Invalid Arguments")

bot.run(globals()[sys.argv[1]])
