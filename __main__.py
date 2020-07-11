import discord
from discord.ext import commands
from discord.utils import get
import youtube_dl
import os
import shutil
import sqlite3
from os import system
import discordToken

system("cls")

token = discordToken.token

BOT_PREFIX = '!'

bot = commands.Bot(command_prefix=BOT_PREFIX)
bot.remove_command("help")

DIR = os.path.dirname(__file__)
db = sqlite3.connect(os.path.join(DIR, "SongTracker.db"))
SQL = db.cursor()

queueDictionary = {}


# Signifies the bot is online
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name='!help'))
    print("Logged in as: " + bot.user.name + "\n")


# Joins the voice channel
@bot.command(pass_context=True, aliases=['j', 'joi'])
async def join(ctx):
    SQL.execute('create table if not exists Music('
                '"Num" integer not null primary key autoincrement, '
                '"Server_ID" integer, '
                '"Server_Name" text, '
                '"Voice_ID" integer, '
                '"Voice_Name" text, '
                '"User_Name" text, '
                '"Next_Queue" integer, '
                '"Queue_Name" text, '
                '"Song_Name" text'
                ')')
    server_name = str(ctx.guild)
    server_id = ctx.guild.id
    SQL.execute(f'delete from music where Server_ID ="{server_id}" and Server_Name = "{server_name}"')
    db.commit()
    user_name = str(ctx.message.author)
    queue_name = f"Queue#{server_id}"
    song_name = f"Song#{server_id}"
    channel_id = ctx.message.author.voice.channel.id
    channel_name = str(ctx.message.author.voice.channel)
    queue_num = 1
    SQL.execute(
        'insert into Music(Server_ID, Server_Name, Voice_ID, Voice_Name, User_Name, Next_Queue, Queue_Name, '
        'Song_Name) values(?,?,?,?,?,?,?,?)',
        (server_id, server_name, channel_id, channel_name, user_name, queue_num, queue_name, song_name))
    db.commit()

    channel = ctx.message.author.voice.channel
    voice = get(bot.voice_clients, guild=ctx.guild)

    if voice is not None:
        return await voice.move_to(channel)

    await channel.connect()

    print(f"The bot has connected to {channel}\n")

    await ctx.send(f"Joined {channel}")


@bot.command(pass_context=True)
async def test(ctx):
    id = ctx.guild
    id_hash = hash(id)
    user_name = str(ctx.message.author)
    print(ctx.guild.id)


