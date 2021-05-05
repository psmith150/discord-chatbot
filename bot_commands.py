"""Provides commands to be utilized by a Discord bot"""
from dotenv import load_dotenv
from requests import get, post
import os
import json
from datetime import datetime, timedelta
import numbers
import sqlite3

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

def quarantine(name, time=3, unit='days'):
    if time is None:
        time = 3
    if unit is None:
        unit = 'days'
    if not isinstance(time, numbers.Number):
        raise ValueError('Specified time is not a valid number')
    delta = None
    if unit == 'day' or unit == 'days':
        delta = timedelta(days=time)
    elif unit == 'week' or unit == 'weeks':
        delta = timedelta(weeks=time)
    elif unit == 'hour' or unit == 'hours':
        delta = timedelta(hours=time)
    elif unit == 'minute' or unit == 'minutes':
        delta = timedelta(minutes=time)
    elif unit == 'second' or unit == 'seconds':
        delta = timedelta(seconds=time)
    elif unit == 'millisecond' or unit == 'milliseconds':
        delta = timedelta(milliseconds=time)
    elif unit == 'microsecond' or unit == 'microseconds':
        delta = timedelta(microseconds=time)
    else:
        raise ValueError('Specified time unit is not valid.')
    starttime = datetime.now()
    endtime = starttime + delta
    conn = _db_connect()
    _db_create_quarantine_table(conn)
    _insert_quarantine_item(conn, name, starttime, endtime)
    conn.close()
    return endtime

def _db_connect():
    """
    Connects to a SQLite database
    """
    conn = None
    try:
        conn = sqlite3.connect('data.db')
    except Exception as ex:
        pass
    return conn

def _db_create_quarantine_table(conn):
    """
    Creates the table for quarantine data
    """
    query = """ CREATE TABLE IF NOT EXISTS quarantine (
                    id Integer PRIMARY KEY,
                    name text NOT NULL,
                    start_date text,
                    end_date text,
                    notified Integer NOT NULL
                );"""
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()

def _insert_quarantine_item(conn, name, starttime, endtime):
    """
    Inserts a new quarantine item into the table
    """
    query = """INSERT INTO quarantine(name, start_date, end_date, notified)
                VALUES(?,?,?,?)"""
    cursor = conn.cursor()
    cursor.execute(query, (name, starttime, endtime, 0))
    conn.commit()

def _get_quarantine_item(conn, name):
    """
    Retrieves end date/time of the oldest quarantined item with the specified name.
    """
    query = """SELECT end_date FROM quarantine
                WHERE name LIKE ?
                ORDER BY start_date ASC"""
    cursor = conn.cursor()
    cursor.execute(query, (name,))
    return cursor.fetchone()

def _check_quarantine_items(conn):
    """
    Checks the quarantined items for any that are out of quarantine
    """
    query = """SELECT id, name, end_date, notified FROM quarantine
                WHERE notified = 0
                ORDER BY start_date ASC"""
    update_query = """UPDATE quarantine
                        SET notified = 1
                        WHERE id = ?"""
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    currentdate = datetime.now()
    notification_names = []
    for row in results:
        enddate = datetime.fromisoformat(row['end_date'])
        if enddate <= currentdate:
            notification_names.append(row['name'])
            cursor.execute(update_query, (row['id'],))
    conn.commit()
    return notification_names
