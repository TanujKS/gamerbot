from utils import utils, constants
from utils.constants import r, Converters, EnvVars, Color

import discord
from discord.ext import commands, tasks
from discord.utils import get

import asyncio


class Stats(commands.Cog, description="Commands for player statistics for all supported games"):
    def __init__(self, bot):
        self.bot = bot
        self.checkIfLive.start()
        print("Loaded", __name__)


    @tasks.loop(seconds=60)
    async def checkIfLive(self):
        trackingGuilds = utils.loadTrackingGuilds()

        for guild in trackingGuilds:
            for track in trackingGuilds[guild]:
                index = trackingGuilds[guild].index(track)
                data = await utils.getJSON(f'https://api.twitch.tv/helix/search/channels?query={trackingGuilds[guild][index]["streamer"]}/', headers={"client-id":EnvVars.TWITCH_CLIENT_ID, "Authorization": EnvVars.TWITCH_AUTH})
                returned = list(data['data'])
                for channel in returned:
                    if channel['id'] == str(trackingGuilds[guild][index]['id']):
                        x = channel
                        is_live = x['is_live']
                        if is_live:
                            if trackingGuilds[guild][index]['pinged'] == "False":
                                embed = discord.Embed(title=trackingGuilds[guild][index]['message'], description=f"https://twitch.tv/{trackingGuilds[guild][index]['streamer']}", color=Color.red())
                                embed.set_thumbnail(url=x['thumbnail_url'])
                                embed.add_field(name=x['title'], value="\u200b", inline=False)
                                guildSend = self.bot.get_guild(guild)
                                channel = guildSend.get_channel(trackingGuilds[guild][index]['channel-id'])
                                await channel.send(embed=embed)
                                trackingGuilds[guild][index]['pinged'] = "True"
                        else:
                            trackingGuilds[guild][index]['pinged'] = "False"
                        break
        utils.saveData("trackingGuilds", trackingGuilds)


    @checkIfLive.before_loop
    async def before_checkIfLive(self):
        await self.bot.wait_until_ready()


    @commands.command(help="Gets the statistics of a Fortnite player")
    async def fortnite(self, ctx, player):
        player = player.replace(" ", "%20")
        data = await utils.getJSON(f"https://fortnite-api.com/v1/stats/br/v2?name={player}")
        if data['status'] != 200:
            raise commands.BadArgument(f'Player "{player}" not found.')
        else:
            embed = discord.Embed(title=f"Fortnite stats for {data['data']['account']['name']}", color=Color.red())
            embed.add_field(name="Username:", value=data['data']['account']['name'], inline=False)
            embed.add_field(name="ID:", value=data['data']['account']['id'], inline=False)
            embed.add_field(name="BattlePass Level:", value=data['data']['battlePass']['level'])
            embed.add_field(name="BattlePass Progress:", value=data['data']['battlePass']['progress'])
            embed.add_field(name="Score", value=data['data']['stats']['all']['overall']['score'])
            embed.add_field(name="Overall Kills:", value=data['data']['stats']['all']['overall']['kills'])
            embed.add_field(name="Overall Deaths", value=data['data']['stats']['all']['overall']['deaths'])
            embed.add_field(name="Overall K/D Rate", value=data['data']['stats']['all']['overall']['kd'])
            embed.add_field(name="Overall Games Played", value=data['data']['stats']['all']['overall']['matches'])
            embed.add_field(name="Overall Wins", value=data['data']['stats']['all']['overall']['wins'])
            embed.add_field(name="Overall Losses", value=data['data']['stats']['all']['overall']['deaths'])
            embed.add_field(name="Overall W/L Rate", value=round(data['data']['stats']['all']['overall']['wins']/data['data']['stats']['all']['overall']['deaths'], 2))
            embed.set_footer(text="Stats provided using the unofficial Fortnite-API")
            embed.set_thumbnail(url="https://logodix.com/logo/45400.jpg")
            await ctx.reply(embed=embed)


    @staticmethod
    async def twitchProfile(channel, data):
        embed = discord.Embed(title=f"{data['display_name']}'s' Twitch Stats", description=f"https://twitch.tv/{channel}", color=Color.red())
        embed.set_thumbnail(url=data['profile_image_url'])
        embed.add_field(name="Username:", value=data['display_name'], inline=True)
        embed.add_field(name="Login Name:", value=data['login'], inline=True)
        embed.add_field(name="ID", value=data['id'], inline=True)
        channelType = data['broadcaster_type'].capitalize()
        if not channelType:
            channelType = "None"
        embed.add_field(name="Channel Type", value=channelType, inline=False)
        description = data['description']
        if not description:
            description = "None"
        embed.add_field(name="Channel Description", value=description, inline=False)
        embed.add_field(name="Views", value=data['view_count'], inline=True)
        followers = await utils.getJSON(f"https://api.twitch.tv/helix/users/follows?to_id={data['id']}", headers={"client-id":f"{EnvVars.TWITCH_CLIENT_ID}", "Authorization":f"{EnvVars.TWITCH_AUTH}"})
        embed.add_field(name="Followers", value=followers['total'], inline=True)
        embed.set_footer(text=f"Stats provided by the Twitch API \nNot the streamer your looking for? Type 'see more' to see more {channel}s and then run '?twitchbyid (id_of_the_channel_you_want)'")
        return embed


    @commands.command(help="Gets the statistics of a Twitch streamer by their Channel ID")
    async def twitchbyid(self, ctx, id):
        rawData = await utils.getJSON(f"https://api.twitch.tv/helix/users?id={id}", headers={"client-id":f"{EnvVars.TWITCH_CLIENT_ID}", "Authorization":f"{EnvVars.TWITCH_AUTH}"})
        if not rawData.get('data'):
            raise commands.ChannelNotFound(channel)
        await self.twitch(ctx, rawData['data'][0]['login'])


    @commands.command(help="Gets the statistics of a Twitch streamer by their channel name")
    async def twitch(self, ctx, channel):
        user = await utils.getJSON(f"https://api.twitch.tv/helix/users?login={channel}", headers={"client-id":f"{EnvVars.TWITCH_CLIENT_ID}", "Authorization":f"{EnvVars.TWITCH_AUTH}"})

        if not user.get('data'):
            raise commands.ChannelNotFound(channel)

        data = (user['data'])[0]
        await ctx.reply(embed=await self.twitchProfile(channel, data))

        def ytCheck(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content == "see more"
        try:
            seemore = await self.bot.wait_for('message', timeout=30, check=ytCheck)
        except asyncio.TimeoutError:
            return

        for x in user['data']:
            if x != user['data'][0]:
                await ctx.reply(embed=await self.twitchProfile(channel, x))


    @commands.command(help="Notifies the current channel whenever a streamer goes live")
    async def twitchtrack(self, ctx, channel, message=None):
        trackingGuilds = utils.loadTrackingGuilds()

        if not message:
            message = f"{channel} is live"

        user = await utils.getJSON(f"https://api.twitch.tv/helix/users?login={channel}", headers={"client-id":f"{EnvVars.TWITCH_CLIENT_ID}", "Authorization":f"{EnvVars.TWITCH_AUTH}"})
        if not user:
            raise commands.ChannelNotFound(channel)

        x = (user['data'])[0]
        trackingGuilds[ctx.guild.id].append({})
        trackingGuilds[ctx.guild.id][-1]['channel-id'] = ctx.channel.id
        trackingGuilds[ctx.guild.id][-1]['streamer'] = channel
        trackingGuilds[ctx.guild.id][-1]['pinged'] = "False"
        trackingGuilds[ctx.guild.id][-1]['message'] = message
        trackingGuilds[ctx.guild.id][-1]['id'] = x['id']
        embed = discord.Embed(title=f"THIS IS AN EXAMPLE STREAM: {trackingGuilds[ctx.guild.id][-1]['message']}", description=f"https://twitch.tv/{trackingGuilds[ctx.guild.id][-1]['streamer']}", color=Color.red())
        embed.set_thumbnail(url=x['profile_image_url'])
        embed.add_field(name="This is an example stream", value="\u200b", inline=False)
        channelSend = ctx.guild.get_channel(trackingGuilds[ctx.guild.id][-1]["channel-id"])
        await channelSend.send(embed=embed)
        utils.saveData("trackingGuilds", trackingGuilds)


    @commands.command(help="Stops notifying the current channel whenever a streamer goes live")
    async def deltrack(self, ctx, *, streamer):
        trackingGuilds = utils.loadTrackingGuilds()

        def findTwitchTrack(ctx, streamer):
            for track in trackingGuilds[ctx.guild.id]:
                if trackingGuilds[ctx.guild.id][trackingGuilds[ctx.guild.id].index(track)]['streamer'] == streamer:
                    return trackingGuilds[ctx.guild.id].index(track)
            return None

        track = findTwitchTrack(ctx, streamer)
        if track == None:
            raise commands.ChannelNotFound(streamer)
        trackingGuilds[ctx.guild.id].pop(track)

        await ctx.reply(f"No longer tracking {streamer}")
        utils.saveData("trackingGuilds", trackingGuilds)


    @commands.command(help="Gets a list of all tracked Twitch streamers")
    async def twitchtracklist(self, ctx):
        trackingGuilds = utils.loadTrackingGuilds()
        embed = discord.Embed(title=f"All Twitch Tracks in {ctx.guild.name}", color=Color.red())
        for track in trackingGuilds[ctx.guild.id]:
            index = trackingGuilds[ctx.guild.id].index(track)
            embed.add_field(name=trackingGuilds[ctx.guild.id][index]['streamer'], value=f"Tracking to channel: {ctx.guild.get_channel(trackingGuilds[ctx.guild.id][index]['channel-id'])}")
        await ctx.reply(embed=embed)


    @commands.command(help="Gets the statistics of a YouTuber", aliases=["yt"])
    async def youtube(self, ctx, *, channel):
        channel = channel.replace(" ", "%20")
        data = await utils.getJSON(f"https://youtube.googleapis.com/youtube/v3/search?part=snippet&q={channel}&type=channel&key={EnvVars.YT_KEY}")
        errors = data.get('error')
        if errors:
            raise commands.BadArgument("YouTube returned an error!")
        if not data.get('items'):
            raise commands.ChannelNotFound(channel)
        Paginator = utils.Paginator(self.bot)
        for channel in data['items']:
            rawData = await utils.getJSON(f"https://www.googleapis.com/youtube/v3/channels?part=statistics&id={channel['snippet']['channelId']}&key={EnvVars.YT_KEY}")
            stats = rawData['items'][0]['statistics']
            embed = discord.Embed(title=f"YouTube statistics for {channel['snippet']['title']}", description=f"https://www.youtube.com/channel/{rawData['items'][0]['id']}", color=Color.red())
            embed.add_field(name="Channel Name:", value=channel['snippet']['title'], inline=True)
            embed.add_field(name="Channel ID:", value=rawData['items'][0]['id'], inline=True)
            embed.add_field(name="Channel Description:", value=channel['snippet']['description'] if channel['snippet']['description'] else "None", inline=False)
            embed.add_field(name="Views:", value=stats.get('viewCount', 0), inline=True)
            embed.add_field(name="Subscribers:", value=stats.get('subscriberCount', 0), inline=True)
            embed.add_field(name="Videos:", value=stats.get('videoCount'), inline=True)
            embed.set_thumbnail(url=channel['snippet']['thumbnails']['default']['url'])
            embed.set_footer(text=f"Stats provided by the YouTube API")
            Paginator.add_page(embed)
        await Paginator.send_page(ctx=ctx)


    @commands.command(description="<id> must be the Steam ID of a CS:GO player \n Player must have their Steam profile set to public", help="Links your Discord to a CS:GO account", aliases=['csgolink'])
    async def csgoverify(self, ctx, id):
        csgoLinks = utils.loadCSGOLinks()
        rawData = await utils.getJSON(f"https://public-api.tracker.gg/v2/csgo/standard/profile/steam/{id}", headers={"TRN-Api-Key": EnvVars.TRN_API_KEY})
        data = rawData.get('data')
        if not data:
            raise commands.BadArgument(rawData['errors'][0]['message'])
        await ctx.reply(f"{str(ctx.author)} is now linked to {data['platformInfo']['platformUserHandle']} \n**NOTE: There is no way to verify you are actually {data['platformInfo']['platformUserHandle']}, this is purely for convenience so you do not have to memorize your ID**")
        csgoLinks[ctx.author.id] = data['platformInfo']['platformUserId']
        utils.saveData("csgoLinks", csgoLinks)


    @commands.command(description="<player> must be the Steam ID of a CS:GO player \n Player must have their Steam profile set to public", help="Gets the statistics of a CS:GO player")
    async def csgo(self, ctx, *player):
        csgoLinks = utils.loadCSGOLinks()
        if len(player) == 0:
            member = ctx.author.id
        elif ctx.message.mentions:
            member = await Converters.MemberConverter.convert(ctx, player[0])
            member = member.id
        else:
            member = None
            player = player[0]
        if member:
            player = csgoLinks.get(member)
            if not player:
                raise commands.BadArgument(f"There is no CS:GO ID linked to {str(ctx.guild.get_member(member))}. Run {utils.determine_prefix(ctx.bot, ctx, clean=True)}csgolink")
        rawData = await utils.getJSON(f"https://public-api.tracker.gg/v2/csgo/standard/profile/steam/{player}", headers={"TRN-Api-Key": EnvVars.TRN_API_KEY})
        data = rawData.get('data')
        if not data:
            raise commands.BadArgument(rawData['errors'][0]['message'])
        embed = discord.Embed(title=f"{data['platformInfo']['platformUserHandle']}'s CS:GO Profile", description=f"Stats for {data['platformInfo']['platformUserHandle']}", color=Color.red())
        embed.set_thumbnail(url=data['platformInfo']['avatarUrl'])
        embed.add_field(name="Username:", value=data['platformInfo']['platformUserHandle'], inline=True)
        embed.add_field(name="ID:", value=data['platformInfo']['platformUserId'], inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="Kills:", value=data['segments'][0]['stats']['kills']['value'], inline=True)
        embed.add_field(name="Deaths:", value=data['segments'][0]['stats']['deaths']['value'], inline=True)
        embed.add_field(name="K/D Rate:", value=round(data['segments'][0]['stats']['kd']['value'], 2), inline=True)
        embed.add_field(name="Damage:", value=data['segments'][0]['stats']['damage']['value'], inline=True)
        embed.add_field(name="Headshots:", value=data['segments'][0]['stats']['headshots']['value'], inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="Shots Fired:", value=data['segments'][0]['stats']['shotsFired']['value'], inline=True)
        embed.add_field(name="Shots Hit:", value=data['segments'][0]['stats']['shotsHit']['value'], inline=True)
        embed.add_field(name="Shot Accuracy:", value=f"{round(data['segments'][0]['stats']['shotsAccuracy']['value'], 2)}%", inline=True)
        embed.add_field(name="Bombs Planted:", value=data['segments'][0]['stats']['bombsPlanted']['value'], inline=True)
        embed.add_field(name="Bombs Defused:", value=data['segments'][0]['stats']['bombsDefused']['value'], inline=True)
        embed.add_field(name="Hostages Rescued:", value=data['segments'][0]['stats']['hostagesRescued']['value'], inline=True)
        embed.add_field(name="Wins:", value=data['segments'][0]['stats']['wins']['value'], inline=True)
        embed.add_field(name="Losses:", value=data['segments'][0]['stats']['losses']['value'], inline=True)
        embed.add_field(name="Ties:", value=data['segments'][0]['stats']['ties']['value'], inline=True)
        embed.add_field(name="W/L Rate:", value=round(data['segments'][0]['stats']['wins']['value']/data['segments'][0]['stats']['losses']['value'], 2), inline=True)
        embed.add_field(name="W/L Percentage:", value=f"{round(data['segments'][0]['stats']['wlPercentage']['value'], 2)}", inline=True)
        await ctx.reply(embed=embed)


    @commands.command(aliases=["clash"])
    async def clashroyale(self, ctx, id):
        data = await utils.getJSON(f"https://api.clashroyale.com/v1/players/{id.replace('#', '%23')}/", headers={"Accept":"application/json", "authorization":EnvVars.CLASH_KEY}, proxies=EnvVars.proxies)
        print(data)

        if data.get('reason'):
            raise commands.BadArgument(f"Something went wrong! \nError: {data.get('reason')}")

        embed = discord.Embed(title=f"{data['name']}'s Clash Royale Profile", color=Color.red())
        embed.set_thumbnail(url=data['currentFavouriteCard']['iconUrls']['medium'])
        embed.add_field(name="Name:", value=data['name'])
        embed.add_field(name="Tag:", value=data['tag'])
        embed.add_field(name="\u200b", value="\u200b")
        embed.add_field(name="Trophies:", value=data['trophies'])
        embed.add_field(name="Best Trophies:", value=data['bestTrophies'])
        embed.add_field(name="\u200b", value="\u200b")
        embed.add_field(name="Wins:", value=data['wins'])
        embed.add_field(name="Losses:", value=data['losses'])
        embed.add_field(name="W/L Rate:", value=utils.getRate(data['wins'], data['losses']))
        embed.add_field(name="Draws:", value=data['battleCount']-(data['wins'] + data['losses']))
        embed.add_field(name="Games Played:", value=data['battleCount'])
        embed.add_field(name="Three Crown Wins:", value=data['threeCrownWins'])
        embed.add_field(name="Clan:", value=data['clan']['name'] if data.get('clan') else "None")
        await ctx.reply(embed=embed)




def setup(bot):
    bot.add_cog(Stats(bot))
