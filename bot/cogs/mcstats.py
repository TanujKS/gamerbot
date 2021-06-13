from utils import utils, constants
from utils.constants import r, Converters, EnvVars, Color
from cogs import paginator

import discord
from discord.ext import commands
from discord.utils import get

import math

import time
from datetime import datetime

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
    modes = {'None': 'None'}

    def __init__(self, *, player, mode, ctx, rawData, data):
        self.player = player
        self.mode = mode
        self.rawData = rawData
        self.data = data
        self.ctx = ctx


    @classmethod
    def getHypixelHelp(cls):
        help = ""
        for key, value in cls.modes.items():
            if isinstance(key, tuple):
                help += key[0]
            elif isinstance(key, str):
                help += key
            help += ", "
        help = help[:-2]
        return help


    @classmethod
    def check_mode(cls, mode):
        mode = utils.multi_key_dict_get(cls.modes, mode)
        if not mode:
            raise commands.BadArgument(f"Invalid mode \nMode can be {cls.getHypixelHelp()}")
        return mode


    @classmethod
    def get_display_mode(cls, mode):
        display_mode = utils.get_key_from_value(cls.modes, mode)
        if isinstance(display_mode, tuple):
            display_mode = display_mode[0]
        display_mode = display_mode.capitalize()
        return display_mode


    @classmethod
    async def has_link(cls, ctx, player_and_mode: tuple):
        player_and_mode = list(player_and_mode)

        if len(player_and_mode) == 0:
            member = ctx.author
            mode = None

        elif utils.multi_key_dict_get(cls.modes, " ".join(player_and_mode)):
            member = ctx.author
            mode = utils.multi_key_dict_get(cls.modes, " ".join(player_and_mode))

        elif ctx.message.mentions:
            member = await Converters.MemberConverter.convert(ctx, player_and_mode[0])
            player_and_mode.pop(0)
            if player_and_mode:
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

        return player, uuid, mode


    @classmethod
    async def get_raw_data(cls, ctx: commands.context, player_and_mode: tuple):
        player, uuid, mode = await cls.has_link(ctx, player_and_mode)

        rawData = await utils.getJSON(f"https://api.hypixel.net/player?key={EnvVars.HYPIXEL_KEY}&uuid={uuid}")
        if rawData.get("success") == None:
            raise commands.BadArgument(rawData.get('cause'))

        return player, mode, rawData


    def finalize(self, embed):
        embed.set_thumbnail(url=MinecraftSkinFetcher.head(self.rawData['player']['uuid']))
        embed.set_footer(text=f"Stats provided using the Mojang and Hypixel APIs \nAvatars from Crafatar \nStats requested by {str(self.ctx.author)}")
        embed = utils.insert_commas_to_embed(embed)
        return embed


    async def all_stats(self):
        rawData = self.rawData
        data = self.data

        Paginator = paginator.Paginator(self.ctx.bot)
        Paginator.add_page(self.finalize(self.overall_stats()))

        for alias, mode in self.modes.items():
            Paginator.add_page(self.finalize(self.mode_stats(mode)))

        await Paginator.send_page(ctx=self.ctx)


    async def send(self, *, paginator=True):
        if self.mode == None:
            if paginator:
                return await self.all_stats()
            else:
                embed = self.overall_stats()
        else:
            embed = self.mode_stats(self.mode)
        embed = self.finalize(embed)
        await self.ctx.reply(embed=embed)