# leaves the voice channel
@bot.command(pass_context=True, aliases=['l', 'lea'])
async def leave(ctx):
    server_name = str(ctx.guild)
    server_id = ctx.guild.id
    channel_id = ctx.message.author.voice.channel.id
    channel_name = str(ctx.message.author.voice.channel)
    SQL.execute(
        f'delete from music where Server_ID ="{server_id}" and Server_Name = "{server_name}" and Voice_ID="{channel_id}" and Voice_Name="{channel_name}"')
    db.commit()

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
async def play(ctx, *url: str):
    server_name = str(ctx.guild)
    server_id = ctx.guild.id
    channel_id = ctx.message.author.voice.channel.id
    channel_name = str(ctx.message.author.voice.channel)
    try:
        SQL.execute(
            f'select Song_Name from Music where Server_ID="{server_id}" and Server_Name="{server_name}" and Voice_ID="{channel_id}" and Voice_Name="{channel_name}"')
        name_song = SQL.fetchone()
        SQL.execute(f'select Server_Name from Music where Server_ID="{server_id}" and Server_Name="{server_name}"')
        name_server = SQL.fetchone()
    except:
        await ctx.send("The bot must join a voice channel to play a song: Join one and use '/join'")
        return

    def check_queue():

        DIR = os.path.dirname(__file__)
        db = sqlite3.connect(os.path.join(DIR, "SongTracker.db"))
        SQL = db.cursor()
        SQL.execute(f'select Queue_Name from Music where Server_ID="{server_id}" and Server_Name="{server_name}"')
        name_queue = SQL.fetchone()
        SQL.execute(f'select Server_Name from Music where Server_ID="{server_id}" and Server_Name="{server_name}"')
        name_server = SQL.fetchone()

        Queue_infile = os.path.isdir("./Queues")
        if Queue_infile is True:
            DIR = os.path.abspath(os.path.realpath("Queues"))
            Queue_Main = os.path.join(DIR, name_queue[0])
            length = len(os.listdir(Queue_Main))
            still_q = length - 1
            try:
                first_file = os.listdir(Queue_Main)[0]

                song_num = first_file.split('-')[0]
            except:
                print("No more queued song(s)\n")
                SQL.execute('update Music set Next_Queue = 1 where Server_ID = ? and Server_Name = ?',
                            (server_id, server_name))
                db.commit()
                return

            main_location = os.path.dirname(os.path.realpath(__file__))
            song_path = os.path.abspath(os.path.realpath(Queue_Main) + "\\" + first_file)
            if length != 0:
                print("Song done, playing next queued\n")
                print(f"Songs still in queue: {still_q}")
                song_there = os.path.isfile(f"{name_song[0]}({name_server[0]}).mp3")
                if song_there:
                    os.remove(f"{name_song[0]}({name_server[0]}).mp3")
                shutil.move(song_path, main_location)
                for file in os.listdir("./"):
                    if file == f"{song_num}-{name_song[0]}({name_server[0]}).mp3":
                        os.rename(file, f'{name_song[0]}({name_server[0]}).mp3')
                voice.play(discord.FFmpegPCMAudio("song.mp3"), after=lambda e: check_queue())
                voice.source = discord.PCMVolumeTransformer(voice.source)
                voice.source.volume = 0.50

            else:
                SQL.execute('update Music set Next_Queue = 1 where Server_ID = ? and Server_Name = ?',
                            (server_id, server_name))
                db.commit()
                return

        else:
            SQL.execute('update Music set Next_Queue = 1 where Server_ID = ? and Server_Name = ?',
                        (server_id, server_name))
            db.commit()
            print("No songs were queued before the ending of the last song\n")

    song_there = os.path.isfile(f"{name_song[0]}({name_server[0]}).mp3")
    try:
        if song_there:
            os.remove(f"{name_song[0]}({name_server[0]}).mp3")
            SQL.execute('update Music set Next_Queue = 1 where Server_ID = ? and Server_Name = ?',
                        (server_id, server_name))
            db.commit()
            print("Removed old song file")
    except PermissionError:
        print("Trying to delete song file, but it's being played")
        await ctx.send("ERROR: Music playing")
        return

    SQL.execute(f'select Queue_Name from Music where Server_ID="{server_id}" and Server_Name="{server_name}"')
    name_queue = SQL.fetchone()
    queue_infile = os.path.isdir("./Queues")
    if queue_infile is True:
        DIR = os.path.abspath(os.path.realpath("Queues"))
        Queue_Main = os.path.join(DIR, name_queue[0])
        Queue_Main_infile = os.path.isdir(Queue_Main)
        if Queue_Main_infile is True:
            print("Removed old queue folder")
            shutil.rmtree(Queue_Main)

    await ctx.send("Getting Everything Ready.")

    voice = get(bot.voice_clients, guild=ctx.guild)
    song_path = f"./{name_song[0]}({name_server[0]}).mp3"

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': False,
        'outtmpl': song_path,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    song_search = " ".join(url)

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            print("Downloading audio now\n")
            info = ydl.extract_info(f"ytsearch1:{song_search}", download=False)
            info_dict = info.get('entries', None)[0]
            print(info_dict)
            video_title = info_dict.get('title', None)
            ydl.download([f"ytsearch1:{song_search}"])

    except:
        print("FALLBACK: youtube-dl does not support this URL, using Spotify (This is normal if spotify URL)")
        c_path = os.path.dirname(os.path.realpath(__file__))
        system(f"spotdl -ff {name_song[0]}({name_server[0]}) -f " + '"' + c_path + '"' + " -s " + song_search)

    voice.play(discord.FFmpegPCMAudio(f"{name_song[0]}({name_server[0]}).mp3"), after=lambda e: check_queue())
    voice.source = discord.PCMVolumeTransformer(voice.source)
    voice.source.volume = 0.50

    await ctx.send(f"Now playing: {video_title}")

    print("playing\n")


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
    server_name = str(ctx.guild)
    server_id = ctx.guild.id
    SQL.execute('update Music set Next_Queue = 1 where Server_ID = ? and Server_Name = ?', (server_id, server_name))
    db.commit()
    SQL.execute(f'select Queue_Name from Music where Server_ID="{server_id}" and Server_Name="{server_name}"')
    name_queue = SQL.fetchone()

    queue_infile = os.path.isdir("./Queues")
    if queue_infile is True:
        DIR = os.path.abspath(os.path.realpath("Queues"))
        Queue_Main = os.path.join(DIR, name_queue[0])
        Queue_Main_infile = os.path.isdir(Queue_Main)
        if Queue_Main_infile is True:
            shutil.rmtree(Queue_Main)

    voice = get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_playing():
        print("Music stopped")
        voice.stop()
        await ctx.send("Music stopped")
    else:
        print("No music playing failed to stop")
        await ctx.send("No music playing failed to stop")


