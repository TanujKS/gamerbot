from utils import utils, constants
from utils.constants import r, Converters, HypixelModes, EnvVars, Color

import discord
from discord.ext import commands
from discord.utils import get

import math

import time
from datetime import datetime

from collections import OrderedDict

from mojang import MojangAPI


class MinecraftSkinFetcher:
    api = "https://mc-heads.net/"
    head_url = "head/"
    body_url = "body/"


    def __init__(self, url):
        self.url = url


    def __str__(self):
        return self.url


    @classmethod
    def head(cls, identifier):
        return cls(cls.api + cls.head_url + identifier + cls.finalize())


    @classmethod
    def body(cls, identifier):
        return cls(cls.api + cls.body_url + identifier + cls.finalize())


    @staticmethod
    def finalize():
        return f"/&?{round(time.time())}"


class HypixelStatFetcher:
    api_url = f"https://api.hypixel.net/player?key={EnvVars.HYPIXEL_KEY}"

    def __init__(self, *, player, mode, rawData, data):
        self.player = player
        self.mode = mode
        self.rawData = rawData
        self.data = mode
        print(player, mode)


    @classmethod
    def has_mode(cls):
        try:
            cls.modes
        except AttributeError:
            raise AttributeError("No modes have been specified")


    @classmethod
    def check_mode(cls, mode):
        cls.has_mode()
        mode = utils.multi_key_dict_get(cls.modes, mode)
        if not mode:
            raise commands.BadArgument("Invalid mode")
        return mode


    @classmethod
    async def get_raw_data(cls, ctx: commands.context, player_and_mode: tuple):
        cls.has_mode()
        player_and_mode = list(player_and_mode)

        if len(player_and_mode) == 0:
            member = ctx.author
            mode = None

        elif utils.multi_key_dict_get(cls.modes, " ".join(player_and_mode)):
            member = ctx.author
            mode = " ".join(player_and_mode)

        elif ctx.message.mentions:
            member = await Converters.MemberConverter.convert(ctx, player_and_mode[0])
            player_and_mode.pop(0)
            if player_and_mode:
                print(" ".join(player_and_mode))

                mode = cls.check_mode(" ".join(player_and_mode))
            else:
                mode = None

        else:
            member = None
            player = player_and_mode[0]
            player_and_mode.pop(0)
            if player_and_mode:
                mode = cls.check_mode(" ".join(player_and_mode))
            else:
                mode = None

        if member:
            player = r.get(member.id)
            if not player:
                raise commands.BadArgument(f"{str(member)} has not linked their Discord to their Minecraft account. Run {utils.determine_prefix(ctx.bot, ctx, clean=True)}mclink")
            player = player.decode("utf-8")

        uuid = MojangAPI.get_uuid(player)
        if not uuid:
            raise commands.BadArgument(f'Player "{player}" not found.')

        rawData = await utils.getJSON(f"https://api.hypixel.net/player?key={EnvVars.HYPIXEL_KEY}&uuid={uuid}")
        if rawData.get("success") == None:
            raise commands.BadArgument(rawData.get('cause'))

        return player, mode, rawData