class BedwarsStatFetcher(HypixelStatFetcher):
    modes =  {("solos", "solo", "ones"): "eight_one", ("doubles", "double", "twos"): "eight_two", ("3s", "triples", "threes", "3v3v3v3"): "four_three", ("4s", "4v4v4v4", "quadruples", "fours"): "four_four", "4v4": "two_four"}


    @classmethod
    async def get_data(cls, ctx: commands.context, player_and_mode):
        player, mode, rawData = await cls.get_raw_data(ctx, player_and_mode)

        if not rawData.get('player') or not rawData['player'].get('stats') or not rawData['player']['stats'].get("Bedwars"):
            raise commands.BadArgument(f"{player} has not played Bedwars")

        data = rawData['player']['stats']['Bedwars']

        return cls(player=player, mode=mode, ctx=ctx, rawData=rawData, data=data)


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
        ceilingRate, total, res = utils.getCeilingRate(data.get("wins_bedwars", 0), data.get("losses_bedwars", 0))
        embed.add_field(name=f"Wins for {ceilingRate} W/LR:", value=f"{utils.insert_commas(res)} ({utils.insert_commas(total)} total)", inline=False)

        embed.add_field(name="Kills:", value=data.get("kills_bedwars", 0), inline=True)
        embed.add_field(name="Deaths:", value=data.get("deaths_bedwars", 0), inline=True)
        embed.add_field(name="K/D Rate:", value=utils.getRate(data.get("kills_bedwars", 0), data.get("deaths_bedwars", 0)), inline=True)
        ceilingRate, total, res = utils.getCeilingRate(data.get("kills_bedwars", 0), data.get("deaths_bedwars", 0))
        embed.add_field(name=f"Kills for {ceilingRate} K/DR", value=f"{utils.insert_commas(res)} ({utils.insert_commas(total)} total)", inline=False)

        embed.add_field(name="Final Kills:", value=data.get("final_kills_bedwars", 0), inline=True)
        embed.add_field(name="Final Deaths:", value=data.get("final_deaths_bedwars", 0), inline=True)
        embed.add_field(name="Final K/D Rate:", value=utils.getRate(data.get("final_kills_bedwars", 0), data.get("final_deaths_bedwars", 0)), inline=True)
        ceilingRate, total, res = utils.getCeilingRate(data.get("final_kills_bedwars", 0), data.get("final_deaths_bedwars", 0))
        embed.add_field(name=f"Final Kills for {ceilingRate} FK/DR", value=f"{utils.insert_commas(res)} ({utils.insert_commas(total)} total)", inline=False)

        embed.add_field(name="Beds Broken:", value=data.get("beds_broken_bedwars", 0), inline=True)
        embed.add_field(name="Beds Lost:", value=data.get("beds_lost_bedwars", 0), inline=True)
        embed.add_field(name="B/L Rate:", value=utils.getRate(data.get("beds_broken_bedwars", 0), data.get("beds_lost_bedwars", 0)), inline=True)

        embed.add_field(name="Kills/Game:", value=utils.getRate(data.get("kills_bedwars", 0), data.get("games_played_bedwars", 0)), inline=True)
        embed.add_field(name="Finals/Game:", value=utils.getRate(data.get("final_kills_bedwars", 0), data.get("games_played_bedwars", 0)), inline=True)
        embed.add_field(name="Beds/Game:", value=utils.getRate(data.get("beds_broken_bedwars", 0), data.get("games_played_bedwars", 0)), inline=True)

        return embed


    def mode_stats(self, mode):
        rawData = self.rawData
        data = self.data

        display_mode = self.get_display_mode(mode)

        embed = discord.Embed(title=f"{rawData['player']['displayname']}'s Hypixel {display_mode} Bedwars Profile", description=f"{display_mode} Bedwars stats for {rawData['player']['displayname']}", color=Color.red())
        embed.add_field(name="Games Played:", value=data.get(f"{mode}_games_played_bedwars", 0), inline=True)
        embed.add_field(name="Current Winstreak:", value=data.get(f"{mode}_winstreak", 0), inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)

        embed.add_field(name="Kills:", value=data.get(f"{mode}_kills_bedwars", 0), inline=True)
        embed.add_field(name="Deaths:", value=data.get(f"{mode}_deaths_bedwars", 0), inline=True)
        embed.add_field(name="K/D Rate:", value=utils.getRate(data.get(f"{mode}_kills_bedwars", 0), data.get(f"{mode}_deaths_bedwars", 0)), inline=True)
        ceilingRate, total, res = utils.getCeilingRate(data.get(f"{mode}_kills_bedwars", 0), data.get(f"{mode}_deaths_bedwars", 0))
        embed.add_field(name=f"Kills for {ceilingRate} K/DR", value=f"{utils.insert_commas(res)} ({utils.insert_commas(total)} total)", inline=False)

        embed.add_field(name="Final Kills:", value=data.get(f"{mode}_final_kills_bedwars", 0), inline=True)
        embed.add_field(name="Final Deaths:", value=data.get(f"{mode}_final_deaths_bedwars", 0), inline=True)
        embed.add_field(name="Final K/D Rate:", value=utils.getRate(data.get(f"{mode}_final_kills_bedwars", 0), data.get(f"{mode}_final_deaths_bedwars", 0)), inline=True)
        ceilingRate, total, res = utils.getCeilingRate(data.get(f"{mode}_final_kills_bedwars", 0), data.get(f"{mode}_final_deaths_bedwars", 0))
        embed.add_field(name=f"Final kills needed for {ceilingRate} FK/DR", value=f"{utils.insert_commas(res)} ({utils.insert_commas(total)} total)", inline=False)

        embed.add_field(name="Wins:", value=data.get(f"{mode}_wins_bedwars", 0), inline=True)
        embed.add_field(name="Losses:", value=data.get(f"{mode}_losses_bedwars", 0), inline=True)
        embed.add_field(name="W/L Rate", value=utils.getRate(data.get(f"{mode}_wins_bedwars", 0), data.get(f"{mode}_losses_bedwars", 0)), inline=True)
        ceilingRate, total, res = utils.getCeilingRate(data.get(f"{mode}_wins_bedwars", 0), data.get(f"{mode}_losses_bedwars", 0))
        embed.add_field(name=f"Wins needed for {ceilingRate} W/LR", value=f"{utils.insert_commas(res)} ({utils.insert_commas(total)} total)", inline=False)

        embed.add_field(name="Beds Broken:", value=data.get(f"{mode}_beds_broken_bedwars", 0), inline=True)
        embed.add_field(name="Beds Lost:", value=data.get(f"{mode}_beds_lost_bedwars", 0), inline=True)
        embed.add_field(name="B/L Rate:", value=utils.getRate(data.get(f"{mode}_beds_broken_bedwars", 0), data.get(f"{mode}_beds_lost_bedwars", 0)), inline=True)

        embed.add_field(name="Kills/Game:", value=utils.getRate(data.get(f"{mode}_kills_bedwars", 0), data.get(f"{mode}_games_played_bedwars", 0)), inline=True)
        embed.add_field(name="Finals/Game:", value=utils.getRate(data.get(f"{mode}_final_kills_bedwars", 0), data.get(f"{mode}_games_played_bedwars", 0)), inline=True)
        embed.add_field(name="Beds/Game:", value=utils.getRate(data.get(f"{mode}_beds_broken_bedwars", 0), data.get(f"{mode}_games_played_bedwars", 0)), inline=True)

        return embed