@bot.command(pass_context=True, aliases=['q', 'que'])
async def queue(ctx, *url: str):
    server_name = str(ctx.guild)
    server_id = ctx.guild.id
    try:
        SQL.execute(f'select Queue_Name from Music where Server_ID="{server_id}" and Server_Name="{server_name}"')
        name_queue = SQL.fetchone()
        SQL.execute(f'select Song_Name from Music where Server_ID="{server_id}" and Server_Name="{server_name}"')
        name_song = SQL.fetchone()
        SQL.execute(f'select Next_Queue from Music where Server_ID="{server_id}" and Server_Name="{server_name}"')
        q_num = SQL.fetchone()
    except:
        await ctx.send("The bot must join a voice channel to queue a song: Join by using '/join'")
        return

    Queue_infile = os.path.isdir("./Queues")
    if Queue_infile is False:
        os.mkdir("Queues")
    DIR = os.path.abspath(os.path.realpath("Queues"))
    Queue_Main = os.path.join(DIR, name_queue[0])
    Queue_Main_infile = os.path.isdir(Queue_Main)
    if Queue_Main_infile is False:
        os.mkdir(Queue_Main)

    SQL.execute(f'select Server_Name from Music where Server_ID="{server_id}" and Server_Name="{server_name}"')
    name_server = SQL.fetchone()
    queue_path = os.path.abspath(os.path.realpath(Queue_Main) + f"\\{q_num[0]}-{name_song[0]}({name_server[0]}).mp3")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': queue_path,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',

        }],
    }

    song_search = " ".join(url)

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            print("Downloading audio now\n")
            ydl.download([f"ytsearch1:{song_search}"])
            info = ydl.extract_info(f"ytsearch1:{song_search}", download=False)
            info_dict = info.get('entries', None)[0]
            video_title = info_dict.get('title', None)
    except:
        print("FALLBACK: youtube-dl does not support this URL, using Spotify (This is normal if spotify URL)")
        q_path = os.path.abspath(os.path.realpath("Queue"))
        Q_DIR = os.path.abspath(os.path.realpath("Queues"))
        Queue_Path = os.path.join(Q_DIR, name_queue[0])
        system(
            f"spotdl -ff {q_num[0]}-{name_song[0]}({name_server[0]}) -f " + '"' + Queue_Path + '"' + " -s " + song_search)

    await ctx.send(f"Added, '{video_title}', to the queue")

    SQL.execute('update Music set Next_Queue = Next_Queue + 1 where Server_ID = ? and Server_Name = ?',
                (server_id, server_name))
    db.commit()

    print(f"added to queue\n")


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


@bot.command(pass_context=True, aliases=['v', 'vol'])
async def volume(ctx, volume: int):
    if ctx.voice_client is None:
        return await ctx.send("Not connected to voice channel.")

    print(volume / 100)

    ctx.voice_client.source.volume = volume / 100
    await ctx.send(f"Changed volume to {volume}%")


@bot.command(pass_context=True, aliases=['rewind', 're'])
async def restart(ctx):
    voice = get(bot.voice_clients, guild=ctx.guild)
    if os.path.isfile("song.mp3"):
        voice.stop()
        voice.play(discord.FFmpegPCMAudio("song.mp3"))
        voice.source = discord.PCMVolumeTransformer(voice.source)
        voice.source.volume = 0.50
        print("rewinding song now.")
        await ctx.send("Rewinding song!")
    else:
        print("No song, didn't rewind.")
        await ctx.send("Nothing to rewind!")


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
    embed.add_field(name='Aliases for "!restart"', value='"rewind", "re"', inline=False)
    embed.add_field(name='Aliases for "!loop', value='none', inline=False)
    embed.add_field(name='Aliases for "!volume"', value='"v", "vol"', inline=False)

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
    embed.add_field(name='!restart', value='restarts the song currently playing', inline=False)
    embed.add_field(name='!loop', value='loops currently playing song indefinitely', inline=False)
    embed.add_field(name='!volume', value='you can increase the volume, by adding a number from 1-100 after the '
                                          'command. The higher the number the louder the song will play', inline=False)

    await ctx.message.author.send(mention, embed=embed)
    await ctx.send(f"I've sent {mention} a DM informing them of my commands!")


bot.run(token)
