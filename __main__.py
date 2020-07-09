import discord
from discord.ext import commands
from discord.utils import get
import youtube_dl
import os
import shutil
from os import system
import discordToken

system("cls")

token = discordToken.token

BOT_PREFIX = '!'

bot = commands.Bot(command_prefix=BOT_PREFIX)
bot.remove_command("help")

queueDictionary = {}


# Signifies the bot is online
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name='!help'))
    print("Logged in as: " + bot.user.name + "\n")


# Joins the voice channel
@bot.command(pass_context=True, aliases=['j', 'joi'])
async def join(ctx):
    global voice
    channel = ctx.message.author.voice.channel
    voice = get(bot.voice_clients, guild=ctx.guild)

    if voice and voice.is_connected():
        await voice.move_to(channel)
    else:
        voice = await channel.connect()

    await voice.disconnect()

    if voice and voice.is_connected():
        await voice.move.to(channel)
    else:
        voice = await channel.connect()
        print(f"The bot has connected to {channel}\n")

    await ctx.send(f"Joined {channel}.")


# leaves the voice channel
@bot.command(pass_context=True, aliases=['l', 'lea'])
async def leave(ctx):
    channel = ctx.message.author.voice.channel
    voice = get(bot.voice_clients, guild=ctx.guild)

    if voice and voice.is_connected():
        await voice.disconnect()
        print(f"The bot has left {channel}.")
        await ctx.send(f"Left {channel}.")
    else:
        print("Bot was told to leave voice channel but was not in one.")
        await ctx.send("Don't think I was in a voice channel.")


# plays song
@bot.command(pass_context=True, aliases=['p', 'pla'])
async def play(ctx, url: str):
    def check_queue():
        Queue_infile = os.path.isdir("./Queue")
        if Queue_infile is True:
            DIR = os.path.abspath(os.path.realpath("Queue"))
            length = len(os.listdir(DIR))
            still_q = length - 1
            try:
                first_file = os.listdir(DIR)[0]
            except:
                print("No more queued song(s).\n")
                queueDictionary.clear()
                return
            main_location = os.path.dirname(os.path.realpath(__file__))
            song_path = os.path.abspath(os.path.realpath("Queue") + "\\" + first_file)
            if length != 0:
                print("Song done, playing next queued song\n")
                print(f"songs still in queue: {still_q}")
                song_there = os.path.isfile("song.mp3")
                if song_there:
                    os.remove("song.mp3")
                shutil.move(song_path, main_location)
                for file in os.listdir("./"):
                    if file.endswith(".mp3"):
                        os.rename(file, "song.mp3")

                voice.play(discord.FFmpegPCMAudio("song.mp3"), after=lambda e: check_queue())
                voice.source = discord.PCMVolumeTransformer(voice.source)
                voice.source.volume = 0.50
            else:
                queueDictionary.clear()
                return
        else:
            queueDictionary.clear()
            print("No songs were queued before the end of the last song.\n")

    song_there = os.path.isfile("song.mp3")
    try:
        if song_there:
            os.remove("song.mp3")
            queueDictionary.clear()
            print("Removed old song file")
    except PermissionError:
        print("Trying to delete song file, but it's being played")
        await ctx.send("ERROR: Music playing")
        return

    Queue_infile = os.path.isdir("./Queue")
    try:
        Queue_folder = "./Queue"
        if Queue_infile is True:
            print("Removed old queue folder.\n")
            shutil.rmtree(Queue_folder)
    except:
        print("No old queue folder")

    await ctx.send("Getting Everything Ready.")

    voice = get(bot.voice_clients, guild=ctx.guild)

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',

        }],
    }

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            print("Downloading song now.\n")
            ydl.download([url])
    except:
        print("FALLBACK: youtube-dl does not support this URL, using Spotify (This is normal if Spotify URL)")
        c_path = os.path.dirname(os.path.realpath(__file__))
        system("spotdl -f " + '"' + c_path + '"' + " -s " + url)

    for file in os.listdir("./"):
        if file.endswith(".mp3"):
            name = file
            print(f"Renamed File:{file}\n")
            os.rename(file, "song.mp3")

    voice.play(discord.FFmpegPCMAudio("song.mp3"), after=lambda e: check_queue())
    voice.source = discord.PCMVolumeTransformer(voice.source)
    voice.source.volume = 0.50
    try:
        nname = name.rsplit("-", 2)
        await ctx.send(f"Playing: {nname[0]}.")
    except:
        await ctx.send(f"Playing Song")

    print("Playing.\n")


# pauses song

@bot.command(pass_context=True, aliases=['pa', 'pau'])
async def pause(ctx):
    voice = get(bot.voice_clients, guild=ctx.guild)

    if voice and voice.is_playing():
        print('Music paused.')
        voice.pause()
        await ctx.send("Music paused.")
    else:
        print("Music not playing")
        await ctx.send("Music not playing. Could not Pause.")


# resumes song

