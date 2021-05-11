from utils import utils, constants, exceptions
from utils.constants import r, ezmessages, teams, command_prefix, emojis

import discord
from discord.ext import commands, tasks
from discord.utils import get

import random

import asyncio


class Listeners(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.updateStatus.start()

        self.hidden = True
        print("Loaded", __name__)


    @commands.Cog.listener()
    async def on_ready(self):
        print("Logged into", self.bot.user)
        print("ID:", self.bot.user.id)


    async def bot_check(self, ctx):
        blackListed = utils.loadBlacklisted(r)
        if ctx.author.id not in blackListed:
            return True
        else:
            raise exceptions.Blacklisted()


    def initGuild(self, guild : discord.Guild):
        guildInfo = utils.loadGuildInfo(r)
        guildInfo[guild.id] = {}
        guildInfo[guild.id]['antiez'] = False
        guildInfo[guild.id]['teamLimit'] = 2
        guildInfo[guild.id]['maximumTeams'] = 1
        guildInfo[guild.id]['TTVCrole'] = "TTVC"
        guildInfo[guild.id]['prefix'] = command_prefix
        utils.saveData(r, "guildInfo", guildInfo)
        print(f"Initialised {guild.name}")


    @commands.Cog.listener()
    async def on_guild_join(self, guild : discord.Guild):
        guildInfo = utils.loadGuildInfo(r)
        trackingGuilds = utils.loadTrackingGuilds(r)

        try:
            trackingGuilds[guild.id]
        except KeyError:
            trackingGuilds[guild.id] = []

        try:
            guildInfo[guild.id]
        except KeyError:
            self.initGuild(guild)

        await utils.sendReport(ctx, f"Joined {guild.name} with {guild.member_count} members")

        utils.saveData(r, "trackingGuilds", trackingGuilds)

        print(f"Joined {guild}")


    @commands.Cog.listener()
    async def on_guild_remove(self, guild : discord.Guild):
        print(f"Left {guild}")

        await utils.sendReport(ctx, f"Left {guild.name} with {guild.member_count} members")

        try:
            dm = await guild.owner.create_dm()
            def check(m):
                return m.author == dm.recipient and m.channel == dm
            await dm.send(f"Hello {str(guild.owner)}. I see you have removed {self.bot.user.name} from your server. As GamerBot is a new bot and is still in development it would be great to get your feedback on how the bot is/why you removed it. Would you be willing to answer a few questions? (y/n)")
            response = await self.bot.wait_for('message', timeout=120, check=check)
            if response.content == "y":
                await dm.send(f"Thank you! First, why are you removing {self.bot.user.name} from your server?")
                response = await self.bot.wait_for('message', timeout=120, check=check)
                await utils.sendReport(ctx, f"Reason for removal: {response.content}")

                await dm.send(f"Got it, on a scale of 1-10 how would you rate {self.bot.user.name}'s features, response time, ease of use, etc")
                response = await self.bot.wait_for('message', timeout=120, check=check)
                await utils.sendReport(ctx, f"Rating: {response.content}")

                await dm.send("Thanks! Any other comments/feedback?")
                response = await self.bot.wait_for('message', timeout=120, check=check)
                await utils.sendReport(ctx, f"Feedback: {response.content}")

                await dm.send(f"Thank you. Your feedback helps us make {self.bot.user.name} a better bot.")

            else:
                await dm.send("No problem. Goodbye!")

        except Exception as e:
            await utils.sendReport(ctx, f"Could not DM {str(guild.owner)} Exception: {e}")


    @commands.Cog.listener()
    async def on_message(self, message):
        guildInfo = utils.loadGuildInfo(r)

        if not message.author.bot:

            messageList = message.content.lower().split()

            if not message.reference and len(messageList) == 1 and self.bot.user in message.mentions:
                try:
                    await message.channel.send(f"My prefix in this server is `{utils.determine_prefix(self.bot, message)[-1]}`")
                except discord.errors.Forbidden:
                    pass

            if message.guild:

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
            if ctx.author.id == self.owner_id:
                await ctx.send("Bypassed disabled command")
                return await ctx.reinvoke()

        if isinstance(error, exceptions.raiseErrors):
            error = exceptions.EmbedError(title=str(error))

        elif isinstance(error, asyncio.TimeoutError):
            error = exceptions.EmbedError(title="Timed out")

        elif isinstance(error, exceptions.passErrors):
            return

        if isinstance(error, exceptions.EmbedError):
            embed = discord.Embed(title=error.title, description=error.description, color=constants.RED)

            if isinstance(originalerror, utils.exceptions.Blacklisted):
                try:
                    return await ctx.author.send(embed=embed)
                except discord.errors.Forbidden:
                    pass

            await ctx.reply(embed=embed)

        else:
            print(type(error), error)
            embed = discord.Embed(title="Error Report", color=constants.RED)
            embed.add_field(name="Guild Name:", value=ctx.guild.name, inline=True)
            embed.add_field(name="Guild ID:", value=ctx.guild.id, inline=True)
            embed.add_field(name="Channel:", value=ctx.channel.name, inline=True)
            embed.add_field(name="Error Victim:", value=str(ctx.author), inline=True)
            embed.add_field(name="Victim ID:", value=ctx.author.id, inline=True)
            embed.add_field(name="Time", value=message.created_at, inline=False)
            embed.add_field(name="Command:", value=ctx.command.name, inline=False)
            embed.add_field(name="Error:", value=type(error), inline=True)
            embed.add_field(name="Error:", value=error, inline=True)
            await utils.sendReport(ctx, "Error", embed=embed)
            error = exceptions.EmbedError(title="Something went wrong! This has been reported and will be reviewed shortly")
            await self.on_command_error(ctx, error)

        if isinstance(originalerror, commands.MissingRequiredArgument):
            return await ctx.send_help(ctx.command.name)


    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        guildInfo = utils.loadGuildInfo(r)

        if not user.bot and reaction.message.author == self.bot.user:
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

            try:
                dic = reaction.message.embeds[0].to_dict()
                if dic['title'].startswith("(closed)"):
                    await reaction.remove(user)
                elif dic['footer']['text'].startswith("Poll by"):
                    if str(reaction) in emojis:
                        for eachreaction in reaction.message.reactions:
                            if not str(eachreaction) == str(reaction):
                                await eachreaction.remove(user)
                    else:
                        await reaction.remove(user)
            except IndexError:
                pass


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
        guildInfo = utils.loadGuildInfo(r)
        trackingGuilds = utils.loadTrackingGuilds(r)

        appinfo = await self.bot.application_info()
        self.owner_id = appinfo.owner.id

        statusList = [f"on {len(self.bot.guilds)} servers | Use ?help to see what I can do", "major internal update :D", "whatever game you like", "why do bots not have custom statuses <(｀^´)>"]
        await self.bot.change_presence(activity=discord.Game(random.choice(statusList)))

        for guild in self.bot.guilds:
            if not trackingGuilds.get(guild.id):
                trackingGuilds[guild.id] = []
            if not guildInfo.get(guild.id):
                self.initGuild(guild)

        utils.saveData(r, "guildInfo", guildInfo)


    @updateStatus.before_loop
    async def before_updateStatus(self):
        await self.bot.wait_until_ready()




def setup(bot):
    bot.add_cog(Listeners(bot))
