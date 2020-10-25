"""Provides commands to be utilized by a Discord bot"""
from dotenv import load_dotenv
from requests import get, post
import os
import json

def get_home_status(user):
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

def announce(message):
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