@bot.command(pass_context=True, aliases=['res', 'r'])
async def resume(ctx):
    voice = get(bot.voice_clients, guild=ctx.guild)

    if voice and voice.is_paused():
        print("Resumed music.")
        voice.resume()
        await ctx.send("Music has been resumed.")
    else:
        print("Music is not paused")
        await ctx.send("Music is not Paused")


# stops song

@bot.command(pass_context=True, aliases=['s', 'sto'])
async def stop(ctx):
    voice = get(bot.voice_clients, guild=ctx.guild)

    queueDictionary.clear()

    queue_infile = os.path.isdir("./Queue")
    if queue_infile is True:
        shutil.rmtree("./Queue")

    if voice and voice.is_playing():
        print('Music Stopped.')
        voice.stop()
        await ctx.send("The music has ended :(")
    else:
        print("No music playing, didn't stop.")
        await ctx.send("There was no music to be stopped.")


@bot.command(pass_context=True, aliases=['q', 'que'])
async def queue(ctx, url: str):
    Queue_infile = os.path.isdir("./Queue")
    if Queue_infile is False:
        os.mkdir("Queue")
    DIR = os.path.abspath(os.path.realpath("Queue"))
    q_num = len(os.listdir(DIR))
    q_num += 1
    add_queue = True
    while add_queue:
        if q_num in queueDictionary:
            q_num += 1
        else:
            add_queue = False
            queueDictionary[q_num] = q_num

    queue_path = os.path.abspath(os.path.realpath("Queue") + f"\song{q_num}.%(ext)s")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': queue_path,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',

        }],
    }
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            print("Downloading audio now\n")
            ydl.download([url])
    except:
        print("FALLBACK: youtube-dl does not support this URL, using Spotify (This is normal if spotify URL)")
        q_path = os.path.abspath(os.path.realpath("Queue"))
        system(f"spotdl -ff -f " + '"' + q_path + '"' + " -s " + url)

    await ctx.send("Adding song" + str(q_num) + " to the queue.")

    print("Song added to queue\n")

    @bot.command(pass_context=True, aliases=['next', 'sk', 'n'])
    async def skip(ctx):
        voice = get(bot.voice_clients, guild=ctx.guild)

        if voice and voice.is_playing():
            print('Playing next song.')
            voice.stop()
            await ctx.send("Next Song")
        else:
            print("No music playing, failed to play next song.")
            await ctx.send("There was no music to be skipped.")


@bot.command(pass_context=True, aliases=['a'])
async def aliases(ctx):
    mention = ctx.message.author.mention
    embed = discord.Embed(
        colour=discord.Colour.blue()
    )

    embed.set_author(name='Aliases')
    embed.add_field(name='Aliases for "!join"', value='"j", "joi"', inline=False)
    embed.add_field(name='Aliases for "!leave"', value='"l", "lea"', inline=False)
    embed.add_field(name='Aliases for "!play"', value='"p", "pla"', inline=False)
    embed.add_field(name='Aliases for "!pause"', value='"pa", "pau"', inline=False)
    embed.add_field(name='Aliases for "!resume"', value='"r", "res"', inline=False)
    embed.add_field(name='Aliases for "!stop"', value='"s", "sto"', inline=False)
    embed.add_field(name='Aliases for "!queue"', value='"q", "que"', inline=False)
    embed.add_field(name='Aliases for "!invite"', value='"inv, "invi"', inline=False)
    embed.add_field(name='Aliases for "!skip"', value='"nex", "ski", "sk", "n"', inline=False)
    embed.add_field(name='Aliases for "!aliases"', value='"a"', inline=False)
    await ctx.send(mention, embed=embed)
    await ctx.send(f"Here are the aliases, {mention}!")


@bot.command(pass_context=True, aliases=['inv', 'invi'])
async def invite(ctx):
    link = await ctx.channel.create_invite(max_age=300)
    await ctx.send("Here is an invite to your server:" + " " + str(link))


@bot.command(pass_context=True, aliases=['h'])
async def help(ctx):
    print("The user has decided to ask the bot for help.")
    mention = ctx.message.author.mention
    embed = discord.Embed(
        colour=discord.Colour.orange()
    )

    embed.set_author(name='Commands')
    embed.add_field(name='!join', value='joins a voice channel', inline=False)
    embed.add_field(name='!leave', value='leaves the voice channel', inline=False)
    embed.add_field(name='!play', value='plays a song, add a Youtube/Spotify link after the command', inline=False)
    embed.add_field(name='!pause', value='pauses the song currently playing', inline=False)
    embed.add_field(name='!resume', value='resumes the song after being paused', inline=False)
    embed.add_field(name='!stop', value='stops the song currently being played, and ends the queue', inline=False)
    embed.add_field(name='!queue', value='you can queue songs', inline=False)
    embed.add_field(name='!invite', value='you can get the invite link for your server', inline=False)
    embed.add_field(name='!skip', value='you can skip the song, and go to the next song in the queue', inline=False)
    embed.add_field(name='!aliases', value='you can view the aliases for each command', inline=False)

    await ctx.message.author.send(mention, embed=embed)
    await ctx.send(f"I've sent {mention} a DM informing them of my commands!")


bot.run(token)
