from utils import utils, constants
from utils.constants import r, emojis, Converters

import discord
from discord.ext import commands
from discord.utils import get

from PIL import Image
from io import BytesIO

from googletrans import Translator
from googletrans.constants import LANGUAGES

from PyDictionary import PyDictionary

import datetime as dtime
from datetime import datetime


class Misc(commands.Cog, description="Miscellaneous Commands"):
    def __init__(self, bot):
        self.bot = bot
        self.bot.help_command.cog = self
        self.stopWatches = {}
        print("Loaded", __name__)


    @commands.command(help="Unpins all messages in a channel")
    @commands.has_guild_permissions(manage_messages=True)
    @commands.bot_has_guild_permissions(manage_messages=True)
    async def unpinall(self, ctx):
        pins = await ctx.channel.pins()
        await ctx.reply(f"Are you sure you want me too unpin all {len(pins)} messages? (y/n)")
        def check(m):
            responses = ['y', 'n']
            return ctx.author == m.author and ctx.channel == m.channel and msg.content in responses
        msg = await self.bot.wait_for('message', timeout=60.0, check=check)
        if msg.content == "y":
            for message in pins:
                await message.unpin()
            await ctx.reply(f"Unpinned all messages")
        elif msg.content == "n":
            await ctx.reply("Cancelled")


    @commands.command(help="Changes server-specific configurations")
    async def settings(self, ctx, *setting):
        guildInfo = utils.loadGuildInfo()

        if len(setting) == 0:
            embed = discord.Embed(title=f"Settings for {ctx.guild.name}", description=f"To edit a setting use '{utils.determine_prefix(ctx.bot, ctx, clean=True)}settings (setting) (on/off, 1/2/3, etc)", color=constants.RED)
            embed.add_field(name=f"Anti-Ez: `{utils.convertBooltoStr(guildInfo[ctx.guild.id]['antiez'])}`", value=f"{utils.determine_prefix(ctx.bot, ctx, clean=True)}settings antiez on/off")
            embed.add_field(name=f"Maximum members allowed on one team: `{guildInfo[ctx.guild.id]['teamLimit']}`", value=f"{utils.determine_prefix(ctx.bot, ctx, clean=True)}settings teamlimit 1/2/3...")
            embed.add_field(name=f"Role required to use speak (Text to Voice Channel): `{guildInfo[ctx.guild.id]['TTVCrole']}`", value=f"{utils.determine_prefix(ctx.bot, ctx, clean=True)}settings TTVCrole some_role")
            embed.add_field(name=f"Prefix for {str(self.bot.user)} in this server: `{utils.determine_prefix(ctx.bot, ctx, clean=True)}`", value=f"{utils.determine_prefix(ctx.bot, ctx, clean=True)}settings prefix some_prefix")

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
                embed = discord.Embed(title=f"Anti-EZ is now {utils.convertBooltoStr(guildInfo[ctx.guild.id]['antiez'])}", color=constants.RED)

            elif setting[0] == "teamlimit":
                try:
                    setting = int(setting[1])
                except ValueError:
                    raise commands.BadArgument("Argument must be a number")
                guildInfo[ctx.guild.id]['teamLimit'] = setting
                embed = discord.Embed(title=f"Maximum members allowed in one team is now {guildInfo[ctx.guild.id]['teamLimit']}", color=constants.RED)

            elif setting[0] == "TTVCrole":
                if setting[1] == "everyone":
                    setting1 = "@everyone"
                else:
                    setting1 = setting[1]
                if not get(ctx.guild.roles, name=setting1):
                    raise commands.RoleNotFound(setting1)
                guildInfo[ctx.guild.id]['TTVCrole'] = setting1
                embed = discord.Embed(title=f"TTVC Role is now set to {guildInfo[ctx.guild.id]['TTVCrole']}", color=constants.RED)

            elif setting[0] == "prefix":
                guildInfo[ctx.guild.id]['prefix'] = setting[1]
                embed = discord.Embed(title=f"Prefix for {str(self.bot.user)} in {ctx.guild.name} is now {guildInfo[ctx.guild.id]['prefix']}")

            else:
                raise commands.BadArgument(f'Setting "{setting[0]}" not found.')
            utils.saveData("guildInfo", guildInfo)

        else:
            raise commands.BadArgument("Invalid arguments")

        await ctx.reply(embed=embed)


    @commands.command(help="Uses Google Translate to translate a message into English")
    async def translate(self, ctx, *, message):
        embed = discord.Embed(title=f'Translation of "{message}"', color=constants.RED)
        translation = Translator().translate(message, dest='en')
        embed.add_field(name=LANGUAGES[translation.src.lower()].capitalize(), value=message, inline=False)
        embed.add_field(name=LANGUAGES[translation.dest].capitalize(), value=translation.text, inline=False)
        await ctx.send(embed=embed)


    @commands.command(help="Returns the definition of a word")
    async def define(self, ctx, word):
        embed = discord.Embed(title=f"Definition of '{word}'", color=constants.RED)
        meanings = PyDictionary().meaning(word)

        if not meanings:
            raise commands.BadArgument(f"Could not find a defintion for '{word}'")

        for item in meanings:
            message = ""
            for meaning in meanings[item]:
                message += f"\n{meaning}"
            embed.add_field(name=item, value=message, inline=False)
        await ctx.send(embed=embed)


    @commands.command(description="Arguments can be left blank or max_age (an integer), max_uses (an integer in seconds), and reason", help="Generates an invite to the current text channel")
    @commands.has_guild_permissions(create_instant_invite=True)
    @commands.bot_has_guild_permissions(create_instant_invite=True)
    async def invite(self, ctx, max_age=0, max_uses=0, reason=None):
        inviteLink = await ctx.channel.create_invite(max_age=max_age, max_uses=max_uses, reason=reason)

        if max_age == 0:
            max_age = "infinite"
        else:
            max_age = dtime.timedelta(seconds=max_age)

        if max_uses == 0:
            max_uses = "infinite"

        await ctx.reply(f"Created invite with a maximum age of {max_age}, {max_uses} maximum uses, and with reason: {reason}. \n{inviteLink}")


    @commands.command(description="member_or_role can be the name, id, or mention of a role or member", help="Returns the permissions for a role of member in the current server")
    @commands.guild_only()
    async def perms(self, ctx, member_or_role=None):
        def convertPermtoEmoji(member, perm, permissions):
            if getattr(permissions, perm) == True:
                return "✅"
            elif getattr(permissions, perm) == False:
                return "❌"

        if member_or_role == None:
            member_or_role = ctx.author
        else:
            try:
                member_or_role = await Converters.RoleConverter.convert(ctx, member_or_role)
            except commands.RoleNotFound:
                member_or_role = await Converters.MemberConverter.convert(ctx, member_or_role)


        embed = discord.Embed(title=f"Perms for {str(member_or_role)} in {ctx.guild.name}", color=constants.RED)

        if type(member_or_role) == discord.Member:
            permissions = member_or_role.guild_permissions

        elif type(member_or_role) == discord.Role:
            permissions = member_or_role.permissions

        for perm in permissions:
            embed.add_field(name=perm[0].replace('_', ' ').title(), value=convertPermtoEmoji(member_or_role, perm[0], permissions))

        await ctx.reply(embed=embed)


    @commands.command(description="<user> can be the name, id, or mention of a Discord user", help="Returns the profile picture of a Discord user", aliases=['pfp', 'profile'])
    async def avatar(self, ctx, *user : discord.User):
        user = ctx.author if not user else user[0]
        await ctx.reply(user.avatar_url)


    @commands.command(description="<emoji> can be the name, or id of an emoji", help="Returns a CDN of an emoji")
    async def emoji(self, ctx, emoji : discord.Emoji):
        await ctx.reply(emoji.url)


    @commands.command(help="Creates a new emoji from an image URL")
    @commands.bot_has_guild_permissions(manage_emojis=True)
    @commands.has_guild_permissions(manage_emojis=True)
    async def addemoji(self, ctx, emojiName, url):
        if len(ctx.guild.emojis) == ctx.guild.emoji_limit:
            raise commands.BadArgument("Max numbers of emojis has been reached")

        response = await utils.getJSON(url, json=False, read=True)
        img = BytesIO(response)
        try:
            emoji = await ctx.guild.create_custom_emoji(name=emojiName, image=img.read())
        except discord.HTTPException as error:
            raise commands.BadArgument(error.text)

        await ctx.reply(f"Created {emojiName}: \n{emoji}")


    @commands.command(description="Poll must have more than 2 options and less than 8 options \nPoll title must be less than 256 characters", help="Creates a poll where users can only vote once")
    @commands.bot_has_guild_permissions(add_reactions=True, manage_messages=True)
    async def poll(self, ctx, poll, *options):
        if len(options) > 8:
            raise commands.BadArgument("Maximum of 8 options")
        if len(options) < 2:
            raise commands.BadArgument("Minimum of 2 options")

        try:
            embed = discord.Embed(title=poll, color=constants.RED)
        except discord.HTTPException:
            raise commands.BadArgument("Poll title must be less than 256 characters")

        for option in options:
            embed.add_field(name=emojis[options.index(option)], value="\u200b", inline=True)
            embed.add_field(name=option, value="\u200b", inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)

        embed.set_footer(text=f"Poll by {str(ctx.author)}")
        msg = await ctx.send(embed=embed)
        await ctx.message.delete()
        for i in range(0, len(options)):
            await msg.add_reaction(emojis[i])


    @commands.command(description="You can only close your own poll", help="Closes a poll tallying the results and preventing anymore votes", enabled=False, hidden=True)
    @commands.bot_has_guild_permissions(add_reactions=True, manage_messages=True)
    async def closepoll(self, ctx):
        def closePollCheck(reaction, user):
            return user == ctx.author and str(reaction) == "❌"
        close = await ctx.reply("React to the poll I must close with an ❌")
        reaction, user = await self.bot.wait_for('reaction_add', timeout=120.0, check=closePollCheck)
        dic = reaction.message.embeds[0].to_dict()

        footer = dic['footer']['text']
        footer = footer[8:]
        title = f"(closed) {dic['title']}"
        if str(user) == footer:
            embed = discord.Embed(title=title, color=constants.RED)
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
                    x += 1
            await reaction.message.edit(embed=embed)
            await reaction.remove(user)
        else:
            raise commands.BadArgument(f"Only {dic} can close that poll")


    @commands.command(description="<member> can be the name, id, or mention of a member \nNickname must be fewer than 32 characters", help="Changes a member's nickname")
    @commands.bot_has_guild_permissions(manage_nicknames=True)
    @commands.has_permissions(manage_nicknames=True)
    async def nick(self, ctx, member : discord.Member, nick=None):
        oldNick = member.display_name

        if nick:
            nick = " ".join(nick)

        try:
            await member.edit(nick=nick)

        except discord.Forbidden:
            raise commands.BadArgument(f"Could not change {member.mention}'s nickname because their highest role is higher than mine.")
        except discord.HTTPException:
            raise commands.BadArgument("Nickname must be fewer than 32 characters")


        await ctx.reply(f"Changed {member.mention}'s nickname from {oldNick} to {member.display_name}")


    @commands.command(description="For accurate ping readings, this is ratelimited to 1 use every 5 seconds per guild", help="Checks GamerBot's Ping")
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def ping(self, ctx):
        t = await ctx.reply("Pong!")
        await t.edit(content=f'Pong! `{(t.created_at-ctx.message.created_at).total_seconds() * 1000}ms`')


    @commands.command(description="<member> can be the name, id, or mention of a member", help="Quotes a member")
    @commands.bot_has_guild_permissions(manage_webhooks=True, manage_messages=True)
    async def quote(self, ctx, member : discord.Member, *, message):
        webhook = get(await ctx.channel.webhooks(), name="quotebot")
        if not webhook:
            webhook = await ctx.channel.create_webhook(name="quotebot")
        await webhook.send(message, username=member.display_name, avatar_url=member.avatar_url)
        await ctx.message.delete()


    @commands.command(help="Reports a problem to GamerBot Support")
    @commands.cooldown(1, 600, commands.BucketType.guild)
    async def report(self, ctx):
        def check(m):
            return m.channel == ctx.channel and m.author == ctx.author
        await ctx.reply("Please write your message as to what errors/problems you are experiencing. This will timeout in 3 minutes")
        message = await self.bot.wait_for('message', timeout=180, check=check)
        embed = discord.Embed(title="Report", color=constants.RED)
        embed.add_field(name="Guild Name:", value=ctx.guild.name, inline=True)
        embed.add_field(name="Guild ID:", value=ctx.guild.id, inline=True)
        embed.add_field(name="Guild Owner:", value=ctx.guild.owner.mention, inline=True)
        embed.add_field(name="Channel:", value=ctx.channel.mention, inline=True)
        embed.add_field(name="Time:", value=utils.UTCtoZone(ctx.message.created_at, ctx.guild.region))
        embed.add_field(name="Reporter:", value=ctx.author.mention, inline=True)
        embed.add_field(name="Report:", value=message.content, inline=False)
        await ctx.reply("Your report is submitted", embed=embed)
        await utils.sendReport(ctx, "Report", embed=embed)


    @commands.command(help="Starts a stopwatch if there is no active one")
    async def starttimer(self, ctx):
        if self.stopWatches.get(ctx.author.id):
            raise commands.BadArgument("Stop watch already in use")
        await ctx.reply("Starting stopwatch")
        self.stopWatches[ctx.author.id] = datetime.utcnow()


    @commands.command(help="Stops a stopwatch if there is an active one")
    async def stoptimer(self, ctx):
        startTime = self.stopWatches.get(ctx.author.id)
        if not startTime:
            raise commands.BadArgument("No active stopwatches")
        seconds = (datetime.utcnow() - startTime).total_seconds()
        await ctx.reply(f"Ended timer. Timer ran for: {datetime.timedelta(seconds=seconds)}")
        del self.stopWatches[ctx.author.id]


    @commands.command(description="Message must include ATLEAST one member or role mention to DM", help="DMs members or all members with a role")
    @commands.has_guild_permissions(administrator=True)
    async def dm(self, ctx, *, message):
        if not ctx.message.role_mentions and not ctx.message.mentions:
            raise commands.BadArgument("No members or roles provided")

        dmedMessage = "Succesfully DMed:"

        for role in ctx.message.role_mentions:
            dmedMessage += f"\nAll members with {role.name}"
            for member in role.members:
                dm = await member.create_dm()
                await dm.send(message)
        for member in ctx.message.mentions:
            dmedMessage += f"\n{member.mention}"
            dm = await member.create_dm()
            await dm.send(message)

        await ctx.reply(dmedMessage)


    @commands.command(description="<member> can be the name, id, or mention of a member or 'bot'", help="Starts a game of rock, paper, scissors with a member or GamerBot")
    async def rps(self, ctx, member):
        moves = ["rock", "paper", "scissors"]

        if member == "bot":
            def rpsBotCheck(m):
                return m.author == ctx.author and m.channel == ctx.channel and m.content in moves
            await ctx.reply("Please choose from `rock`, `paper`, or `scissors`")
            move1 = await self.bot.wait_for('message', timeout=60.0, check=rpsBotCheck)
            botmove = random.choice(moves)
            move2 = await ctx.reply(botmove)

        else:
            def rpsCheck2(m):
                return m.author == member and m.guild == None and m.content in moves
            def rpsCheck1(m):
                return m.author == ctx.author and m.guild == None and m.content in moves

            member = await Converters.MemberConverter.convert(ctx, member)
            await ctx.send(f"{member.mention}! {ctx.author.mention} challenges you to rock paper scissors!")

            await ctx.reply(f"{ctx.author.mention} DM me your move")

            dm = await ctx.author.create_dm()
            await dm.send("Please choose from `rock`, `paper`, or `scissors`")

            move1 = await self.bot.wait_for('message', timeout=60.0, check=rpsCheck1)
            await ctx.send(f"{member.mention} DM me your move")

            dm = await member.create_dm()
            await dm.send("Please choose from `rock`, `paper`, or `scissors`")

            move2 = await self.bot.wait_for('message', timeout = 60.0, check=rpsCheck2)

        if move1.content == move2.content:
            embedVar = discord.Embed(title=f"{str(move1.author)} and {str(move2.author)} Tie! ", description=f"{move1.content.capitalize()} and {move2.content.capitalize()}", color=constants.RED)
        if move1.content == "rock" and move2.content == "scissors":
            embedVar = discord.Embed(title=f"{str(move1.author)} beats {str(move2.author)}", description=f"{move1.content.capitalize()} and {move2.content.capitalize()}", color=constants.RED)
        if move1.content == "scissors" and move2.content == "rock":
            embedVar = discord.Embed(title=f"{str(move2.author)} beats {str(move1.author)}", description=f"{move2.content.capitalize()} and {move1.content.capitalize()}", color=constants.RED)
        if move1.content == "rock" and move2.content == "paper":
            embedVar = discord.Embed(title=f"{str(move2.author)} beats {str(move1.author)}", description=f"{move2.content.capitalize()} and {move1.content.capitalize()}", color=constants.RED)
        if move1.content == "scissors" and move2.content == "paper":
            embedVar = discord.Embed(title=f"{str(move1.author)} beats {str(move2.author)}", description=f"{move1.content.capitalize()} and {move2.content.capitalize()}", color=constants.RED)
        if move1.content == "paper" and move2.content == "rock":
            embedVar = discord.Embed(title=f"{str(move1.author)} beats {str(move2.author)}", description=f"{move1.content.capitalize()} and {move2.content.capitalize()}", color=constants.RED)
        if move1.content == "paper" and move2.content == "scissors":
            embedVar = discord.Embed(title=f"{str(move2.author)} beats {str(move1.author)}", description=f"{move2.content.capitalize()} and {move1.content.capitalize()}", color=constants.RED)
        await ctx.reply(embed=embedVar)




def setup(bot):
    bot.add_cog(Misc(bot))
