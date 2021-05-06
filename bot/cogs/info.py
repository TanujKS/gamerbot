from utils.constants import embedColors, regions

import discord
from discord.ext import commands
from discord.utils import get

import pytz
from pytz import timezone, utc


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.description = "Commands for getting information on users, members, etc"
        print("Loaded", __name__)


    async def getUserInfo(self, ctx, user : discord.User):
        embed = discord.Embed(title=f"{str(user)}'s Profile", description=user.mention, color=embedColors["Red"])
        embed.set_thumbnail(url=user.avatar_url)
        embed.add_field(name="Display Name:", value=user.display_name)
        embed.add_field(name="ID:", value=user.id)
        embed.add_field(name="Account creation date:", value=(user.created_at).astimezone(timezone(regions[str(ctx.guild.region)])).strftime('%m/%d/%Y %H:%M:%S ') + f" {regions[str(ctx.guild.region)]} Time")
        return embed


    @commands.command(description="<user> can be the name, id, or mention of a user", help="Gets information of a user")
    async def userinfo(self, ctx, user : discord.User):
        embed = await self.getUserInfo(ctx, user)
        await ctx.reply(embed=embed, allowed_mentions=discord.AllowedMentions.none())


    @commands.command(description="<member> can be the name, id, or mention of a member", help="Gets information of a member")
    async def memberinfo(self, ctx, member : discord.Member):
        embed = await self.getUserInfo(ctx, member)
        embed.add_field(name=f"Joined {ctx.guild.name} at:", value=(member.joined_at).astimezone(timezone(regions[str(ctx.guild.region)])).strftime('%m/%d/%Y %H:%M:%S ') + f" {regions[str(ctx.guild.region)]} Time")
        await ctx.send(embed=embed, mention_author=False)


    @commands.command(description="<guild> can be the name, or id of a server GamerBot is in or left blank to get information of the current server", help="Gets information of a server", aliases=["serverinfo"], enabled=False, hidden=True)
    async def guildinfo(self, ctx, *guild : discord.Guild):
        if not guild:
            guild = ctx.guild

        embed = discord.Embed(title=f"{guild.name}'s Information", color=embedColors["Red"])
        embed.set_thumbnail(url=ctx.guild.icon_url)




def setup(bot):
    bot.add_cog(Info(bot))
