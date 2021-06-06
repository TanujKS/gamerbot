import discord
from discord.ext import commands


class TestCommands(commands.Cog, description="Unstable test commands", command_attrs=dict(hidden=True, description="Can only be used by an Owner")):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = True
        print("Loaded", __name__)


    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)


    @commands.command()
    async def pagetest(self, ctx):
        Paginator = utils.Paginator(self.bot)
        for i in range(1, 11):
            embed = discord.Embed(title=f"Page {i}", color=Color.red())
            Paginator.add_page(embed)
        await Paginator.send_page(ctx=ctx)




def setup(bot):
    if bot.debug:
        bot.add_cog(TestCommands(bot))
