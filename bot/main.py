from utils import utils, exceptions
from utils.help import EmbedHelpCommand
from utils.constants import r, EnvVars

import os
import sys

import discord
from discord.ext import commands


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

bot.owner_mode = True if len(sys.argv) >= 3 and sys.argv[2] == "owner" else False

for file in os.listdir("bot/cogs"):
    if file.endswith(".py"):
        fileName = file[:-3]
        bot.load_extension(f"cogs.{fileName}")


try:
    TOKEN = getattr(EnvVars, sys.argv[1])
except (AttributeError, IndexError):
    raise ValueError("Invalid token")


bot.run(TOKEN)