class SkyWarsStatFetcher(HypixelStatFetcher):
    modes = {("solo normal", "solos normal"): "solos normal", ("solo insane", "solos insane"): "solos insane", ("teams normal", "team normal", "doubles normal", "double normal"): "teams normal", ("teams insane", "team insane", "doubles insane", "double insane"): "teams insane"}


    @staticmethod
    def getSkyWarsLevel(xp : int):
        xps = [0, 20, 70, 150, 250, 500, 1000, 2000, 3500, 6000, 10000, 15000]

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


    @classmethod
    async def get_data(cls, ctx: commands.context, player_and_mode):
        player, mode, rawData = await cls.get_raw_data(ctx, player_and_mode)

        if not rawData.get('player') or not rawData['player'].get('stats') or not rawData['player']['stats'].get("SkyWars"):
            raise commands.BadArgument(f"{player} has not played SkyWars")
        data = rawData['player']['stats']['SkyWars']

        return cls(player=player, mode=mode, ctx=ctx, rawData=rawData, data=data)


    def overall_stats(self):
        rawData = self.rawData
        data = self.data

        embed = discord.Embed(title=f"{rawData['player']['displayname']}'s Hypixel Skywars Profile", description=f"Skywars stats for {rawData['player']['displayname']}", color=Color.red())
        embed.add_field(name="Coins:", value=data.get('coins', 0), inline=True)
        embed.add_field(name="EXP:", value=data.get('skywars_experience', 0), inline=True)
        embed.add_field(name="Level:", value=self.getSkyWarsLevel(data.get('skywars_experience', 0)), inline=True)
        embed.add_field(name="Games Played:", value=data.get('wins', 0) + data.get('losses', 0), inline=True)
        embed.add_field(name="Current Winstreak:", value=data.get('win_streak', 0), inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)

        embed.add_field(name="Souls:", value=data.get("souls", 0), inline=True)
        embed.add_field(name="Heads:", value=data.get("heads", 0), inline=True)
        embed.add_field(name="Assists:", value=data.get('assists', 0), inline=True)

        embed.add_field(name="Kills:", value=data.get('kills', 0), inline=True)
        embed.add_field(name="Deaths:", value=data.get('deaths', 0), inline=True)
        embed.add_field(name="K/D Rate:", value=utils.getRate(data.get('kills', 0), data.get('deaths', 0)), inline=True)
        ceilingRate, total, res = utils.getCeilingRate(data.get("kills", 0), data.get("deaths", 0))
        embed.add_field(name=f"Kills for {ceilingRate} K/DR ", value=f"{utils.insert_commas(res)} ({utils.insert_commas(total)} total)", inline=False)

        embed.add_field(name="Wins:", value=data.get('wins', 0), inline=True)
        embed.add_field(name="Losses:", value=data.get('losses', 0), inline=True)
        embed.add_field(name="W/L Rate:", value=utils.getRate(data.get('wins', 0), data.get('losses', 0)), inline=True)
        ceilingRate, total, res = utils.getCeilingRate(data.get("wins", 0), data.get("losses", 0))
        embed.add_field(name=f"Wins for {ceilingRate} W/LR", value=f"{utils.insert_commas(res)} ({utils.insert_commas(total)} total)", inline=False)

        embed.add_field(name="Kills/Game:", value=utils.getRate(data.get('kills', 0), (data.get('wins', 0)+data.get('losses', 0))), inline=True)
        embed.add_field(name="Assists/Game:", value=utils.getRate(data.get('assists', 0), (data.get('wins', 0)+data.get('losses', 0))), inline=True)
        embed.add_field(name="Souls/Game:", value=utils.getRate(data.get('souls', 0), (data.get('wins', 0)+data.get('losses', 0))), inline=True)

        return embed


    def mode_stats(self, mode):
        func = self.get_func_from_mode(mode)
        embed = func(self)
        return embed


    def get_func_from_mode(self, mode):
        for key, func in self.__class__.__dict__.items():
            if callable(func) and hasattr(func, "mode") and func.mode == mode:
                return func


    def set_mode(mode):
        def predicate(function):
            function.mode = mode
            return function
        return predicate


    @set_mode("solos normal")
    def solos_normal_stats(self):
        rawData = self.rawData
        data = self.data

        embed = discord.Embed(title=f"{rawData['player']['displayname']}'s Hypixel Solos Normal Skywars Profile", description=f"Solo Normal Skywars stats for {rawData['player']['displayname']}", color=Color.red())
        embed.add_field(name="EXP:", value=data.get('skywars_experience', 0), inline=True)
        embed.add_field(name="Level:", value=self.getSkyWarsLevel(data.get('skywars_experience', 0)), inline=True)
        embed.add_field(name="Games Played:", value=(data.get('wins_solo', 0) - data.get('wins_solo_insane', 0)) + (data.get('losses_solo', 0) - data.get('losses_solo_insane', 0)), inline=True)
        embed.add_field(name="Kills:", value=data.get('kills_solo', 0) - data.get('kills_solo_insane', 0), inline=True)
        embed.add_field(name="Deaths:", value=data.get('deaths_solo', 0) - data.get('deaths_solo_insane', 0), inline=True)
        embed.add_field(name="K/D Rate:", value=utils.getRate(data.get('kills_solo', 0) - data.get('kills_solo_insane', 0), data.get('deaths_solo', 0) - data.get('deaths_solo_insane', 0)), inline=True)
        embed.add_field(name="Wins:", value=data.get('wins_solo', 0) - data.get('wins_solo_insane', 0), inline=True)
        embed.add_field(name="Losses:", value=data.get('losses_solo', 0) - data.get('losses_solo_insane', 0), inline=True)
        embed.add_field(name="W/L Rate:", value=utils.getRate(data.get('wins_solo', 0) - data.get('wins_solo_insane', 0), data.get('losses_solo', 0) - data.get('losses_solo_insane', 0)), inline=True)

        return embed


    @set_mode("solos insane")
    def solos_insane_stats(self):
        rawData = self.rawData
        data = self.data

        embed = discord.Embed(title=f"{rawData['player']['displayname']}'s Hypixel Solos Insane Skywars Profile", description=f"Solo Insane Skywars stats for {rawData['player']['displayname']}", color=Color.red())
        embed.add_field(name="EXP:", value=data.get('skywars_experience', 0), inline=True)
        embed.add_field(name="Level:", value=self.getSkyWarsLevel(data.get('skywars_experience', 0)), inline=True)
        embed.add_field(name="Games Played:", value=data.get('wins_solo_insane', 0) + data.get('losses_solo_insane', 0), inline=True)
        embed.add_field(name="Kills:", value=data.get('kills_solo_insane', 0), inline=True)
        embed.add_field(name="Deaths:", value=data.get('deaths_solo_insane', 0), inline=True)
        embed.add_field(name="K/D Rate:", value=utils.getRate(data.get("kills_solo_insane", 0), data.get("deaths_solo_insane", 0)), inline=True)
        embed.add_field(name="Wins:", value=data.get("wins_solo_insane", 0), inline=True)
        embed.add_field(name="Losses:", value=data.get("losses_solo_insane", 0), inline=True)
        embed.add_field(name="W/L Rate:", value=utils.getRate(data.get("wins_solo_insane", 0), data.get("losses_solo_insane", 0)), inline=True)

        return embed


    @set_mode("teams normal")
    def teams_normal_stats(self):
        rawData = self.rawData
        data = self.data

        embed = discord.Embed(title=f"{rawData['player']['displayname']}'s Hypixel Teams Normal Skywars Profile", description=f"Teams Normal Skywars stats for {rawData['player']['displayname']}", color=Color.red())
        embed.add_field(name="EXP:", value=data.get("skywars_experience", 0), inline=True)
        embed.add_field(name="Level:", value=self.getSkyWarsLevel(data.get("skywars_experience", 0)), inline=True)
        embed.add_field(name="Games Played:", value=(data.get("wins_team", 0) - data.get("wins_team_insane", 0)) + (data.get("losses_team", 0) - data.get("losses_team_insane", 0)), inline=True)
        embed.add_field(name="Kills:", value=data.get("kills_team", 0) - data.get("kills_team_insane", 0), inline=True)
        embed.add_field(name="Deaths:", value=data.get("deaths_team", 0) - data.get("deaths_team_insane", 0), inline=True)
        embed.add_field(name="K/D Rate:", value=utils.getRate(data.get("kills_team", 0) - data.get("kills_team_insane", 0), data.get("deaths_team", 0) - data.get("deaths_team_insane", 0)), inline=True)
        embed.add_field(name="Wins:", value=data.get("wins_team", 0) - data.get("wins_team_insane", 0), inline=True)
        embed.add_field(name="Losses:", value=data.get("losses_team", 0) - data.get("losses_team_insane", 0), inline=True)
        embed.add_field(name="W/L Rate:", value=utils.getRate(data.get("wins_team", 0) - data.get("wins_team_insane", 0), data.get("losses_team", 0) - data.get("losses_team_insane", 0)), inline=True)

        return embed


    @set_mode("teams insane")
    def teams_insane_stats(self):
        rawData = self.rawData
        data = self.data

        embed = discord.Embed(title=f"{rawData['player']['displayname']}'s Hypixel Teams Insane Skywars Profile", description=f"Teams Insane Skywars stats for {rawData['player']['displayname']}", color=Color.red())
        embed.add_field(name="EXP:", value=data.get('skywars_experience', 0), inline=True)
        embed.add_field(name="Level:", value=self.getSkyWarsLevel(data.get("skywars_experience", 0)), inline=True)
        embed.add_field(name="Games Played:", value=data.get("wins_team_insane", 0) + data.get("losses_team_insane", 0), inline=True)
        embed.add_field(name="Kills:", value=data.get("kills_team_insane", 0), inline=True)
        embed.add_field(name="Deaths:", value=data.get("deaths_team_insane", 0), inline=True)
        embed.add_field(name="K/D Rate:", value=utils.getRate(data.get("kills_team_insane", 0), data.get("deaths_team_insane", 0)), inline=True)
        embed.add_field(name="Wins:", value=data.get("wins_team_insane", 0), inline=True)
        embed.add_field(name="Losses:", value=data.get("losses_team_insane", 0), inline=True)
        embed.add_field(name="W/L Rate:", value=utils.getRate(data.get("wins_team_insane", 0), data.get("losses_team_insane", 0)), inline=True)

        return embed


