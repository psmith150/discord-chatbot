from discord.ext import commands
from dotenv import load_dotenv
from requests import get, post
import os
import json

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='home')
    async def check_home(self, ctx, user):
        """Checks if the specified user is home"""
        if user is None:
            await ctx.send('Specify a user to query')
            return
        status = _get_home_status(user)
        await ctx.send(status)

    @check_home.error
    async def home_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
                await ctx.send('Please specify a user to check')

    @commands.command(name='announce')
    async def announce(self, ctx, *args):
        """Sends a message to a speaker"""
        if (len(args) == 0):
            await ctx.send("Please enter a message to announce")
            return
        message = ' '.join(args)
        status = _announce(message)
        await ctx.send(status)

def _get_home_status(user):
    """Queries the home status of a Home Assistant user"""
    load_dotenv()
    TOKEN = os.getenv('HOME_ASSISTANT_TOKEN')
    url = f"http://192.168.1.10:8123/api/states/person.{user.lower()}"
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'content-type': 'application/json',
    }
    response = get(url, headers=headers)
    if response.status_code == 404:
        return f'User {user} cannot be found.'
    response_data = response.json()
    state = response_data.get('state')
    if state is None:
        return 'Home state not defined'
    return f'{user} is currently {state}'

def _announce(message):
    """Announce a message over a speaker"""
    load_dotenv()
    TOKEN = os.getenv('HOME_ASSISTANT_TOKEN')
    url = f"http://192.168.1.10:8123/api/services/tts/google_say"
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'content-type': 'application/json',
    }
    response = post(url, json = {'message':message,'entity_id':'media_player.living_room_speaker'}, headers=headers)
    if response.status_code != 200:
        return f'Unable to process message "{message}"'
    return f'Your message "{message}" was announced!'

def setup(bot):
    bot.add_cog(General(bot))