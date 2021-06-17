import discord
from discord.ext import commands


class TestCommands(commands.Cog, description="Unstable test commands", command_attrs=dict(hidden=True, description="Can only be used by an Owner")):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = True
        print("Loaded", __name__)


    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)


def setup(bot):
    if getattr(bot, "debug", False):
        bot.add_cog(TestCommands(bot))
