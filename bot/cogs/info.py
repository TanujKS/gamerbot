from utils.constants import embedColors, regions

import discord
from discord.ext import commands
from discord.utils import get

import pytz
from pytz import timezone, utc


class Info(commands.Cog, description="Commands for getting information on users, members, etc"):
    def __init__(self, bot):
        self.bot = bot
        print("Loaded", __name__)


    async def getUserInfo(self, ctx, user : discord.User):
        embed = discord.Embed(title=f"{str(user)}'s Profile", description=user.mention, color=embedColors["Red"])
        embed.set_thumbnail(url=user.avatar_url)
        embed.add_field(name="Display Name:", value=user.display_name)
        embed.add_field(name="ID:", value=user.id)
        embed.add_field(name="Account creation date:", value=(user.created_at).astimezone(timezone(regions[str(ctx.guild.region)])).strftime('%m/%d/%Y %H:%M:%S ') + f" {regions[str(ctx.guild.region)]} Time")
        return embed


    @commands.command(help="Gets source code of GamerBot")
    async def sourcecode(self, ctx):
        embed = discord.Embed(color=embedColors["Red"])
        embed.add_field(name="Source Code:", value="https://github.com/gamerbot")
        embed.add_field(name="Invite Link:", value="http://gamerbot.ga")
        await ctx.reply(embed=embed)


    @commands.command(description="<user> can be the name, id, or mention of a user", help="Gets information of a user")
    async def userinfo(self, ctx, user : discord.User):
        embed = await self.getUserInfo(ctx, user)
        await ctx.reply(embed=embed, allowed_mentions=discord.AllowedMentions.none())


    @commands.command(description="<member> can be the name, id, or mention of a member", help="Gets information of a member")
    @commands.guild_only()
    async def memberinfo(self, ctx, member : discord.Member):
        embed = await self.getUserInfo(ctx, member)
        embed.add_field(name=f"Joined {ctx.guild.name} at:", value=(member.joined_at).astimezone(timezone(regions[str(ctx.guild.region)])).strftime('%m/%d/%Y %H:%M:%S') + f" {regions[str(ctx.guild.region)]} Time")
        await ctx.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())


    @commands.command(description="<guild> can be the name, or id of a server GamerBot is in or left blank to get information of the current server", help="Gets information of a server", aliases=["serverinfo"], enabled=False, hidden=True)
    @commands.guild_only()
    async def guildinfo(self, ctx, *guild : discord.Guild):
        if not guild:
            guild = ctx.guild

        embed = discord.Embed(title=f"{guild.name}'s Information", description=f"Description: {guild.description}", color=embedColors["Red"])
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.add_field(name="Name:", value=guild.name)
        embed.add_field(name="ID:", value=guild.id)
        embed.add_field(name="Created at:", value=(guild.created_at).astimezone(timezone(regions[str(ctx.guild.region)])).strftime('%m/%d/%Y %H:%M:%S') + f" {regions[str(ctx.guild.region)]} Time")
        embed.add_field(name="Members:", value=len([member for member in ctx.guild.members if not member.bot]))
        embed.add_field(name="Bots:", value=len([bot for bot in ctx.guild.members if bot.bot]))
        embed.add_field(name="Total Members:", value=guild.member_count)
        embed.add_field(name="Region:", value=str(ctx.guild.region))
        embed.add_field(name="Region:", value=regions[str(ctx.guild.region)])
        embed.add_field(name="\u200b", value="\u200b")
        embed.add_field(name="Owner:", value=str(ctx.guild.owner))
        embed.add_field(name="Owner ID:", value=guild.owner_id)
        embed.add_field(name="Owner Mention:", value=guild.owner.mention)
        embed.add_field(name="Emoji Limit:", value=f"{guild.emoji_limit} Emojis")
        embed.add_field(name="Filesize Limit:", value=f"{guild.filesize_limit} Bytes")
        embed.add_field(name="Bitrate Limit:", value=f"{guild.bitrate_limit} Bits")

        def getMFALevel(mfaint : int):
            if int == 0:
                return "Not required"
            if int == 1:
                return "Required"

        embed.add_field(name="Multi-Factor Authenticat")
        await ctx.reply(embed=embed, allowed_mentions=discord.AllowedMentions.none())




def setup(bot):
    bot.add_cog(Info(bot))
