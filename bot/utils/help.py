if __name__ == "__main__":
    from constants import Color
else:
    from utils.constants import Color

import discord
from discord.ext import commands


class EmbedHelpCommand(commands.MinimalHelpCommand):
    def __init__(self):
        super().__init__()
        self.verify_checks = False


    async def send_pages(self):
        destination = self.get_destination()
        embed = discord.Embed(description="", color=Color.red())
        embed.set_footer(text="GamerBot is created and maintained by tanju_shorty#2828")
        embed.set_thumbnail(url=self.context.bot.user.avatar_url)
        for page in self.paginator.pages:
            embed.description += page
        await destination.send(embed=embed)


    async def send_cog_help(self, cog):
        if getattr(cog, "hidden", False):
            return

        await super().send_cog_help(cog)
