import discord
from discord.ext import commands

raiseErrors = (commands.UserNotFound, commands.CommandOnCooldown, commands.NoPrivateMessage, commands.BadArgument, commands.UnexpectedQuoteError, commands.DisabledCommand, commands.MissingPermissions, commands.MissingRole, commands.BotMissingPermissions, discord.errors.Forbidden, commands.MissingRequiredArgument, commands.ExpectedClosingQuoteError, discord.errors.InvalidArgument)
passErrors = (commands.CommandNotFound, commands.NotOwner)


class EmbedError(Exception):
    def __init__(self, *, title, description=""):
        self.title = "⚠️ " + title
        self.description = description
        super().__init__()


class Blacklisted(commands.BadArgument):
    def __init__(self):
        super().__init__(message="You are blacklisted and cannot use GamerBot commands")
