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
        try:
            if cog.hidden:
                return
        except AttributeError:
            pass

        bot = self.context.bot
        if bot.description:
            self.paginator.add_line(bot.description, empty=True)

        note = self.get_opening_note()
        if note:
            self.paginator.add_line(note, empty=True)

        if cog.description:
            self.paginator.add_line(cog.description, empty=True)

        filtered = await self.filter_commands(cog.get_commands(), sort=self.sort_commands)
        if filtered:
            self.paginator.add_line('**%s %s**' % (cog.qualified_name, self.commands_heading))
            for command in filtered:
                self.add_subcommand_formatting(command)

            note = self.get_ending_note()
            if note:
                self.paginator.add_line()
                self.paginator.add_line(note)

        await self.send_pages()