class BedwarsStatFetcher(HypixelStatFetcher):
    modes = HypixelModes.bedwarsModes

    @classmethod
    async def get_data(cls, ctx, player_and_mode):
        player, mode, rawData = await cls.get_raw_data(ctx, player_and_mode)

        if not rawData.get('player') or not rawData['player'].get('stats') or not rawData['player']['stats'].get("Bedwars"):
            raise commands.BadArgument(f"{player} has not played Bedwars")

        data = rawData['player']['stats']['Bedwars']

        return cls(player=player, mode=mode, rawData=rawData, data=data)


    def overall_stats(self):
        rawData = self.rawData
        data = self.data

        embed = discord.Embed(title=f"{rawData['player']['displayname']}'s Hypixel Bedwars Profile", description=f"Bedwars stats for {rawData['player']['displayname']}", color=Color.red())
        embed.add_field(name="Coins:", value=data.get("coins", 0), inline=True)
        embed.add_field(name="EXP:", value=data.get("Experience", 0), inline=True)
        embed.add_field(name="Level:", value=rawData['player']['achievements'].get("bedwars_level", 0), inline=True)
        embed.add_field(name="Games Played:", value=data.get("games_played_bedwars", 0), inline=True)
        embed.add_field(name="Current Winstreak:", value=data.get("winstreak", 0), inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)

        embed.add_field(name="Wins:", value=data.get("wins_bedwars", 0), inline=True)
        embed.add_field(name="Losses:", value=data.get("losses_bedwars", 0), inline=True)
        embed.add_field(name="W/L Rate:", value=utils.getRate(data.get('wins_bedwars', 0), data.get("losses_bedwars", 0)), inline=True)
        ceilingRate, total, res = self.getCeilingRate(data=data, kills="wins_bedwars", deaths="losses_bedwars")
        embed.add_field(name=f"Wins for {ceilingRate} W/LR:", value=f"{utils.insert_commas(res)} ({utils.insert_commas(total)} total)", inline=False)

        embed.add_field(name="Kills:", value=data.get("kills_bedwars", 0), inline=True)
        embed.add_field(name="Deaths:", value=data.get("deaths_bedwars", 0), inline=True)
        embed.add_field(name="K/D Rate:", value=utils.getRate(data.get("kills_bedwars", 0), data.get("deaths_bedwars", 0)), inline=True)
        ceilingRate, total, res = self.getCeilingRate(data=data, kills="kills_bedwars", deaths="deaths_bedwars")
        embed.add_field(name=f"Kills for {ceilingRate} K/DR", value=f"{utils.insert_commas(res)} ({utils.insert_commas(total)} total)", inline=False)

        embed.add_field(name="Final Kills:", value=data.get("final_kills_bedwars", 0), inline=True)
        embed.add_field(name="Final Deaths:", value=data.get("final_deaths_bedwars", 0), inline=True)
        embed.add_field(name="Final K/D Rate:", value=utils.getRate(data.get("final_kills_bedwars", 0), data.get("final_deaths_bedwars", 0)), inline=True)
        ceilingRate, total, res = self.getCeilingRate(data=data, kills="final_kills_bedwars", deaths="final_deaths_bedwars")
        embed.add_field(name=f"Final Kills for {ceilingRate} FK/DR", value=f"{utils.insert_commas(res)} ({utils.insert_commas(total)} total)", inline=False)

        embed.add_field(name="Beds Broken:", value=data.get("beds_broken_bedwars", 0), inline=True)
        embed.add_field(name="Beds Lost:", value=data.get("beds_lost_bedwars", 0), inline=True)
        embed.add_field(name="B/L Rate:", value=utils.getRate(data.get("beds_broken_bedwars", 0), data.get("beds_lost_bedwars", 0)), inline=True)

        embed.add_field(name="Kills/Game:", value=utils.getRate(data.get("kills_bedwars", 0), data.get("games_played_bedwars", 0)), inline=True)
        embed.add_field(name="Finals/Game:", value=utils.getRate(data.get("final_kills_bedwars", 0), data.get("games_played_bedwars", 0)), inline=True)
        embed.add_field(name="Beds/Game:", value=utils.getRate(data.get("beds_broken_bedwars", 0), data.get("games_played_bedwars", 0)), inline=True)
        return embed


