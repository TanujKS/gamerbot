from utils import utils
from utils.constants import r, teams, emojis

import discord
from discord.ext import commands
from discord.utils import get

import asyncio


class Teams(commands.Cog, description="Commands for team and event management"):
    def __init__(self, bot):
        self.bot = bot
        self.nonSetupCommands = ["setup", "wipe"]
        for command in self.get_commands():
            if command.name not in self.nonSetupCommands:
                command.description += "\nServer must be setup with the setup command"

        print("Loaded", __name__)


    async def cog_check(self, ctx):
        if ctx.command.name in self.nonSetupCommands:
            return True
        else:
            return utils.checkIfSetup(ctx)


    @commands.command(help="Locks all team voice channels")
    @commands.bot_has_guild_permissions(manage_channels=True)
    @commands.has_permissions(manage_channels=True)
    async def lockevents(self, ctx):
        guildInfo = utils.loadGuildInfo(r)
        for team in teams:
            channel = get(ctx.guild.voice_channels, name=team)
            perms = channel.overwrites_for(ctx.guild.default_role)
            perms.connect = False
            await channel.set_permissions(ctx.guild.default_role, overwrite=perms)
            await channel.edit(user_limit=guildInfo[ctx.guild.id]['teamLimit'])
        await ctx.reply("Locked all team voice channels")


    @commands.command(help="Unlocks all team voice channels")
    @commands.bot_has_guild_permissions(manage_channels=True)
    @commands.has_guild_permissions(manage_channels=True)
    async def unlockevents(self, ctx):
        for team in teams:
            voicechannel = get(ctx.guild.voice_channels, name=team)
            await voicechannel.set_permissions(ctx.guild.default_role, connect=True)
            await voicechannel.edit(user_limit=None)
        await ctx.reply("Unlocked all voice channels")


    @commands.command(description="<member> can be the name, id, or mention of a member", help="Bans a member from particpating in events")
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.has_guild_permissions(manage_roles=True)
    async def eventban(self, ctx, member : discord.Member):
        role = get(ctx.guild.roles, name="Banned from event")

        if role in member.roles:
            await ctx.reply(f"{member.mention} is already banned")

        else:
            await member.add_roles(role)
            await ctx.reply(f"Banned {member.mention} from events")


    @commands.command(description="<member> can be the name, id, or mention of a member", help="Bans a member from particpating in events")
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.has_guild_permissions(manage_roles=True)
    async def eventunban(self, ctx, member):
        role = get(ctx.guild.roles, name="Banned from event")
        if not role:
            raise commands.BadArgument("Could not find role, your server may not be setup for Game Events yet. Run ?setup")

        if member == "all":
            for member in role.members:
                await member.remove_roles(role)
                await ctx.reply(f"Unbanned {member.mention} from events")

        else:
            member = MemberConverter.convert(ctx, member)

            if role in member.roles:
                await member.remove_roles(role)
                await ctx.reply(f"Unbanned {member.mention} from events")
            else:
                raise commands.BadArgument(f"{member.mention} is not banned")


    @commands.command(help="Creates an interactive menu where members can select a team")
    @commands.bot_has_guild_permissions(manage_roles=True, manage_messages=True)
    @commands.has_guild_permissions(manage_roles=True, manage_messages=True)
    async def createteams(self, ctx):
        await ctx.message.delete()
        msg = await ctx.send("React to get into your teams")

        for emoji in emojis:
            await msg.add_reaction(emoji)


    @commands.command(help="Closes a team menu")
    @commands.bot_has_guild_permissions(manage_messages=True)
    @commands.has_guild_permissions(manage_messages=True)
    async def closeteams(self, ctx):
        def closeTeamsCheck(reaction, user):
            return user == ctx.author and reaction.message.content == "React to get into your teams" and reaction.message.author == self.bot.user

        close = await ctx.reply("React to the message I must close")
        reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=closeTeamsCheck)

        await close.delete()
        await ctx.message.delete()

        await reaction.message.edit(content="Teams are now closed.")


    @commands.command(description="Team can be a name, id, or mention of a role called Team 1, Team 2, ... Team 8", help="Removes all members from a team")
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.has_guild_permissions(manage_roles=True)
    async def clearteam(self, ctx, team : discord.Role):
        if not team.name in teams:
            raise commands.BadArgument(f'Team "{team}" not found.')

        role = get(ctx.guild.roles, name=team)

        for member in role.members:
            await member.remove_roles(role)
            await ctx.reply(f"Cleared {str(role)}")


    @commands.command(help=f"Same as clearteam but clears all teams")
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.has_guild_permissions(manage_roles=True)
    async def clearteams(ctx):
        for team in teams:
            role = get(ctx.guild.roles, name=team)

            for member in role.members:
                await member.remove_roles(role)

            await ctx.reply("Cleared all teams")


    @commands.command(description="", help="Creates the roles and channels for GamerBot to manage gaming events")
    @commands.bot_has_guild_permissions(manage_channels=True, manage_roles=True)
    @commands.has_guild_permissions(manage_channels=True, manage_roles=True)
    @commands.cooldown(1, 120, commands.BucketType.guild)
    async def setup(self, ctx):
        def check(m):
            return m.channel == ctx.channel and m.author == ctx.author
        await ctx.reply("Alright lets get started setting up your server! What game are you going to be playing on your server? (Or type `cancel`)")

        msg = await self.bot.wait_for('message', check=check)
        if msg.content == "cancel":
            raise commands.BadArgument("Cancelled")

        #loading = get(self.bot.get_guild(816778178907209738).emojis, name="loading")
        #embed = discord.Embed(title=f"Setting up your server for {msg.content} Events", description="This make take a while...")
        #embed.add_field(name="Important Channels", value="\u200b")
        #embed.add_field(name=loading, value="\u200b")
        #embed.add_field(name="\u200b", value="\u200b")
        #embed.add_field(name="Test", value="\u200b")
        #embed.add_field(name=loading, value="\u200b")
        #await ctx.reply(embed=embed)
        async with ctx.channel.typing():
            category = await ctx.guild.create_category(msg.content + " Events")
            announcement = await ctx.guild.create_text_channel(f"{msg.content}-announcement", overwrites=None, category=category)
            await asyncio.sleep(5)

            rules = await ctx.guild.create_text_channel(f"{msg.content}-rules", overwrites=None, category=category)
            await asyncio.sleep(5)

            logs = await ctx.guild.create_text_channel(f"{msg.content}-event-logs", overwrites=None, category=category)
            await asyncio.sleep(5)

            await announcement.set_permissions(ctx.guild.default_role, send_messages=False)
            await rules.set_permissions(ctx.guild.default_role, send_messages=False)
            await logs.set_permissions(ctx.guild.default_role, send_messages=False)

            lounge = await ctx.guild.create_text_channel(f"{msg.content}-lounge", overwrites=None, category=category)
            await asyncio.sleep(5)

            banned = await ctx.guild.create_role(name="Banned from event")
            await asyncio.sleep(5)

            perms = lounge.overwrites_for(banned)
            perms.send_messages = False
            await lounge.set_permissions(banned, overwrite=perms)

            channel1 = await ctx.guild.create_voice_channel(f"{msg.content} Events", overwrites=None, category=category)
            await asyncio.sleep(5)

            perms = channel1.overwrites_for(banned)
            perms.connect = False
            await channel1.set_permissions(banned, overwrite=perms)

            perms1 = channel1.overwrites_for(ctx.guild.default_role)
            perms1.connect = True
            await channel1.set_permissions(ctx.guild.default_role, overwrite=perms1)

            for team in teams:
                role = await ctx.guild.create_role(name=team)
                channel = await ctx.guild.create_voice_channel(team, overwrites=None, category=category, user_limit=2)

                perms = channel.overwrites_for(role)
                perms.connect = True
                await channel.set_permissions(role, overwrite=perms)

                perms = channel.overwrites_for(ctx.guild.default_role)
                perms.connect = False
                await channel.set_permissions(ctx.guild.default_role, overwrite=perms)

                await asyncio.sleep(5)

        await ctx.reply(f"Your server is setup! \n**DO NOT change the name of the voicechannels or the roles that {self.bot.user.name} has created as it may mess up certain commands**")


    @commands.command(description="", help="Deletes the roles and channels for GamerBot to manage gaming events", checks=None)
    @commands.bot_has_guild_permissions(manage_channels=True, manage_roles=True)
    @commands.has_guild_permissions(manage_channels=True, manage_roles=True)
    async def wipe(self, ctx):
        def wipeCheck(m):
            responses = ["y", "n"]
            return m.channel == ctx.channel and m.author == ctx.author and m.content in responses

        await ctx.reply("Are you sure you want to wipe the server of all event channels? This will delete ALL channels and ALL roles I have created (`y`/`n`)")
        response = await self.bot.wait_for('message', timeout=60.0, check=wipeCheck)

        if response.content == "y":
            for category in ctx.guild.categories:
                if "Events" in category.name:
                    for channel in category.channels:
                        await channel.delete()
                    await category.delete()

            for team in teams:
                role = get(ctx.guild.roles, name=team)
                if role:
                    await role.delete()

            role = get(ctx.guild.roles, name="Banned from event")
            if role:
                await role.delete()

            await ctx.reply("Wiped all event channels and roles")

        if response.content == "n":
            await ctx.reply("Cancelled the wipe")


    @commands.command(description="<team> can be a name, id, or mention of a role called Team 1, Team 2, ... Team 8", help="Removes all members from a team")
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.has_guild_permissions(manage_roles=True)
    async def setteam(self, ctx, team : discord.Role):
        if not team.name in teams:
            raise commands.BadArgument(f'Team "{team}" not found.')

        for member in ctx.message.mentions:
            for team in teams:
                role = get(member.roles, name=team)
                if role:
                    await member.remove_roles(role)
            await member.add_roles(team)
            await ctx.reply(f"Added {member.mention} to {str(team)}")


    @commands.command(help="Moves all members in the main event voice channel to their team voice channels")
    @commands.bot_has_guild_permissions(move_members=True)
    @commands.has_guild_permissions(move_members=True)
    async def moveteams(self, ctx):
        for voicechannel in ctx.guild.voice_channels:
            if "Events" in voicechannel.name:
                for member in voicechannel.members:
                    for team in teams:
                        if get(member.roles, name=team):
                            voicechannel = get(ctx.guild.voice_channels, name=team)
                            await member.edit(voice_channel=voicechannel)
                await ctx.reply(f"Moved all members to their team voice channels")

                break


    @commands.command(help="Moves all members in their team voice channels to the main event voice channel")
    @commands.bot_has_guild_permissions(move_members=True)
    @commands.has_guild_permissions(move_members=True)
    async def moveevents(self, ctx):
        for vc in ctx.guild.voice_channels:
            if "Events" in vc.name:
                events = vc
                break

        for team in teams:
            voicechannel = get(ctx.guild.voice_channels, name=team)
            for member in voicechannel.members:
                await member.edit(voice_channel=events)

        await ctx.reply(f"Moved all members to {events.name}")





def setup(bot):
    bot.add_cog(Teams(bot))
