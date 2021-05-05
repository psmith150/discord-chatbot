from discord.ext import commands
import os
from dotenv import load_dotenv
import bot_commands
import re

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

bot = commands.Bot(command_prefix='!')
bot.case_insensitive = True

@bot.command(name='home')
async def check_home(ctx, user):
    """Checks if the specified user is home"""
    if user is None:
        await ctx.send('Specify a user to query')
        return
    status = bot_commands.get_home_status(user)
    await ctx.send(status)

@check_home.error
async def home_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Please specify a user to check')

@bot.command(name='announce')
async def announce(ctx, *args):
    """Sends a message to a speaker"""
    if (len(args) == 0):
        await ctx.send("Please enter a message to announce")
        return
    message = ' '.join(args)
    status = bot_commands.announce(message)
    await ctx.send(status)

@bot.command(name='quarantine')
async def quarantine(ctx, *, arg):
    """Sets a quarantine timer for a given item"""
    pattern = r'^([\w\s]+?)(?:\s([\d\.]+)\s([\w]+))?$'
    match = re.search(pattern, arg)
    if not match:
        await ctx.send("I didn't understand that; please enter your command like ""!quarantine item X days"".")
        return
    (name, time, unit) = match.groups()
    print((name, time, unit))
    if time is not None:
        try:
            time = int(time)
        except:
            time = float(time)
    try:
        endtime = bot_commands.quarantine(name, time, unit)
    except Exception as ex:
        await ctx.send('Unspecified error: ' + str(ex))
        return
    await ctx.send(f'{name} is quarantined until {endtime.strftime("%m-%d-%Y at %I:%M:%S %p")}')

@bot.event
async def on_command_error(ctx, error):
    await ctx.send(f'Unspecified error in command {ctx.command.name}: ' + str(error))
        

bot.run(TOKEN)