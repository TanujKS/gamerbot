from utils import utils, exceptions
from utils.help import EmbedHelpCommand
from utils.constants import r, EnvVars

import discord
from discord.ext import commands

import os

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("TOKEN", help="The variable name for the token to log into a Discord client")
parser.add_argument("-d", "--debug", help="Boots the bot into Debug mode, where only the bot Owner can use commands and tracebacks are printed etc", action="store_true")
args = parser.parse_args()


if r.get("shutdown") == "True":
    raise Exception("Shutting down")


bot = commands.Bot(
    command_prefix=utils.determine_prefix,
    description="Help for GamerBot commands",
    intents=discord.Intents.all(),
    case_insensitive=True,
    help_command=EmbedHelpCommand(),
    allowed_mentions=discord.AllowedMentions.none()
)

bot.debug = True if args.debug else False


for file in os.listdir("bot/cogs"):
    if file.endswith(".py"):
        fileName = file[:-3]
        bot.load_extension(f"cogs.{fileName}")


try:
    TOKEN = getattr(EnvVars, args.TOKEN)
except AttributeError:
    raise ValueError("Invalid token")


bot.run(TOKEN)
