from utils import utils, constants, exceptions
from utils.constants import r, ezmessages, teams, command_prefix, emojis, Color

import discord
from discord.ext import commands, tasks
from discord.utils import get

import random

import asyncio

import traceback


class Listeners(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.updateStatus.start()

        self.hidden = True

        print("Loaded", __name__)


    async def bot_check(self, ctx):
        if self.bot.debug:
            return await self.bot.is_owner(ctx.author)

        blackListed = utils.loadBlacklisted()
        if ctx.author.id not in blackListed:
            return True
        else:
            raise exceptions.Blacklisted()


    @commands.Cog.listener()
    async def on_ready(self):
        print("Logged into", self.bot.user)
        print("ID:", self.bot.user.id)
        print("Debug:", self.bot.debug)


    @staticmethod
    def initGuild(guild : discord.Guild):
        guildInfo = utils.loadGuildInfo()
        guildInfo[guild.id] = {}
        guildInfo[guild.id]['antiez'] = False
        guildInfo[guild.id]['teamLimit'] = 2
        guildInfo[guild.id]['maximumTeams'] = 1
        guildInfo[guild.id]['TTVCrole'] = "TTVC"
        guildInfo[guild.id]['prefix'] = command_prefix
        utils.saveData("guildInfo", guildInfo)
        print(f"Initialised {guild.name}")


    @commands.Cog.listener()
    async def on_guild_join(self, guild : discord.Guild):
        guildInfo = utils.loadGuildInfo()
        trackingGuilds = utils.loadTrackingGuilds()

        try:
            trackingGuilds[guild.id]
        except KeyError:
            trackingGuilds[guild.id] = []

        try:
            guildInfo[guild.id]
        except KeyError:
            self.initGuild(guild)

        await utils.sendReport(f"Joined {guild.name} with {guild.member_count} members")

        utils.saveData("trackingGuilds", trackingGuilds)

        print(f"Joined {guild}")


    @commands.Cog.listener()
    async def on_guild_remove(self, guild : discord.Guild):
        print(f"Left {guild}")

        await utils.sendReport(f"Left {guild.name} with {guild.member_count} members")

        try:
            dm = await guild.owner.create_dm()
            def check(m):
                responses = ['y', 'n']
                return m.author == dm.recipient and m.channel == dm and m.content in responses

            await dm.send(f"Hello {guild.owner.mention}. I see you have removed {self.bot.user.name} from your server. As GamerBot is a new bot and is still in development it would be great to get your feedback on how the bot is/why you removed it. Would you be willing to answer a few questions? (y/n)")
            response = await self.bot.wait_for('message', timeout=120, check=check)
            if response.content == "y":
                await dm.send(f"Thank you! First, why are you removing {self.bot.user.name} from your server?")
                response = await self.bot.wait_for('message', timeout=120, check=check)
                await utils.sendReport(f"Reason for removal: {response.content}")

                await dm.send(f"Got it, on a scale of 1-10 how would you rate {self.bot.user.name}'s features, response time, ease of use, etc")
                response = await self.bot.wait_for('message', timeout=120, check=check)
                await utils.sendReport(f"Rating: {response.content}")

                await dm.send("Thanks! Any other comments/feedback?")
                response = await self.bot.wait_for('message', timeout=120, check=check)
                await utils.sendReport(f"Feedback: {response.content}")

                await dm.send(f"Thank you. Your feedback helps us make {self.bot.user.name} a better bot.")

            else:
                await dm.send("No problem. Goodbye!")

        except Exception as e:
            await utils.sendReport(f"Could not DM {guild.owner.mention} Exception: {e}")


    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:

            messageList = message.content.lower().split()
            if message.guild:

                if not message.reference and len(messageList) == 1 and message.guild.me.mention == messageList[0]:
                    try:
                        await message.channel.send(f"My prefix in this server is `{utils.determine_prefix(self.bot, message, clean=True)}`")
                    except discord.errors.Forbidden:
                        pass

                guildInfo = utils.loadGuildInfo()

                if ("ez" in messageList or "kys" in messageList) and guildInfo[message.guild.id]['antiez']:
                    webhooks = await message.channel.webhooks()
                    webhook = get(webhooks, name="ezbot")
                    if not webhook:
                        webhook = await message.channel.create_webhook(name="ezbot")

                    await webhook.send(random.choice(ezmessages), username=message.author.display_name, avatar_url=message.author.avatar_url)
                    await message.delete()


    @commands.Cog.listener()
    async def on_command_error(self, ctx, originalerror):
        error = originalerror.original if isinstance(originalerror, commands.CommandInvokeError) else originalerror

        if isinstance(error, commands.DisabledCommand):
            if await self.bot.is_owner(ctx.author):
                await ctx.send("Bypassed disabled command")
                return await ctx.reinvoke()

        if isinstance(error, exceptions.raiseErrors):
            error = exceptions.EmbedError(title=str(error))

        elif isinstance(error, asyncio.TimeoutError):
            error = exceptions.EmbedError(title="Timed out")

        elif isinstance(error, exceptions.passErrors):
            return

        if isinstance(error, exceptions.EmbedError):
            embed = discord.Embed(title=error.title, description=error.description, color=Color.red())

            if isinstance(originalerror, utils.exceptions.Blacklisted):
                try:
                    return await ctx.author.send(embed=embed)
                except discord.errors.Forbidden:
                    pass

            await ctx.reply(embed=embed)

        else:
            if self.bot.debug:
                traceback.print_tb(error.__traceback__)
                print(type(error), error)
            else:
                embed = discord.Embed(title="Error Report", color=Color.red())
                embed.add_field(name="Guild Name:", value=ctx.guild.name, inline=True)
                embed.add_field(name="Guild ID:", value=ctx.guild.id, inline=True)
                embed.add_field(name="Channel:", value=ctx.channel.name, inline=True)
                embed.add_field(name="Error Victim:", value=str(ctx.author), inline=True)
                embed.add_field(name="Victim ID:", value=ctx.author.id, inline=True)
                embed.add_field(name="Time", value=ctx.message.created_at, inline=False)
                embed.add_field(name="Command:", value=ctx.command.name, inline=False)
                embed.add_field(name="Error:", value=type(error), inline=True)
                embed.add_field(name="Message:", value=str(error), inline=True)
                await utils.sendReport("Error", embed=embed)
                tb = traceback.extract_tb(error.__traceback__).format()
                message = "```"
                for t in tb:
                    message += t
                message += "```"
                await utils.sendReport(message)

            error = exceptions.EmbedError(title="Something went wrong! This has been reported and will be reviewed shortly")
            await self.on_command_error(ctx, error)

        if isinstance(originalerror, commands.MissingRequiredArgument):
            return await ctx.send_help(ctx.command.name)


    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if not user.bot and reaction.message.author == self.bot.user:
            guildInfo = utils.loadGuildInfo()
            if reaction.message.content == "React to get into your teams":
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


            if reaction.message.content == "Teams are now closed.":
                await reaction.remove(user)


    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        if reaction.message.content == "React to get into your teams" and reaction.message.author == self.bot.user:
            if utils.checkIfSetup(reaction):
                if str(reaction) in emojis:
                    team = teams[emojis.index(str(reaction))]
                    role = get(user.guild.roles, name=team)
                    if role in user.roles:
                        await user.remove_roles(role)


    @tasks.loop(seconds=600)
    async def updateStatus(self):
        guildInfo = utils.loadGuildInfo()
        trackingGuilds = utils.loadTrackingGuilds()

        appinfo = await self.bot.application_info()
        self.owner_id = appinfo.owner.id

        statusList = [f"on {len(self.bot.guilds)} servers | Use ?help to see what I can do", "major internal update :D", "whatever game you like", "why do bots not have custom statuses <(｀^´)>"]
        await self.bot.change_presence(activity=discord.Game(random.choice(statusList)))

        for guild in self.bot.guilds:
            if not trackingGuilds.get(guild.id):
                trackingGuilds[guild.id] = []
            if not guildInfo.get(guild.id):
                self.initGuild(guild)

        utils.saveData("guildInfo", guildInfo)


    @updateStatus.before_loop
    async def before_updateStatus(self):
        await self.bot.wait_until_ready()




def setup(bot):
    bot.add_cog(Listeners(bot))