class MinecraftStats(commands.Cog, name="MC Stats", description="Commands for Minecraft player statistics"):
    def __init__(self, bot):
        self.bot = bot
        print("Loaded", __name__)


    @staticmethod
    async def hasLink(ctx, player):
        if len(player) == 0:
            member = ctx.author
        elif ctx.message.mentions:
            member = await Converters.MemberConverter.convert(ctx, player[0])
        else:
            member = None
            player = player[0]
        if member:
            player = r.get(member.id)
            if player == None:
                raise commands.BadArgument(f"{str(member)} has not linked their Discord to their Minecraft account")
            player = player.decode('utf-8')
        return player


    @commands.command(description="<player> can be a Minecraft player or left blank to get your own statistics", help="Gets statistics of a Minecraft player", aliases=['mc'])
    async def minecraft(self, ctx, *player):
        player = await self.hasLink(ctx, player)
        uuid = MojangAPI.get_uuid(player)
        if not uuid:
            raise commands.BadArgument(f'Player "{player}" not found.')
        info = MojangAPI.get_profile(uuid)
        embed = discord.Embed(title=f"{info.name}'s Minecraft Profile", description=f"Stats for {info.name}", color=Color.red())
        embed.set_thumbnail(url=MinecraftSkinFetcher.head(uuid))
        embed.set_footer(text="Stats provided using the Mojang APIs \nAvatars and skins from Crafatar")
        embed.add_field(name="Username:", value=info.name, inline=True)
        embed.add_field(name="UUID:", value=info.id, inline=True)

        name_history = MojangAPI.get_name_history(uuid)
        history = ""
        for entry in name_history:
            history += f"\n{entry['name']}"
        embed.add_field(name="Past Usernames (From oldest down to latest):", value=history, inline=False)

        await ctx.reply(embed=embed)


    @commands.command(help="Links your Discord to a Hypixel account", aliases=['mclink'])
    async def mcverify(self, ctx, player):
        uuid = MojangAPI.get_uuid(player)
        if not uuid:
            raise commands.BadArgument(f'Player "{player}" not found.')

        data = await utils.getJSON(f"https://api.hypixel.net/player?key={EnvVars.HYPIXEL_KEY}&uuid={uuid}")
        if not data.get('player') or not data['player'].get('socialMedia'):
            raise commands.BadArgument(f"{player} has not played Hypixel or has not linked Discord and cannot verify their account. If this is your account, log into Hypixel and run /discord")

        link = data['player']['socialMedia']['links'].get('DISCORD') if data['player']['socialMedia'].get('links') else None
        if link == None:
            raise commands.BadArgument(f"**{data['player']['displayname']}** has no Discord user linked to their Hypixel account")
        if link == str(ctx.author):
            await ctx.reply(f"Your Discord account is now linked to **{data['player']['displayname']}**. Anyone can see your Minecraft and Hypixel stats by doing `'?mc {ctx.author.mention}'` and running `?mc` will bring up your own Minecraft stats")
            r.set(ctx.author.id, data['player']['displayname'])
        else:
            raise commands.BadArgument(f"**{data['player']['displayname']}** can only be linked to {data['player']['socialMedia']['links']['DISCORD']}")


    @commands.command(description="<player> can be a Minecraft player or left blank to get your own skin", help="Gets the skin of a Minecraft player")
    async def skin(self, ctx, *player):
        player = await self.hasLink(ctx, player)
        uuid = MojangAPI.get_uuid(player)
        if not uuid:
            raise commands.BadArgument(f'Player "{player}" not found.')
        info = MojangAPI.get_profile(uuid)
        embed=discord.Embed(title=f"{info.name}'s Skin", description=f"Full render of {info.name}'s skin", color=Color.red())
        embed.set_footer(text="Stats provided using the Mojang API \nAvatars and skins from Crafatar")
        embed.set_image(url=MinecraftSkinFetcher.body(uuid))
        await ctx.reply(embed=embed)


    @commands.command(description="<player> can be a Minecraft player or left blank to get your own statistics", help="Gets the Hypixel statistics of a Minecraft player")
    async def hypixel(self, ctx, *player):
        player = await self.hasLink(ctx, player)
        uuid = MojangAPI.get_uuid(player)
        if not uuid:
            raise commands.BadArgument(f'Player "{player}" not found.')
        data = await utils.getJSON(f"https://api.hypixel.net/player?key={EnvVars.HYPIXEL_KEY}&uuid={uuid}")
        if not data.get('player') or not data['player'].get('displayname'):
            raise commands.BadArgument(f"{player} has not played Hypixel")
        embed = discord.Embed(title=f"{data['player']['displayname']}'s Hypixel Profile", description=f"Hypixel stats for {data['player']['displayname']}", color=Color.red())
        embed.set_thumbnail(url=MinecraftSkinFetcher.head(data['player']['uuid']))
        embed.set_footer(text=f"Stats provided using the Mojang and Hypixel APIs \nAvatars from Crafatar \nStats requested by {str(ctx.author)}")
        status = None
        ts = data['player'].get('lastLogin')
        if ts:
            ts /= 1000
            d = utils.TimefromStamp(ts, ctx.guild.region)
        else:
            d = "Never"
            status = "Offline"

        ts = data['player'].get('lastLogout')
        if ts:
            ts /= 1000
            d1 = utils.TimefromStamp(ts, ctx.guild.region)
        else:
            d1 = "Never"
            status = "Online"

        if not status:
            if data['player']['lastLogout'] < data['player']['lastLogin']:
                status = "Online"
            else:
                status = "Offline"
        try:
            rank = data['player']['rank']
        except KeyError:
            try:
                if (data['player']['monthlyPackageRank'] and data['player']['monthlyPackageRank'] != 'NONE'):
                    rank = ("MVP++")
                else:
                    rank = (data['player']['newPackageRank'])
            except KeyError:
                rank = data['player'].get('newPackageRank', "None")

        rank = rank.replace("_PLUS","+")
        embed.add_field(name="Status:", value=status, inline=True)
        embed.add_field(name="Rank:", value=rank, inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="Last Logged In:", value=(d), inline=True)
        embed.add_field(name="Last Logged Off:", value=(d1), inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        mostRecentGameType = data['player'].get('mostRecentGameType', "None").lower().capitalize()
        embed.add_field(name="Last Game Played:", value=(mostRecentGameType))
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        EXP = round(data['player'].get("networkExp", 0))
        level = round(1 + (-8750. + (8750**2 + 5000*EXP)**.5) // 2500)
        karma = data['player'].get("karma", 0)
        embed.add_field(name="EXP:", value=EXP, inline=True)
        embed.add_field(name="Level:", value=level, inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="Karma:", value=karma, inline=True)
        friends = await utils.getJSON(f"https://api.hypixel.net/friends?key={EnvVars.HYPIXEL_KEY}&uuid={data['player']['uuid']}")
        embed.add_field(name="Friends:", value=len(friends.get('records', [])), inline=True)
        id = await utils.getJSON(f"https://api.hypixel.net/findGuild?key={EnvVars.HYPIXEL_KEY}&byUuid={data['player']['uuid']}")
        try:
            guild = await utils.getJSON(f"https://api.hypixel.net/guild?key={EnvVars.HYPIXEL_KEY}&id={id['guild']}")
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            embed.add_field(name="Guild:", value=guild['guild']['name'], inline=True)
            embed.add_field(name="Guild Members:", value=len(guild['guild']['members']),  inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)
        except KeyError:
            embed.add_field(name="Guild:", value="None", inline=True)
        if data['player'].get("socialMedia") and data['player']['socialMedia'].get('links'):
            for link in data['player']['socialMedia']['links']:
                embed.add_field(name=link, value=data['player']['socialMedia']['links'][link], inline=False)

        embed = utils.insert_commas_to_embed(embed)
        await ctx.reply(embed=embed)


    @commands.command(description="<player> can be a Minecraft player or left blank to get your own Hypixel guild statistics", help="Gets the statistics of a Hypixel guild of a Minecraft player")
    async def hypixelguild(self, ctx, *player_or_guild):

        def getGuildLevel(exp):
            EXP_NEEDED = [100000, 150000, 250000, 500000, 750000, 1000000, 1250000, 1500000, 2000000, 2500000, 2500000, 2500000, 2500000, 2500000, 3000000]

            level = 0

            for i in range(1000):

                need = 0
                if  i >= len(EXP_NEEDED):
                    need = EXP_NEEDED[len(EXP_NEEDED) - 1]
                else:
                    need = EXP_NEEDED[i]

                if (exp - need) < 0:
                    return math.floor(((level + (exp / need)) * 100) // 100)

                level += 1
                exp -= need

            return 1000


        if len(player_or_guild) == 0:
            member = ctx.author

        elif ctx.message.mentions:
            member = await Converters.MemberConverter.convert(ctx, player_or_guild[0])

        else:
            member = False

            guildName = " ".join(player_or_guild)
            guild = await utils.getJSON(f"https://api.hypixel.net/guild?key={EnvVars.HYPIXEL_KEY}&name={guildName}")
            if not guild.get('guild'):
                raise commands.BadArgument(f"Guild {guildName} not found")

        if member:
            player = r.get(member.id)
            if player == None:
                raise commands.BadArgument(f"{str(member)} has not linked their Discord to their Minecraft account")
            player = player.decode('utf-8')

            uuid = MojangAPI.get_uuid(player)
            if not uuid:
                raise commands.BadArgument(f'Player "{player}" not found')

            guild = await utils.getJSON(f"https://api.hypixel.net/guild?key={EnvVars.HYPIXEL_KEY}&player={uuid}")
            if not guild.get('guild'):
                raise commands.BadArgument(f"Player {player} is not in a guild")


        embed = discord.Embed(title=f"{guild['guild']['name']}'s Guild Profile", description=f"Guild stats for {guild['guild']['name']}", color=Color.red())
        embed.set_footer(text=f"Stats provided using the Mojang and Hypixel APIs \nAvatars from Crafatar \nStats requested by {str(ctx.author)}")
        embed.add_field(name="Guild:", value=guild['guild']['name'], inline=True)
        embed.add_field(name="ID:", value=len(guild['guild']['_id']), inline=True)
        embed.add_field(name="Members:", value=len(guild['guild']['members']), inline=True)
        embed.add_field(name="EXP:", value=guild['guild']['exp'],  inline=True)
        embed.add_field(name="Level:", value=getGuildLevel(guild['guild']['exp']))
        embed.add_field(name="Public:", value=utils.convertBooltoExpress(guild['guild'].get('publiclyListed')))
        embed.add_field(name="Winners:", value=guild['guild']['achievements'].get('WINNERS', 0))
        embed.add_field(name="Experience Kings:", value=guild['guild']['achievements'].get('EXPERIENCE_KINGS', 0))
        embed.add_field(name="Online Players:", value=guild['guild']['achievements'].get('ONLINE_PLAYERS'))

        if member:
            embed.set_thumbnail(url=MinecraftSkinFetcher.head(uuid))
            for member in guild['guild']['members']:
                if member['uuid'] == uuid:
                    embed.add_field(name="\u200b", value="\u200b", inline=False)
                    embed.add_field(name="Player Stats:", value="\u200b", inline=False)
                    embed.add_field(name="Rank", value=member['rank'])
                    embed.add_field(name="Quest Participation", value=member.get('questParticipation', 0))
                    break

        embed = utils.insert_commas_to_embed(embed)
        await ctx.reply(embed=embed)


    @staticmethod
    def getCeilingRate(*, data, kills, deaths):
        ceilingRate = math.ceil(utils.getRate(data.get(kills, 0), data.get(deaths, 0)))
        total = ceilingRate * data.get(deaths, 0)
        res = max(0, total - data.get(kills, 0))
        return ceilingRate, total, res


    @staticmethod
    def write_roman(num : int):
        roman = OrderedDict()
        roman[1000] = "M"
        roman[900] = "CM"
        roman[500] = "D"
        roman[400] = "CD"
        roman[100] = "C"
        roman[90] = "XC"
        roman[50] = "L"
        roman[40] = "XL"
        roman[10] = "X"
        roman[9] = "IX"
        roman[5] = "V"
        roman[4] = "IV"
        roman[1] = "I"
        def roman_num(num : int):
            for r in roman.keys():
                x, y = divmod(num, r)
                yield roman[r] * x
                num -= (r * x)
                if num <= 0:
                    break
        return "".join([a for a in roman_num(num)])


    @commands.command(description=f"<player> can be a Minecraft player or left blank to get your own Bedwars statistics \n Mode can be {utils.getHypixelHelp(HypixelModes.bedwarsModes)} or left blank for overall statistics", help="Gets the Bedwars statistics of a Minecraft player", aliases=['bw', 'bws'])
    async def bedwars(self, ctx, *player_and_mode):
        BedwarsStatFetcher = await BedwarsStatFetcher.get_data(ctx, player_and_mode)
        await ctx.reply(embed=embed)


    @commands.command(description=f"<player> can be a Minecraft player or left blank to get your own Bedwars statistics \n Mode can be {utils.getHypixelHelp(HypixelModes.skywarsModes)} or left blank for overall statistics", help="Gets the SkyWars statistics of a Minecraft player", aliases=['sw', 'sws'])
    async def skywars(self, ctx, *player_and_mode):
        def getSkyWarsLevel(xp : int):
            if xp == 0:
                return 0
            if xp >= 15000:
                return math.floor((xp - 15000) / 10000. + 12)
            else:
                for number in xps:
                    if not xp > number:
                        closestnumber = xps[xps.index(number)-1]
                        break
                return math.floor(xps.index(closestnumber) + 1)

        xps = [0, 20, 70, 150, 250, 500, 1000, 2000, 3500, 6000, 10000, 15000]

        mode = " ".join(player_and_mode)
        if len(player_and_mode) == 0 or utils.multi_key_dict_get(HypixelModes.skywarsModes, mode) != None:
            member = ctx.author
            if len(player_and_mode) > 0:
                player_and_mode = list(player_and_mode)
                player_and_mode.insert(0, "")
                player_and_mode = tuple(player_and_mode)
        elif ctx.message.mentions:
            member = await Converters.MemberConverter.convert(ctx, player_and_mode[0])
        else:
            member = None
            player = player_and_mode[0]
        if member:
            player = r.get(member.id)
            if player == None:
                raise commands.BadArgument(f"{str(member)} has not linked their Discord to their Minecraft account. Run {utils.determine_prefix(ctx.bot, ctx, clean=True)}mclink")
            player = player.decode("utf-8")
        uuid = MojangAPI.get_uuid(player)
        if not uuid:
            raise commands.BadArgument(f'Player "{player}" not found.')
        rawData = await utils.getJSON(f"https://api.hypixel.net/player?key={EnvVars.HYPIXEL_KEY}&uuid={uuid}")
        if not rawData.get('player') or not rawData['player'].get('stats') or not rawData['player']['stats'].get("SkyWars"):
            raise commands.BadArgument(f"{player} has not played SkyWars")
        data = rawData['player']['stats']['SkyWars']
        if len(player_and_mode) <= 1:
            embed = discord.Embed(title=f"{rawData['player']['displayname']}'s Hypixel Skywars Profile", description=f"Skywars stats for {rawData['player']['displayname']}", color=Color.red())
            embed.add_field(name="Coins:", value=data.get('coins', 0), inline=True)
            embed.add_field(name="EXP:", value=data.get('skywars_experience', 0), inline=True)
            embed.add_field(name="Level:", value=getSkyWarsLevel(data.get('skywars_experience', 0)), inline=True)
            embed.add_field(name="Games Played:", value=data.get('wins', 0) + data.get('losses', 0), inline=True)
            embed.add_field(name="Current Winstreak:", value=data.get('win_streak', 0), inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)

            embed.add_field(name="Souls:", value=data.get("souls", 0), inline=True)
            embed.add_field(name="Heads:", value=data.get("heads", 0), inline=True)
            embed.add_field(name="Assists:", value=data.get('assists', 0), inline=True)

            embed.add_field(name="Kills:", value=data.get('kills', 0), inline=True)
            embed.add_field(name="Deaths:", value=data.get('deaths', 0), inline=True)
            embed.add_field(name="K/D Rate:", value=utils.getRate(data.get('kills', 0), data.get('deaths', 0)), inline=True)
            ceilingRate, total, res = self.getCeilingRate(data=data, kills="kills", deaths="deaths")
            embed.add_field(name=f"Kills for {ceilingRate} K/DR ", value=f"{utils.insert_commas(res)} ({utils.insert_commas(total)} total)", inline=False)

            embed.add_field(name="Wins:", value=data.get('wins', 0), inline=True)
            embed.add_field(name="Losses:", value=data.get('losses', 0), inline=True)
            embed.add_field(name="W/L Rate:", value=utils.getRate(data.get('wins', 0), data.get('losses', 0)), inline=True)
            ceilingRate, total, res = self.getCeilingRate(data=data, kills="wins", deaths="losses")
            embed.add_field(name=f"Wins for {ceilingRate} W/LR", value=f"{utils.insert_commas(res)} ({utils.insert_commas(total)} total)", inline=False)

            embed.add_field(name="Kills/Game:", value=utils.getRate(data.get('kills', 0), (data.get('wins', 0)+data.get('losses', 0))), inline=True)
            embed.add_field(name="Assists/Game:", value=utils.getRate(data.get('assists', 0), (data.get('wins', 0)+data.get('losses', 0))), inline=True)
            embed.add_field(name="Souls/Game:", value=utils.getRate(data.get('souls', 0), (data.get('wins', 0)+data.get('losses', 0))), inline=True)
        else:
            player_and_mode = list(player_and_mode)
            player_and_mode.pop(0)
            joinedmode = " ".join(player_and_mode)
            joinedmode = (utils.multi_key_dict_get(HypixelModes.skywarsModes, joinedmode))
            if joinedmode == "solos normal":
                embed = discord.Embed(title=f"{rawData['player']['displayname']}'s Hypixel Solos Normal Skywars Profile", description=f"Solo Normal Skywars stats for {rawData['player']['displayname']}", color=Color.red())
                embed.add_field(name="EXP:", value=data.get('skywars_experience', 0), inline=True)
                embed.add_field(name="Level:", value=getSkyWarsLevel(data.get('skywars_experience', 0)), inline=True)
                embed.add_field(name="Games Played:", value=(data.get('wins_solo', 0) - data.get('wins_solo_insane', 0)) + (data.get('losses_solo', 0) - data.get('losses_solo_insane', 0)), inline=True)
                embed.add_field(name="Kills:", value=data.get('kills_solo', 0) - data.get('kills_solo_insane', 0), inline=True)
                embed.add_field(name="Deaths:", value=data.get('deaths_solo', 0) - data.get('deaths_solo_insane', 0), inline=True)
                embed.add_field(name="K/D Rate:", value=utils.getRate(data.get('kills_solo', 0) - data.get('kills_solo_insane', 0), data.get('deaths_solo', 0) - data.get('deaths_solo_insane', 0)), inline=True)
                embed.add_field(name="Wins:", value=data.get('wins_solo', 0) - data.get('wins_solo_insane', 0), inline=True)
                embed.add_field(name="Losses:", value=data.get('losses_solo', 0) - data.get('losses_solo_insane', 0), inline=True)
                embed.add_field(name="W/L Rate:", value=utils.getRate(data.get('wins_solo', 0) - data.get('wins_solo_insane', 0), data.get('losses_solo', 0) - data.get('losses_solo_insane', 0)), inline=True)
            elif joinedmode == "solos insane":
                embed = discord.Embed(title=f"{rawData['player']['displayname']}'s Hypixel Solos Insane Skywars Profile", description=f"Solo Insane Skywars stats for {rawData['player']['displayname']}", color=Color.red())
                embed.add_field(name="EXP:", value=data.get('skywars_experience', 0), inline=True)
                embed.add_field(name="Level:", value=getSkyWarsLevel(data.get('skywars_experience', 0)), inline=True)
                embed.add_field(name="Games Played:", value=data.get('wins_solo_insane', 0) + data.get('losses_solo_insane', 0), inline=True)
                embed.add_field(name="Kills:", value=data.get('kills_solo_insane', 0), inline=True)
                embed.add_field(name="Deaths:", value=data.get('deaths_solo_insane', 0), inline=True)
                embed.add_field(name="K/D Rate:", value=utils.getRate(data.get("kills_solo_insane", 0), data.get("deaths_solo_insane", 0)), inline=True)
                embed.add_field(name="Wins:", value=data.get("wins_solo_insane", 0), inline=True)
                embed.add_field(name="Losses:", value=data.get("losses_solo_insane", 0), inline=True)
                embed.add_field(name="W/L Rate:", value=utils.getRate(data.get("wins_solo_insane", 0), data.get("losses_solo_insane", 0)), inline=True)
            elif joinedmode == "teams normal":
                embed = discord.Embed(title=f"{rawData['player']['displayname']}'s Hypixel Teams Normal Skywars Profile", description=f"Teams Normal Skywars stats for {rawData['player']['displayname']}", color=Color.red())
                embed.add_field(name="EXP:", value=data.get("skywars_experience", 0), inline=True)
                embed.add_field(name="Level:", value=getSkyWarsLevel(data.get("skywars_experience", 0)), inline=True)
                embed.add_field(name="Games Played:", value=(data.get("wins_team", 0) - data.get("wins_team_insane", 0)) + (data.get("losses_team", 0) - data.get("losses_team_insane", 0)), inline=True)
                embed.add_field(name="Kills:", value=data.get("kills_team", 0) - data.get("kills_team_insane", 0), inline=True)
                embed.add_field(name="Deaths:", value=data.get("deaths_team", 0) - data.get("deaths_team_insane", 0), inline=True)
                embed.add_field(name="K/D Rate:", value=utils.getRate(data.get("kills_team", 0) - data.get("kills_team_insane", 0), data.get("deaths_team", 0) - data.get("deaths_team_insane", 0)), inline=True)
                embed.add_field(name="Wins:", value=data.get("wins_team", 0) - data.get("wins_team_insane", 0), inline=True)
                embed.add_field(name="Losses:", value=data.get("losses_team", 0) - data.get("losses_team_insane", 0), inline=True)
                embed.add_field(name="W/L Rate:", value=utils.getRate(data.get("wins_team", 0) - data.get("wins_team_insane", 0), data.get("losses_team", 0) - data.get("losses_team_insane", 0)), inline=True)
            elif joinedmode == "teams insane":
                embed = discord.Embed(title=f"{rawData['player']['displayname']}'s Hypixel Teams Insane Skywars Profile", description=f"Teams Insane Skywars stats for {rawData['player']['displayname']}", color=Color.red())
                embed.add_field(name="EXP:", value=data.get('skywars_experience', 0), inline=True)
                embed.add_field(name="Level:", value=getSkyWarsLevel(data.get("skywars_experience", 0)), inline=True)
                embed.add_field(name="Games Played:", value=data.get("wins_team_insane", 0) + data.get("losses_team_insane", 0), inline=True)
                embed.add_field(name="Kills:", value=data.get("kills_team_insane", 0), inline=True)
                embed.add_field(name="Deaths:", value=data.get("deaths_team_insane", 0), inline=True)
                embed.add_field(name="K/D Rate:", value=utils.getRate(data.get("kills_team_insane", 0), data.get("deaths_team_insane", 0)), inline=True)
                embed.add_field(name="Wins:", value=data.get("wins_team_insane", 0), inline=True)
                embed.add_field(name="Losses:", value=data.get("losses_team_insane", 0), inline=True)
                embed.add_field(name="W/L Rate:", value=utils.getRate(data.get("wins_team_insane", 0), data.get("losses_team_insane", 0)), inline=True)
            else:
                raise commands.BadArgument(f"Invalid mode  \nMode can be {utils.getHypixelHelp(HypixelModes.skywarsModes)} or left blank for overall statistics")

        embed.set_thumbnail(url=MinecraftSkinFetcher.head(rawData['player']['uuid']))
        embed.set_footer(text=f"Stats provided using the Mojang and Hypixel APIs \nAvatars from Crafatar \nStats requested by {str(ctx.author)}")

        embed = utils.insert_commas_to_embed(embed)
        await ctx.reply(embed=embed)


    @commands.command(description=f"<player> can be a Minecraft player or left blank to get your own Duels statistics \n Mode can be {utils.getHypixelHelp(HypixelModes.duelModes)} or left blank to get overall statistics", help="Gets the Duels statistics of a Minecraft player")
    async def duels(self, ctx, *player_and_mode):
        ranks = ['godlike', 'grandmaster', 'legend', 'master', 'diamond', 'gold', 'iron', 'rookie']
        bridgeModes = ["bridge_3v3v3v3", "bridge_doubles", "bridge_four", "bridge_2v2v2v2"]
        prestige = None

        mode = " ".join(player_and_mode)
        if len(player_and_mode) == 0 or utils.multi_key_dict_get(HypixelModes.duelModes, mode) != None:
            member = ctx.author
            if len(player_and_mode) > 0:
                player_and_mode = list(player_and_mode)
                player_and_mode.insert(0, "")
                player_and_mode = tuple(player_and_mode)
        elif ctx.message.mentions:
            member = await Converters.MemberConverter.convert(ctx, player_and_mode[0])
        else:
            member = None
            player = player_and_mode[0]
        if member:
            player = r.get(member.id)
            if player == None:
                raise commands.BadArgument(f"{str(member)} has not linked their Discord to their Minecraft account. Run {utils.determine_prefix(ctx.bot, ctx, clean=True)}mclink")
            player = player.decode("utf-8")
        uuid = MojangAPI.get_uuid(player)
        if not uuid:
            raise commands.BadArgument(f'Player "{player}" not found.')
        rawData = await utils.getJSON(f"https://api.hypixel.net/player?key={EnvVars.HYPIXEL_KEY}&uuid={uuid}")
        if rawData.get("success") == False:
            raise commands.BadArgument(f"Hypixel API returned an error: {rawData.get('cause')}")
        if not rawData.get('player') or not rawData['player'].get('stats') or not rawData['player']['stats'].get('Duels'):
            raise commands.BadArgument(f"{player} has not played Duels")
        data = rawData['player']['stats']['Duels']
        if len(player_and_mode) < 2:
            embed = discord.Embed(title=f"{rawData['player']['displayname']}'s Hypixel Duels Profile", description=f"Duels stats for {rawData['player']['displayname']}", color=Color.red())
            mode = "all_modes"
            for ra in ranks:
                prestigeNumber = data.get(f'{mode}_{ra}_title_prestige', None)
                if prestigeNumber:
                    if ra == "rookie" and prestigeNumber == 1:
                        break
                    prestige = f'{ra.capitalize()} {self.write_roman(prestigeNumber)}'
                    break
            embed.add_field(name="Games Played:", value=data.get('wins', 0) + data.get('losses', 0), inline=True)
            embed.add_field(name="Winstreak:", value=data.get('current_winstreak', 0), inline=True)
            embed.add_field(name="Best Winstreak:", value=data.get('best_overall_winstreak', 0), inline=True)
            embed.add_field(name="Coins:", value=data.get('coins', 0), inline=True)
            embed.add_field(name="Prestige:", value=prestige, inline=True)
            embed.add_field(name="\u200b", value="\u200b")

            embed.add_field(name="Kills:", value=data.get('kills', 0), inline=True)
            embed.add_field(name="Deaths:", value=data.get('deaths', 0), inline=True)
            embed.add_field(name="K/D Rate:", value=utils.getRate(data.get('kills', 0), data.get('deaths', 0)), inline=True)
            ceilingRate, total, res = self.getCeilingRate(data=data, kills="kills", deaths="deaths")
            embed.add_field(name=f"Kills for {ceilingRate} K/DR", value=f"{utils.insert_commas(res)} ({utils.insert_commas(total)} total)", inline=False)

            embed.add_field(name="Wins:", value=data.get('wins', 0), inline=True)
            embed.add_field(name="Losses:", value=data.get('losses', 0), inline=True)
            embed.add_field(name="W/L Rate:", value=utils.getRate(data.get('wins', 0), data.get('losses', 0)), inline=True)
            ceilingRate, total, res = self.getCeilingRate(data=data, kills="wins", deaths="losses")
            embed.add_field(name=f"Wins for {ceilingRate} W/LR", value=f"{utils.insert_commas(res)} ({utils.insert_commas(total)} total)", inline=False)

            embed.add_field(name="Arrows Shot:", value=data.get('bow_shots', 0), inline=True)
            embed.add_field(name="Arrows Hit:", value=data.get('bow_hits', 0), inline=True)
            embed.add_field(name="Arrows Missed:", value=data.get('bow_shots', 0) - data.get('bow_hits', 0), inline=True)
            embed.add_field(name="Arrow H/S Rate:", value=utils.getRate(data.get('bow_hits', 0), data.get('bow_shots', 0)), inline=False)
            embed.add_field(name="Melee Swings:", value=data.get('melee_swings', 0), inline=True)
            embed.add_field(name="Melee Hits:", value=data.get('melee_hits', 0), inline=True)
            embed.add_field(name="Melee Missed:", value=data.get('melee_swings', 0) - data.get('melee_hits', 0), inline=True)
            embed.add_field(name="Melee H/S Rate:", value=utils.getRate(data.get('melee_hits', 0), data.get('melee_swings', 0)), inline=True)
        else:
            player_and_mode = list(player_and_mode)
            player_and_mode.pop(0)
            mode = " ".join(player_and_mode)
            if not mode in HypixelModes.duelModes:
                raise commands.BadArgument(f'Mode "{mode}" not found. \nMode can be {utils.getHypixelHelp(HypixelModes.duelModes)} or left blank for overall statistics')
            embed = discord.Embed(title=f"{rawData['player']['displayname']}'s Hypixel {mode.capitalize()} Duel Profile", description=f"{mode.capitalize()} duel stats for {rawData['player']['displayname']}", color=Color.red())
            for ra in ranks:
                prestigeNumber = data.get(f'{mode.split()[0]}_{ra}_title_prestige', None)
                if prestigeNumber:
                    if ra == "rookie" and prestigeNumber == 1:
                        break
                    prestige = f'{ra.capitalize()} {self.write_roman(prestigeNumber)}'
                    break
            mode = HypixelModes.duelModes[mode]
            embed.add_field(name="Prestige", value=prestige, inline=True)
            embed.add_field(name="Current Winstreak", value=data.get(f"current_winstreak_mode_{mode}", 0), inline=True)
            embed.add_field(name="Best Winstreak", value=data.get(f"best_winstreak_mode_{mode}", 0), inline=True)

            if mode == "bridge_duel":
                mode = "bridge"
            if mode in bridgeModes:
                mode += "_bridge"

            embed.add_field(name="Kills:", value=data.get(f'{mode}_kills', 0), inline=True)
            embed.add_field(name="Deaths:", value=data.get(f'{mode}_deaths', 0), inline=True)
            embed.add_field(name="K/D Rate:", value=utils.getRate(data.get(f'{mode}_kills', 0), data.get(f'{mode}_deaths', 0)), inline=True)
            ceilingRate, total, res = self.getCeilingRate(data=data, kills=f"{mode}_kills", deaths=f"{mode}_deaths")
            embed.add_field(name=f"Kills for {ceilingRate} K/DR", value=f"{utils.insert_commas(res)} ({utils.insert_commas(total)} total)", inline=False)

            if mode == "bridge":
                mode = "bridge_duel"
            if mode.endswith("_bridge"):
                mode = mode[:-7]

            embed.add_field(name="Wins:", value=data.get(f'{mode}_wins', 0), inline=True)
            embed.add_field(name="Losses:", value=data.get(f'{mode}_losses', 0), inline=True)
            embed.add_field(name="W/L Rate:", value=utils.getRate(data.get(f'{mode}_wins', 0), data.get(f'{mode}_losses', 0)), inline=True)
            ceilingRate, total, res = self.getCeilingRate(data=data, kills=f"{mode}_wins", deaths=f"{mode}_losses")
            embed.add_field(name=f"Wins for {ceilingRate} W/LR", value=f"{utils.insert_commas(res)} ({utils.insert_commas(total)} total)", inline=False)

        embed.set_thumbnail(url=MinecraftSkinFetcher.head(rawData['player']['uuid']))
        embed.set_footer(text=f"Stats provided using the Mojang and Hypixel APIs \nAvatars from Crafatar \nStats requested by {str(ctx.author)}")

        embed = utils.insert_commas_to_embed(embed)
        await ctx.reply(embed=embed)




def setup(bot):
    bot.add_cog(MinecraftStats(bot))