class DuelsStatFetcher(HypixelStatFetcher):
    modes = {"classic": "classic_duel", "uhc": "uhc_duel", "op": "op_duel", "op doubles": "op_doubles", "combo": "combo_duel", "skywars": "sw_duel", "skywars doubles": "sw_doubles", "sumo": "sumo_duel", "uhc doubles": "uhc_doubles", "bridge": "bridge_duel", "bridge 3v3v3v3": "bridge_3v3v3v3", "bridge doubles": "bridge_doubles", "bridge teams": "bridge_four", "bridge 2v2v2v2": "bridge_2v2v2v2"}
    ranks = ['godlike', 'grandmaster', 'legend', 'master', 'diamond', 'gold', 'iron', 'rookie']
    bridgeModes = ["bridge_3v3v3v3", "bridge_doubles", "bridge_four", "bridge_2v2v2v2"]


    @classmethod
    async def get_data(cls, ctx: commands.context, player_and_mode):
        player, mode, rawData = await cls.get_raw_data(ctx, player_and_mode)

        if not rawData.get('player') or not rawData['player'].get('stats') or not rawData['player']['stats'].get('Duels'):
            raise commands.BadArgument(f"{player} has not played Duels")
        data = rawData['player']['stats']['Duels']

        return cls(player=player, mode=mode, ctx=ctx, rawData=rawData, data=data)


    def overall_stats(self):
        rawData = self.rawData
        data = self.data

        embed = discord.Embed(title=f"{rawData['player']['displayname']}'s Hypixel Duels Profile", description=f"Duels stats for {rawData['player']['displayname']}", color=Color.red())
        for rank in self.ranks:
            prestigeNumber = data.get(f'all_modes_{rank}_title_prestige', None)
            if prestigeNumber:
                if rank == "rookie" and prestigeNumber == 1:
                    prestige = None
                    break
                prestige = f'{rank.capitalize()} {utils.write_roman(prestigeNumber)}'
                break
        else:
            prestige = None

        embed.add_field(name="Games Played:", value=data.get('wins', 0) + data.get('losses', 0), inline=True)
        embed.add_field(name="Winstreak:", value=data.get('current_winstreak', 0), inline=True)
        embed.add_field(name="Best Winstreak:", value=data.get('best_overall_winstreak', 0), inline=True)
        embed.add_field(name="Coins:", value=data.get('coins', 0), inline=True)
        embed.add_field(name="Prestige:", value=prestige, inline=True)
        embed.add_field(name="\u200b", value="\u200b")

        embed.add_field(name="Kills:", value=data.get('kills', 0), inline=True)
        embed.add_field(name="Deaths:", value=data.get('deaths', 0), inline=True)
        embed.add_field(name="K/D Rate:", value=utils.getRate(data.get('kills', 0), data.get('deaths', 0)), inline=True)
        ceilingRate, total, res = utils.getCeilingRate(data.get('kills', 0), data.get('deahts', 0))
        embed.add_field(name=f"Kills for {ceilingRate} K/DR", value=f"{utils.insert_commas(res)} ({utils.insert_commas(total)} total)", inline=False)

        embed.add_field(name="Wins:", value=data.get('wins', 0), inline=True)
        embed.add_field(name="Losses:", value=data.get('losses', 0), inline=True)
        embed.add_field(name="W/L Rate:", value=utils.getRate(data.get('wins', 0), data.get('losses', 0)), inline=True)
        ceilingRate, total, res = utils.getCeilingRate(data.get('wins', 0), data.get('losses', 0))
        embed.add_field(name=f"Wins for {ceilingRate} W/LR", value=f"{utils.insert_commas(res)} ({utils.insert_commas(total)} total)", inline=False)

        embed.add_field(name="Arrows Shot:", value=data.get('bow_shots', 0), inline=True)
        embed.add_field(name="Arrows Hit:", value=data.get('bow_hits', 0), inline=True)
        embed.add_field(name="Arrows Missed:", value=data.get('bow_shots', 0) - data.get('bow_hits', 0), inline=True)
        embed.add_field(name="Arrow H/S Rate:", value=utils.getRate(data.get('bow_hits', 0), data.get('bow_shots', 0)), inline=False)
        embed.add_field(name="Melee Swings:", value=data.get('melee_swings', 0), inline=True)
        embed.add_field(name="Melee Hits:", value=data.get('melee_hits', 0), inline=True)
        embed.add_field(name="Melee Missed:", value=data.get('melee_swings', 0) - data.get('melee_hits', 0), inline=True)
        embed.add_field(name="Melee H/S Rate:", value=utils.getRate(data.get('melee_hits', 0), data.get('melee_swings', 0)), inline=True)

        return embed


    def mode_stats(self, mode):
        rawData = self.rawData
        data = self.data
        display_mode = self.get_display_mode(mode)

        embed = discord.Embed(title=f"{rawData['player']['displayname']}'s Hypixel {display_mode} Duel Profile", description=f"{display_mode} duel stats for {rawData['player']['displayname']}", color=Color.red())
        for rank in self.ranks:
            prestigeNumber = data.get(f'{(display_mode).lower()}_{rank}_title_prestige')
            if prestigeNumber:
                if rank == "rookie" and prestigeNumber == 1:
                    prestige = None
                    break
                prestige = f'{rank.capitalize()} {utils.write_roman(prestigeNumber)}'
                break
        else:
            prestige = None

        embed.add_field(name="Prestige", value=prestige, inline=True)
        embed.add_field(name="Current Winstreak", value=data.get(f"current_winstreak_mode_{mode}", 0), inline=True)
        embed.add_field(name="Best Winstreak", value=data.get(f"best_winstreak_mode_{mode}", 0), inline=True)

        if mode == "bridge_duel":
            mode = "bridge"
        if mode in self.bridgeModes:
            mode += "_bridge"

        embed.add_field(name="Kills:", value=data.get(f'{mode}_kills', 0), inline=True)
        embed.add_field(name="Deaths:", value=data.get(f'{mode}_deaths', 0), inline=True)
        embed.add_field(name="K/D Rate:", value=utils.getRate(data.get(f'{mode}_kills', 0), data.get(f'{mode}_deaths', 0)), inline=True)
        ceilingRate, total, res = utils.getCeilingRate(data.get(f"{mode}_kills", 0), data.get(f"{mode}_deaths", 0))
        embed.add_field(name=f"Kills for {ceilingRate} K/DR", value=f"{utils.insert_commas(res)} ({utils.insert_commas(total)} total)", inline=False)

        if mode == "bridge":
            mode = "bridge_duel"
        if mode.endswith("_bridge"):
            mode = mode[:-7]

        embed.add_field(name="Wins:", value=data.get(f'{mode}_wins', 0), inline=True)
        embed.add_field(name="Losses:", value=data.get(f'{mode}_losses', 0), inline=True)
        embed.add_field(name="W/L Rate:", value=utils.getRate(data.get(f'{mode}_wins', 0), data.get(f'{mode}_losses', 0)), inline=True)
        ceilingRate, total, res = utils.getCeilingRate(data.get(f"{mode}_wins", 0), data.get(f"{mode}_losses", 0))
        embed.add_field(name=f"Wins for {ceilingRate} W/LR", value=f"{utils.insert_commas(res)} ({utils.insert_commas(total)} total)", inline=False)

        return embed


