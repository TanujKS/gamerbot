import discord
from discord.ext import commands


class Paginator:
    class PageNotFound(Exception):
        def __init__(self, page_number):
            super().__init__(f"Page {page_number} not found")


    class NoContext(Exception):
        def __init__(self):
            super().__init__("commands.Context is required to send the paginator")


    class PaginatorNotSent(Exception):
        def __init__(self):
            super().__init__("send_page must be called before next_page or previous_page")


    def __init__(self, bot):
        self.bot = bot
        self.pages = ["FILLER"]


    def add_page(self, content):
        self.pages.append(content)


    def del_page(self, index):
        try:
            self.pages.pop(index)
        except IndexError:
            raise self.PageNotFound(index)


    async def send_page(self, *, ctx=None, action="send", page_number=1):
        try:
            page = self.pages[page_number]
            if page == "FILLER":
                return
            content = page if not isinstance(page, discord.Embed) else None
            embed = page if isinstance(page, discord.Embed) else None

            if action == "send":
                if not ctx:
                    raise self.NoContext()

                self.author = ctx.author
                self.ctx = await ctx.send(content, embed=embed)
                self.bot.cogs["PaginatorCog"].paginators[self.ctx.id] = self
                await self.ctx.add_reaction("⬅️")
                await self.ctx.add_reaction("🟦")
                await self.ctx.add_reaction("➡️")

            elif action == "edit":
                await self.ctx.edit(content=content, embed=embed)

            self.currentPage = page_number

        except IndexError:
            raise self.PageNotFound(page_number)


    async def next_page(self):
        try:
            page_number = self.currentPage + 1
            if page_number >= len(self.pages):
                page_number = 1
            self.currentPage = page_number
            await self.send_page(page_number=page_number, action="edit")
        except AttributeError:
            raise self.PaginatorNotSent()


    async def previous_page(self):
        try:
            page_number = self.currentPage - 1
            if page_number == 0:
                page_number = len(self.pages) - 1
            self.currentPage = page_number
            await self.send_page(page_number=page_number, action="edit")
        except AttributeError:
            raise self.PaginatorNotSent()


    async def freeze_paginator(self):
        await self.ctx.clear_reactions()
        del self.bot.cogs["PaginatorCog"].paginators[self.ctx.id]


class PaginatorCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = True
        self.paginators = {}
        print("Loaded", __name__)


    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if not user.bot and reaction.message.author == self.bot.user:
            if self.paginators.get(reaction.message.id):
                if user == self.paginators[reaction.message.id].author:
                    if str(reaction) == "⬅️":
                        await self.paginators[reaction.message.id].previous_page()
                    if str(reaction) == "➡️":
                        await self.paginators[reaction.message.id].next_page()
                    if str(reaction) == "🟦":
                        await self.paginators[reaction.message.id].freeze_paginator()

                await reaction.remove(user)


def setup(bot):
    bot.add_cog(PaginatorCog(bot))
