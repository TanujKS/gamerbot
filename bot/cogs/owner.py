from utils.constants import r
from utils import utils

import discord
from discord.ext import commands
from discord.utils import get

import ast


class Owner(commands.Cog, command_attrs=dict(hidden=True, description="Can only be used by an Owner")):
    def __init__(self, bot):
        self.bot = bot
        self.description = "Commands for bot Owners"
        print("Loaded", __name__)


    async def cog_check(self, ctx):
        return commands.is_owner()


    @commands.command(help="Blacklists a user")
    async def blacklist(self, ctx, user : discord.User):
        blackListed = utils.loadBlacklisted(r)
        if user.id in blackListed:
            raise commands.BadArgument(f"{str(user)} is already blacklisted")
        blackListed.append(user.id)
        r.lpush("blacklisted", user.id)
        await ctx.reply(f"Blacklisted {str(user)}", mention_author=False)


    @commands.command(help="Unblacklists a user")
    async def unblacklist(self, ctx, user : discord.User):
        blackListed = utils.loadBlacklisted(r)
        if not user.id in blackListed:
            raise commands.BadArgument(f"{str(user)} is not blacklisted")
        blackListed.remove(user.id)
        r.lrem("blacklisted", 0, user.id)
        await ctx.reply(f"Unblacklisted {str(user)}", mention_author=False)


    @commands.command(help="Returns a list of blacklisted users")
    async def blacklisted(self, ctx):
        blackListed = utils.loadBlacklisted(r)
        message = ""
        for x in blackListed:
            user = self.bot.get_user(x)
            message += str(user)
            message += "\n"

        await ctx.reply(f"List of blacklisted members: {message}", mention_author=False)


    @commands.command(help="Disables a command")
    async def disablecommand(self, ctx, commandName):
        command = get(self.bot.commands, name=commandName)
        if not command:
            raise commands.BadArgument(f'Command "{commandName}" not found.')
        command.update(enabled=False)
        await ctx.reply(f"Disabled command {command}", mention_author=False)


    @commands.command(help="Enables a command")
    async def enablecommand(self, ctx, commandName):
        command = get(self.bot.commands, name=commandName)
        if not command:
            raise commands.BadArgument(f'Command "{commandName}" not found.')
        command.update(enabled=True)
        await ctx.reply(f"Enabled command {command}", mention_author=False)


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
            if not result:
                result = "Done"

            await ctx.reply(f"```{result}```", mention_author=False)

        except Exception as err:
            raise commands.BadArgument(f"```{err}```")


    @commands.command(help="Restarts the bot")
    async def restart(self, ctx):
        await ctx.reply("Confirm restart: (y/n)", mention_author=False)

        def check(m):
            responses = ['y', 'n']
            return m.author == ctx.author and m.channel == ctx.channel and m.content in responses

        response = await self.bot.wait_for('message', timeout=60, check=check)
        response = response.content

        if response == "y":
            await self.bot.logout()
        elif response == "n":
            await ctx.reply("Cancelled", mention_author=False)


    @commands.command(help="Shuts down the bot")
    async def shutdown(self, ctx):
        await ctx.reply("Confirm shutdown: (y/n)", mention_author=False)
        def check(m):
            responses = ["y", "n"]
            return m.author == ctx.author and m.channel == ctx.channel and m.content in responses
        response = await self.bot.wait_for('message', timeout=60, check=check)
        response = response.content
        if response == "y":
            r.set("shutdown", "True")
            await self.bot.logout()
        elif response == "n":
            await ctx.reply("Cancelled")




def setup(bot):
    bot.add_cog(Owner(bot))