class HypixelOverallStatFetcher(HypixelStatFetcher):
    modes = {"None": "None"}

    @classmethod
    async def get_data(cls, ctx: commands.context, player_and_mode):
        player, mode, rawData = await cls.get_raw_data(ctx, player_and_mode)

        if not rawData.get('player') or not rawData['player'].get('stats') or not rawData['player']['stats'].get('Duels'):
            raise commands.BadArgument(f"{player} has not played Hypixel")

        return cls(player=player, mode=mode, ctx=ctx, rawData=rawData, data=rawData)


    async def send(self):
        data = self.rawData
        ctx = self.ctx

        embed = discord.Embed(title=f"{data['player']['displayname']}'s Hypixel Profile", description=f"Hypixel stats for {data['player']['displayname']}", color=Color.red())
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

        embed = self.finalize(embed)
        await ctx.reply(embed=embed)


class MinecraftStats(commands.Cog, name="MC Stats", description="Commands for Minecraft player statistics"):
    def __init__(self, bot):
        self.bot = bot
        print("Loaded", __name__)


    @commands.command(description="<player> can be a Minecraft player or left blank to get your own statistics", help="Gets statistics of a Minecraft player", aliases=['mc'])
    async def minecraft(self, ctx, *player):
        player, uuid, mode = await HypixelStatFetcher.has_link(ctx, player)
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
        player, uuid, mode = await HypixelStatFetcher.has_link(ctx, player)
        info = MojangAPI.get_profile(uuid)
        embed=discord.Embed(title=f"{info.name}'s Skin", description=f"Full render of {info.name}'s skin", color=Color.red())
        embed.set_footer(text="Stats provided using the Mojang API \nAvatars and skins from Crafatar")
        embed.set_image(url=MinecraftSkinFetcher.body(uuid))
        await ctx.reply(embed=embed)


    @commands.command(description="<player> can be a Minecraft player or left blank to get your own statistics", help="Gets the Hypixel statistics of a Minecraft player")
    async def hypixel(self, ctx, *player):
        StatFetcher = await HypixelOverallStatFetcher.get_data(ctx, player)
        await StatFetcher.send()


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


    @commands.command(description=f"<player> can be a Minecraft player or left blank to get your own Bedwars statistics \n Mode can be {BedwarsStatFetcher.getHypixelHelp()} or left blank for overall statistics", help="Gets the Bedwars statistics of a Minecraft player", aliases=['bw', 'bws'])
    async def bedwars(self, ctx, *player_and_mode):
        StatFetcher = await BedwarsStatFetcher.get_data(ctx, player_and_mode)
        await StatFetcher.send()


    @commands.command(description=f"<player> can be a Minecraft player or left blank to get your own Bedwars statistics \n Mode can be {SkyWarsStatFetcher.getHypixelHelp()} or left blank for overall statistics", help="Gets the SkyWars statistics of a Minecraft player", aliases=['sw', 'sws'])
    async def skywars(self, ctx, *player_and_mode):
        StatFetcher = await SkyWarsStatFetcher.get_data(ctx, player_and_mode)
        await StatFetcher.send()


    @commands.command(description=f"<player> can be a Minecraft player or left blank to get your own Duels statistics \n Mode can be {DuelsStatFetcher.getHypixelHelp()} or left blank to get overall statistics", help="Gets the Duels statistics of a Minecraft player")
    async def duels(self, ctx, *player_and_mode):
        StatFetcher = await DuelsStatFetcher.get_data(ctx, player_and_mode)
        await StatFetcher.send()




def setup(bot):
    bot.add_cog(MinecraftStats(bot))
