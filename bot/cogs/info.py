from utils import utils, constants
from utils.constants import Regions, Converters, Color

import discord
from discord.ext import commands


class Info(commands.Cog, description="Commands for getting information on users, members, etc"):
    def __init__(self, bot):
        self.bot = bot
        print("Loaded", __name__)


    @commands.command(help="Gets source code of GamerBot", aliases=['src'])
    async def sourcecode(self, ctx):
        embed = discord.Embed(color=Color.red())
        embed.add_field(name="Source Code:", value="https://github.com/gamerbot")
        embed.add_field(name="Invite Link:", value="http://gamerbot.ga")
        await ctx.reply(embed=embed)


    async def getUserInfo(self, ctx, user : discord.User):
        embed = discord.Embed(title=f"{str(user)}'s Profile", description=user.mention, color=Color.red())
        embed.set_thumbnail(url=user.avatar_url)
        embed.add_field(name="Display Name:", value=user.display_name)
        embed.add_field(name="ID:", value=user.id)
        embed.add_field(name="Account creation date:", value=utils.UTCtoZone(user.created_at, ctx.guild.region.name))
        return embed


    @commands.command(description="<user> can be the name, id, or mention of a user", help="Gets information of a user")
    async def userinfo(self, ctx, *user : discord.User):
        user = ctx.author if not user else user[0]
        embed = await self.getUserInfo(ctx, user)
        await ctx.reply(embed=embed)


    @commands.command(description="<member> can be the name, id, or mention of a member", help="Gets information of a member")
    @commands.guild_only()
    async def memberinfo(self, ctx, *member : discord.Member):
        member = ctx.author if not member else member[0]
        embed = await self.getUserInfo(ctx, member)
        embed.add_field(name=f"Joined {ctx.guild.name} at:", value=utils.UTCtoZone(member.joined_at, ctx.guild.region.name))
        await ctx.send(embed=embed)


    @commands.command(help="Gets information of the current server", aliases=["serverinfo"])
    @commands.guild_only()
    async def guildinfo(self, ctx, *guild):
        if commands.is_owner() and guild:
            guild = await Converters.GuildConverter.convert(ctx, " ".join(guild))
        else:
            guild = ctx.guild

        embed = discord.Embed(title=f"{guild.name}'s Information", description=f"Description: {guild.description}", color=Color.red())
        embed.set_thumbnail(url=guild.icon_url)
        embed.add_field(name="Name:", value=guild.name)
        embed.add_field(name="ID:", value=guild.id)
        embed.add_field(name="Created at:", value=utils.UTCtoZone(guild.created_at, guild.region.name))
        embed.add_field(name="Members:", value=len([member for member in guild.members if not member.bot]))
        embed.add_field(name="Bots:", value=len([bot for bot in guild.members if bot.bot]))
        embed.add_field(name="Total Members:", value=guild.member_count)
        embed.add_field(name="Region:", value=str(guild.region))
        embed.add_field(name="Region:", value=getattr(Regions, guild.region.name))
        embed.add_field(name="\u200b", value="\u200b")
        embed.add_field(name="Owner:", value=guild.owner.mention, inline=False)
        embed.add_field(name="Emoji Limit:", value=f"{guild.emoji_limit} Emojis")
        embed.add_field(name="Filesize Limit:", value=f"{guild.filesize_limit} Bytes")
        embed.add_field(name="Bitrate Limit:", value=f"{guild.bitrate_limit} Bits")

        def getMFALevel(mfaint : int):
            if mfaint == 0:
                return "Not required"
            if mfaint == 1:
                return "Required"

        embed.add_field(name="Multi-Factor Authentication", value=getMFALevel(guild.mfa_level))
        await ctx.reply(embed=embed)




def setup(bot):
    bot.add_cog(Info(bot))
