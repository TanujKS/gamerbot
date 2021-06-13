import discord
from discord.ext import commands

import redis

import os
from dotenv import load_dotenv
load_dotenv()


class EnvVars:
    ALT_TOKEN = os.getenv("ALT_TOKEN")
    HYPIXEL_KEY = os.getenv("HYPIXEL_KEY")
    REDIS_URL = os.getenv("REDIS_URL")
    REPORTS = os.getenv("REPORTS")
    TOKEN = os.getenv("TOKEN")
    TRN_API_KEY = os.getenv("TRN_API_KEY")
    TWITCH_AUTH = os.getenv("TWITCH_AUTH")
    TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
    YT_KEY = os.getenv("YT_KEY")
    CLASH_KEY = os.getenv("CLASH_KEY")
    proxies = {
    "http": os.getenv('QUOTAGUARDSTATIC_URL'),
    "https": os.getenv('QUOTAGUARDSTATIC_URL')
    }


class Converters:
    MemberConverter = commands.MemberConverter()
    VoiceChannelConverter = commands.VoiceChannelConverter()
    RoleConverter = commands.RoleConverter()
    GuildConverter = commands.GuildConverter()
    

class Regions:
    amsterdam = "Europe/Amsterdam"
    brazil = "America/Sao_Paulo"
    dubai = "Asia/Dubai"
    eu_central = "Europe/Paris"
    eu_west = "Europe/Lisbon"
    europe = "Europe/Paris"
    frankfurt = "Europe/Berlin"
    hongkong = "Asia/Hong_Kong"
    india = "Asia/Kolkata"
    japan = "Asia/Tokyo"
    london = "Europe/London"
    russia = "Europe/Moscow"
    southafrica = "Africa/Johannesburg"
    south_korea = "Asia/Seoul"
    sydney = "Australia/Sydney"
    us_central = "America/Chicago"
    us_east = "America/New_York"
    us_south = "America/Chicago"
    us_west = "America/Los_Angeles"
    vip_amsterdam = "Europe/Amsterdam"
    vip_us_east = "America/New_York"
    vip_us_west = "America/Los_Angeles"


class Color(discord.Color):
    @classmethod
    def red(cls):
        return cls(0xff0000)


command_prefix = "?"

r = redis.from_url(EnvVars.REDIS_URL)

emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣"]

teams = ["Team 1", "Team 2", "Team 3", "Team 4", "Team 5", "Team 6", "Team 7", "Team 8"]

ezmessages = [
    "Wait... This isn't what I typed!",
    "Anyone else really like Rick Astley?",
    "Hey helper, how play game?",
    "Sometimes I sing soppy, love songs in the car.",
    "I like long walks on the beach and playing Hypixel",
    "Please go easy on me, this is my first game!",
    "You're a great person! Do you want to play some Hypixel games with me?",
    "In my free time I like to watch cat videos on Youtube",
    "When I saw the witch with the potion, I knew there was trouble brewing.",
    "If the Minecraft world is infinite, how is the sun spinning around it?",
    "Hello everyone! I am an innocent player who loves everything Hypixel.",
    "Plz give me doggo memes!",
    "I heard you like Minecraft, so I built a computer in Minecraft in your Minecraft so you can Minecraft while you Minecraft",
    "Why can't the Ender Dragon read a book? Because he always starts at the End.",
    "Maybe we can have a rematch?",
    "I sometimes try to say bad things then this happens :(",
    "Behold, the great and powerful, my magnificent and almighty nemisis!",
    "Doin a bamboozle fren.",
    "Your clicks per second are godly.",
    "What happens if I add chocolate milk to macaroni and cheese?",
    "Can you paint with all the colors of the wind",
    "Blue is greener than purple for sure",
    "I had something to say, then I forgot it.",
    "When nothing is right, go left.",
    "I need help, teach me how to play!",
    "Your personality shines brighter than the sun.",
    "You are very good at the game friend.",
    "I like pineapple on my pizza",
    "I like pasta, do you prefer nachos?",
    "I like Minecraft pvp but you are truly better than me!",
    "I have really enjoyed playing with you! <3",
    "ILY <3",
    "Pineapple doesn't go on pizza!",
    "Lets be friends instead of fighting okay?"
    ]
