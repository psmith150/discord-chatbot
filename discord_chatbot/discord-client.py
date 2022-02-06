from discord.ext import commands
import os
from dotenv import load_dotenv
import re

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

bot = commands.Bot(command_prefix='!')
bot.case_insensitive = True

@bot.event
async def on_command_error(ctx, error):
    await ctx.send(f'Unspecified error in command {ctx.command.name}: ' + str(error))

bot.load_extension('general')
bot.load_extension('quarantine')

bot.run(TOKEN)