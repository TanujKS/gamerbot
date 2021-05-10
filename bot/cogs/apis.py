import discord
from discord.ext import commands


class APIHelp(commands.Cog, name="APIs", description="List of all APIs used by GamerBot"):
    def __init__(self, bot):
        self.bot = bot
        print("Loaded", __name__)


    @commands.command(name="Hypixel API", help="https://api.hypixel.net/")
    async def HypixelAPI(self, ctx):
        pass


    @commands.command(name="Mojang API", help="https://mojang.readthedocs.io/en/latest/")
    async def MojangAPI(self, ctx):
        pass


    @commands.command(name="Crafatar API", help="https://crafatar.com/")
    async def MCHeadsAPI(self, ctx):
        pass


    @commands.command(name="Fortnite API", help="https://fortnite-api.com")
    async def FortniteAPI(self, ctx):
        pass


    @commands.command(name="Twitch API", help="https://dev.twitch.tv/docs/api")
    async def TwitchAPI(self, ctx):
        pass


    @commands.command(name="Tracker.gg API", help="https://tracker.gg")
    async def TrackerAPI(self, ctx):
        pass


    @commands.command(name="YouTube API", help="https://developers.google.com/youtube/")
    async def YouTubeAPI(self, ctx):
        pass


    @commands.command(name="Google Translate API", help="https://pypi.org/project/googletrans/")
    async def GoogleAPI(self, ctx):
        pass




def setup(bot):
    bot.add_cog(APIHelp(bot))
