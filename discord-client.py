from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

bot = commands.Bot(command_prefix='!')
bot.case_insensitive = True

@bot.command(name='hello', help='Greets you')
async def greeting(ctx):
    await ctx.send('Greetings!')

bot.run(TOKEN)