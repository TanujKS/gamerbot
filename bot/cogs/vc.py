from utils import utils
from utils.constants import r, Converters

import os

import discord
from discord.ext import commands
from discord.utils import get

from discord import FFmpegPCMAudio
from discord import opus
import gtts
import ffmpeg


class VC(commands.Cog, description="Commands for managing member in voice channels"):
    def __init__(self, bot):
        self.bot = bot
        print("Loaded", __name__)


    @staticmethod
    async def editMemberVoice(ctx, member, action):
        members = []

        if member == "channel-all":
            if not ctx.author.voice.channel:
                raise commands.BadArgument("You are not in a voice channel")

            members = ctx.author.voice.channel.members

            await ctx.reply(f"{action} all members in {ctx.author.voice.channel.mention}")

        elif member == "all":
            for voicechannel in ctx.guild.voice_channels:
                for member in voicechannel.members:
                    members.append(member)

            await ctx.reply(f"{action} all members in {ctx.guild.name}")

        else:
            member = await Converters.MemberConverter.convert(ctx, member)
            if not member.voice:
                raise commands.BadArgument(f"{member.mention} is not in a voice channel")

            members.append(member)

            await ctx.reply(f"{action} {member.mention}")

        return members


    @commands.command(description="<member> can be the name, id, or mention of a member, 'channel-all', or 'all' \n 'voicechannel' can be a voice channel or 'me'", help="Moves a member to a voice channel. \n 'channel-all' moves all people in the channel you are currently in while 'all' moves everyone in a voice channel in the server.")
    @commands.bot_has_guild_permissions(move_members=True)
    @commands.has_guild_permissions(move_members=True)
    async def move(self, ctx, member, *, voicechannel):
        if voicechannel == "me":
            if not ctx.author.voice:
                raise commands.BadArgument("You are not in a voice channel")
            voicechannel = ctx.author.voice.channel
        else:
            voicechannel = await Converters.VoiceChannelConverter.convert(ctx, voicechannel)

        for member in await self.editMemberVoice(ctx, member, "Moving"):
            await member.edit(voice_channel=voicechannel)


    @commands.command(description="<member> can be the name, id, or mention of a member, 'channel-all', or 'all'", help="Server mutes a member. \n'channel-all' mutes all people in the channel you are currently in while 'all' mutes everyone in a voice channel in the server.")
    @commands.bot_has_guild_permissions(mute_members=True)
    @commands.has_guild_permissions(mute_members=True)
    async def mute(self, ctx, member):
        for member in await self.editMemberVoice(ctx, member, "Muting"):
            await member.edit(mute=True)


    @commands.command(description="<member> can be the name, id, or mention of a member, 'channel-all', or 'all'", help="Server deafens a member. \n'channel-all' deafens all people in the channel you are currently in while 'all' deafens everyone in a voice channel in the server.")
    @commands.bot_has_guild_permissions(deafen_members=True)
    @commands.has_guild_permissions(deafen_members=True)
    async def deafen(self, ctx, member):
        for member in await self.editMemberVoice(ctx, member, "Deafening"):
            await member.edit(deafen=True)


    @commands.command(description="<member> can be the name, id, or mention of a member, 'channel-all', or 'all'", help="Server unmutes a member. \n'channel-all' unmutes all people in the channel you are currently in while 'all' unmutes everyone in a voice channel in the server.")
    @commands.bot_has_guild_permissions(mute_members=True)
    @commands.has_guild_permissions(mute_members=True)
    async def unmute(self, ctx, member):
        for member in await self.editMemberVoice(ctx, member, "Unmuting"):
            await member.edit(mute=False)


    @commands.command(description="<member> can be the name, id, or mention of a member, 'channel-all', or 'all'", help="Server undeafens a member. \n'channel-all' undeafens all people in the channel you are currently in while 'all' undeafens everyone in a voice channel in the server.")
    @commands.bot_has_guild_permissions(deafen_members=True)
    @commands.has_guild_permissions(deafen_members=True)
    async def undeafen(self, ctx, member):
        for member in await self.editMemberVoice(ctx, member, "Undeafening"):
            await member.edit(deafen=False)


    @commands.command(description="<member> can be the name, id, or mention of a member, 'channel-all', or 'all'", help="Disconnects a member. \n'channel-all' disconnects all people in the channel you are currently in while 'all' disconnects everyone in a voice channel in the server.")
    @commands.bot_has_guild_permissions(move_members=True)
    @commands.has_guild_permissions(move_members=True)
    async def dc(self, ctx, member):
        for member in await self.editMemberVoice(ctx, member, "Disconnecting"):
            await member.edit(voice_channel=None)


    @commands.command(help="Joins the voice channel you are currently in")
    @commands.has_guild_permissions(use_voice_activation=True, connect=True, speak=True)
    @commands.bot_has_guild_permissions(use_voice_activation=True, connect=True, speak=True)
    async def join(self, ctx):
        if ctx.author.voice:
            if not ctx.guild.voice_client:
                await ctx.author.voice.channel.connect()
                await ctx.guild.change_voice_state(channel=ctx.author.voice.channel, self_deaf=True)
            elif ctx.author.voice.channel != ctx.guild.me.voice.channel:
                if len(ctx.guild.me.voice.channel.members) == 1:
                    await ctx.guild.change_voice_state(channel=ctx.author.voice.channel, self_deaf=True)
                else:
                    raise commands.BadArgument("Already in a voice channel")
        else:
            raise commands.BadArgument("You are not in a voice channel.")
        return ctx.guild.voice_client


    @commands.command(help="Leaves the voice channel GamerBot is in")
    @commands.guild_only()
    async def leave(self, ctx):
        if ctx.guild.voice_client:
            await ctx.guild.voice_client.disconnect()


    def deafen_check():
        async def predicate(ctx):
            if ctx.author.voice:
                if not ctx.author.voice.self_deaf and not ctx.author.voice.deaf:
                    return True
                else:
                    raise commands.BadArgument("You cannot use this command while deafened")
            else:
                return True
        return commands.check(predicate)


    def ttvc_check():
        def predicate(ctx):
            guildInfo = utils.loadGuildInfo()

            if get(ctx.author.roles, name=guildInfo[ctx.guild.id]['TTVCrole']):
                return True
            else:
                raise commands.BadArgument(f"You are missing role {guildInfo[ctx.guild.id]['TTVCrole']} to use Text to Voice Channel")
        return commands.check(predicate)


    @commands.command(description="Requires TTVC role which can be set with ?settings", help="Uses Text to Speech to talk in a voice channel")
    @commands.has_guild_permissions(speak=True)
    @commands.bot_has_guild_permissions(speak=True)
    @deafen_check()
    @ttvc_check()
    async def speak(self, ctx, *, message):
        vc = await self.join(ctx)

        fullmessage = f"{ctx.author.name} says {message}"

        path = f"bot/TTVC/{ctx.message.id}.mp3"
        tts = gtts.gTTS(fullmessage, lang="en")
        tts.save(path)

        while vc.is_playing():
            pass

        vc.play(discord.FFmpegPCMAudio(path), after=lambda e: os.remove(path))




def setup(bot):
    bot.add_cog(VC(bot))
