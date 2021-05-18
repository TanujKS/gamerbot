from utils import utils, constants
from utils.constants import r

import discord
from discord.ext import commands
from discord.utils import get

from datetime import datetime

import ast


class Owner(commands.Cog, description="Commands for bot Owners", command_attrs=dict(hidden=True, description="Can only be used by an Owner")):
    def __init__(self, bot):
        self.bot = bot
        self.command_count = 0
        self.uniqueUsers = []
        self.uniqueGuilds = []
        print("Loaded", __name__)


    async def cog_check(self, ctx):
        return commands.is_owner()


    @commands.Cog.listener()
    async def on_ready(self):
        self.startTime = datetime.utcnow()


    @commands.Cog.listener()
    async def on_command(self, ctx):
        self.command_count += 1

        if ctx.author.id not in self.uniqueUsers:
            self.uniqueUsers.append(ctx.author.id)

        if ctx.guild.id not in self.uniqueGuilds:
            self.uniqueGuilds.append(ctx.guild.id)


    def getTotalMembers(self):
        total_members = 0
        for guild in self.bot.guilds:
            total_members += guild.member_count
        return total_members


    @commands.command(help="Gets information of GamerBot")
    async def botinfo(self, ctx):
        embed = discord.Embed(title="GamerBot statistics", color=constants.RED)
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        embed.add_field(name="Guilds:", value=len(self.bot.guilds))
        embed.add_field(name="Total Members:", value=self.getTotalMembers())
        embed.add_field(name="\u200b", value="\u200b")
        embed.add_field(name="Up since:", value=utils.UTCtoZone(self.startTime, ctx.guild.region), inline=False)
        embed.add_field(name="Commands ran:", value=self.command_count)
        embed.add_field(name="Unique Users:", value=len(self.uniqueUsers))
        embed.add_field(name="Unique Guilds:", value=len(self.uniqueGuilds))
        await ctx.reply(embed=embed)


    @commands.command(help="Gets a list of all servers GamerBot is in and their member count")
    async def guildlist(self, ctx):
        embed = discord.Embed(title="GamerBot Servers", color=constants.RED)
        embed.add_field(name="Guilds:", value=len(self.bot.guilds), inline=False)
        embed.add_field(name="Total Members:", value=self.getTotalMembers(), inline=False)
        for guild in self.bot.guilds:
            embed.add_field(name="Name:", value=guild.name)
            embed.add_field(name="Members:", value=guild.member_count)
            embed.add_field(name="Region:", value=guild.region.name)
        await ctx.reply(embed=embed)


    @commands.command(help="Blacklists a user")
    async def blacklist(self, ctx, user : discord.User):
        blackListed = utils.loadBlacklisted()
        if user.id in blackListed:
            raise commands.BadArgument(f"{user.mention} is already blacklisted")
        blackListed.append(user.id)
        r.lpush("blacklisted", user.id)
        await ctx.reply(f"Blacklisted {user.mention}")


    @commands.command(help="Unblacklists a user")
    async def unblacklist(self, ctx, user : discord.User):
        blackListed = utils.loadBlacklisted()
        if not user.id in blackListed:
            raise commands.BadArgument(f"{user.mention} is not blacklisted")
        blackListed.remove(user.id)
        r.lrem("blacklisted", 0, user.id)
        await ctx.reply(f"Unblacklisted {user.mention}")


    @commands.command(help="Returns a list of blacklisted users")
    async def blacklisted(self, ctx):
        blackListed = utils.loadBlacklisted()
        mentions = [user.mention for user in [self.bot.get_user(x) for x in blackListed]]
        message = ""
        for mention in mentions:
            message += "\n"
            message += mention

        await ctx.reply(f"List of blacklisted members: {message}")


    @commands.command(help="Disables a command")
    async def disablecommand(self, ctx, commandName):
        command = get(self.bot.commands, name=commandName)
        if not command:
            raise commands.BadArgument(f'Command "{commandName}" not found.')
        command.update(enabled=False)
        await ctx.reply(f"Disabled command {command}")


    @commands.command(help="Enables a command")
    async def enablecommand(self, ctx, commandName):
        command = get(self.bot.commands, name=commandName)
        if not command:
            raise commands.BadArgument(f'Command "{commandName}" not found.')
        command.update(enabled=True)
        await ctx.reply(f"Enabled command {command}")


    @commands.command(help="Evalutes code in Python", aliases=['eval', 'exec', 'run'])
    async def eval_fn(self, ctx, *, cmd):

        def insert_returns(body):
            if isinstance(body[-1], ast.Expr):
                body[-1] = ast.Return(body[-1].value)
                ast.fix_missing_locations(body[-1])

            if isinstance(body[-1], ast.If):
                insert_returns(body[-1].body)
                insert_returns(body[-1].orelse)

            if isinstance(body[-1], ast.With):
                insert_returns(body[-1].body)

        try:
            fn_name = "_eval_expr"

            cmd = cmd.strip("` ")

            cmd = "\n".join(f"    {i}" for i in cmd.splitlines())

            body = f"async def {fn_name}():\n{cmd}"

            parsed = ast.parse(body)
            body = parsed.body[0].body

            insert_returns(body)

            env = {
                'bot': ctx.bot,
                'discord': discord,
                'commands': commands,
                'ctx': ctx,
                '__import__': __import__,
                'get': get,
                'r': r,
                "self": self
            }

            exec(compile(parsed, filename="<ast>", mode="exec"), env)

            result = (await eval(f"{fn_name}()", env))

            await ctx.reply(f"```{str(result)}```")

        except Exception as err:
            raise commands.BadArgument(f"```{err}```")


    @commands.command(help="Restarts the bot")
    async def restart(self, ctx):
        await ctx.reply("Confirm restart: (y/n)")
        await self.botLogout(ctx)


    @commands.command(help="Shuts down the bot")
    async def shutdown(self, ctx):
        await ctx.reply("Confirm shutdown: (y/n)")
        if await self.botLogout(ctx):
            r.set("shutdown", "True")


    async def botLogout(self, ctx):
        def check(m):
            responses = ['y', 'n']
            return m.author == ctx.author and m.channel == ctx.channel and m.content in responses

        response = await self.bot.wait_for('message', timeout=60, check=check)
        response = response.content

        if response == "y":
            await self.bot.close()
            return True
        elif response == "n":
            await ctx.reply("Cancelled")




def setup(bot):
    bot.add_cog(Owner(bot))
