from utils import utils
from utils.constants import Color

import discord
from discord.ext import commands

import asyncio
import traceback
import sys


raise_errors = (commands.DisabledCommand, commands.UserNotFound, commands.CommandOnCooldown, commands.NoPrivateMessage, commands.BadArgument, commands.UnexpectedQuoteError, commands.DisabledCommand, commands.MissingPermissions, commands.MissingRole, commands.BotMissingPermissions, discord.errors.Forbidden, commands.MissingRequiredArgument, commands.ExpectedClosingQuoteError, discord.errors.InvalidArgument)
ignored_errors = (commands.CommandNotFound, commands.NotOwner, commands.CheckFailure)


class EmbedError(Exception):
    def __init__(self, original=None, *, title, description=""):
        self.title = "⚠️ " + title
        self.description = description
        self.original = original
        super().__init__()


    def get_embed(self):
        return discord.Embed(title=self.title, description=self.description, color=Color.red())


    async def send(self, destination):
        try:
            await destination.send(embed=self.get_embed())
        except discord.HTTPException:
            pass


class Blacklisted(commands.BadArgument):
    def __init__(self):
        super().__init__(message="You are blacklisted and cannot use GamerBot commands")


class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = True
        print("Loaded", __name__)


    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if hasattr(ctx.command, 'on_error'):
            return

        cog = ctx.cog
        if cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return

        error = getattr(error, 'original', error)
        destination = ctx


        if isinstance(error, ignored_errors):
            return


        if isinstance(error, commands.DisabledCommand):
            if await self.bot.is_owner(ctx.author):
                await ctx.send("Bypassed disabled command")
                try:
                    await ctx.reinvoke()
                    return
                except Exception as error:
                    await self.on_command_error(ctx, error)


        if isinstance(error, asyncio.TimeoutError):
            error = EmbedError(error, title="Timed out")


        if isinstance(error, raise_errors):
            error = EmbedError(error, title=str(error))


        if not isinstance(error, EmbedError):
            if self.bot.debug:
                traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
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
                tb = traceback.format_exception(type(error), error, error.__traceback__)
                message = "```" + "".join(tb) + "```"
                await utils.sendReport(message)

            error = EmbedError(title="Something went wrong! This has been reported and will be reviewed shortly")


        if isinstance(error, EmbedError):
            await error.send(destination)


        if isinstance(error.original, commands.MissingRequiredArgument):
            await destination.send_help(ctx.command.name)


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
