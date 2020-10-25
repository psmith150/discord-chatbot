from discord.ext import commands
import os
from dotenv import load_dotenv
import bot_commands

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

@bot.command(name='announce')
async def announce(ctx, *args):
    """Sends a message to a speaker"""
    if (len(args) == 0):
        await ctx.send("Please enter a message to announce")
        return
    message = ' '.join(args)
    status = bot_commands.announce(message)
    await ctx.send(status)

@bot.event
async def on_command_error(ctx, error):
    if ctx.command.qualified_name == 'home':
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Please specify a user to check')

bot.run(TOKEN)