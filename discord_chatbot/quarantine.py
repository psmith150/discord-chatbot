from discord.ext import commands, tasks
import re
from datetime import datetime, timedelta
import numbers
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'data' / 'quarantine.db'

class Quarantine(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.output_channel_id = 769576139516674050
        self.notify_quarantine_complete.start()
        self.archive_items.start()

    @commands.command(name='quarantine')
    async def quarantine(self, ctx, *, arg):
        """Sets a quarantine timer for a given item"""
        pattern = r'^([\w\s]+?)(?:\s([\d\.]+)\s([\w]+))?$'
        match = re.search(pattern, arg)
        if not match:
            await ctx.send("I didn't understand that; please enter your command like ""!quarantine item X days"".")
            return
        (name, time, unit) = match.groups()
        if time is not None:
            try:
                time = int(time)
            except:
                time = float(time)
        try:
            endtime = _start_quarantine(name, time, unit)
        except Exception as ex:
            await ctx.send('Unspecified error: ' + str(ex))
            return
        await ctx.send(f'{name} is quarantined until {endtime.strftime("%m-%d-%Y at %I:%M:%S %p")}')
    
    @commands.command(name='quarantine-status')
    async def quarantine_status(self, ctx, *args):
        """Returns the status of the quarantined items"""
        statuses = []
        if len(args) == 0:
            statuses = _get_quarantine_status()
        else:
            for name in args:
                statuses += _get_quarantine_status(name)
        messages = []
        for status in statuses:
            (name, end_date) = status
            messages.append(f'{name} is out of quarantine at {end_date.strftime("%m-%d-%Y at %I:%M:%S %p")}.')
        if len(messages) > 0:
            await ctx.send('\n'.join(messages))
    
    @tasks.loop(seconds=10)
    async def notify_quarantine_complete(self):
        data = _check_for_items_to_notify()
        if data is None or len(data) < 1:
            return
        message = '@here '
        for row in data:
            name = row[1]
            message = message + f'{name} is no longer in quarantine.\n'
        message = message.strip()
        channel = self.bot.get_channel(self.output_channel_id)
        await channel.send(message)
        ids = [x[0] for x in data]
        _set_items_as_notified(ids)
    
    @notify_quarantine_complete.before_loop
    async def before_quarantine_complete(self):
        await self.bot.wait_until_ready()
    
    @tasks.loop(hours=1)
    async def archive_items(self):
        _archive_items()
    
    @archive_items.before_loop
    async def before_archive_items(self):
        await self.bot.wait_until_ready()

def _start_quarantine(name, time=3, unit='days'):
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
    _create_quarantine_table(conn)
    _insert_quarantine_item(conn, name, starttime, endtime)
    conn.close()
    return endtime

def _get_quarantine_status(name=None):
    """
    Checks on the quarantine status of an item with a given name.
    Checks all items if name is None.
    If multiple items have the same name, checks all of them.
    """
    conn = _db_connect()
    _create_quarantine_table(conn)
    conn.row_factory = sqlite3.Row
    statuses = []
    if name is None:
        query = """SELECT name, end_date FROM quarantine
                WHERE is_active = 1
                ORDER BY start_date ASC"""
        cursor = conn.cursor()
        cursor.execute(query)
    else:
        query = """SELECT name, end_date FROM quarantine
                    WHERE name LIKE ? AND is_active = 1
                    ORDER BY start_date ASC"""
        cursor = conn.cursor()
        cursor.execute(query, (name,))
    results = cursor.fetchall()
    for row in results:
        statuses.append((row['name'], datetime.fromisoformat(row['end_date'])))
    conn.close()
    return statuses

def _check_for_items_to_notify():
    """
    Checks to see if there are any items that require notification to be given.
    """
    conn = _db_connect()
    _create_quarantine_table(conn)
    data = _check_quarantine_items(conn)
    conn.close()
    return data

def _set_items_as_notified(ids):
    """
    Sets any item in the specified list of IDs as notified.
    """
    conn = _db_connect()
    _create_quarantine_table(conn)
    for id in ids:
        _set_notified_status(conn, id, True)
    conn.close()

def _archive_items():
    """
    Marks any overdue items as not active.
    """
    conn = _db_connect()
    _create_quarantine_table(conn)
    delta = timedelta(days=1)
    _set_items_inactive(conn, delta)

#region DB functions
def _db_connect():
    """
    Connects to a SQLite database
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
    except Exception as ex:
        pass
    return conn

def _create_quarantine_table(conn):
    """
    Creates the table for quarantine data
    """
    query = """ CREATE TABLE IF NOT EXISTS quarantine (
                    id Integer PRIMARY KEY,
                    name text NOT NULL,
                    start_date text,
                    end_date text,
                    notified Integer NOT NULL,
                    is_active Integer NOT NULL
                );"""
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()

def _insert_quarantine_item(conn, name, starttime, endtime):
    """
    Inserts a new quarantine item into the table
    """
    query = """INSERT INTO quarantine(name, start_date, end_date, notified, is_active)
                VALUES(?,?,?,?,?)"""
    cursor = conn.cursor()
    cursor.execute(query, (name, starttime, endtime, 0, 1))
    conn.commit()

def _get_quarantine_item(conn, name):
    """
    Retrieves end date/time of the oldest quarantined item with the specified name.
    """
    query = """SELECT end_date FROM quarantine
                WHERE name LIKE ? & is_active = 1
                ORDER BY start_date ASC"""
    cursor = conn.cursor()
    cursor.execute(query, (name,))
    return cursor.fetchone()

def _check_quarantine_items(conn):
    """
    Checks the quarantined items for any that are out of quarantine
    """
    query = """SELECT id, name, end_date, notified FROM quarantine
                WHERE notified = 0 AND is_active = 1
                ORDER BY start_date ASC"""
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    currentdate = datetime.now()
    notification_data = []
    for row in results:
        enddate = datetime.fromisoformat(row['end_date'])
        if enddate <= currentdate:
            notification_data.append((row['id'], row['name']))
    return notification_data

def _set_notified_status(conn, id, notified=True):
    """
    Sets the notified status of the item with the given id.
    """
    query = """UPDATE quarantine
                SET notified = ?
                WHERE id = ?"""
    cursor = conn.cursor()
    cursor.execute(query, (1 if notified else 0,id))
    conn.commit()

def _set_items_inactive(conn, delta:timedelta):
    """
    Sets the active status of any item that is overdue
    """
    query = """SELECT id, end_date FROM quarantine
                WHERE is_active = 1"""
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    ids = []
    now = datetime.now()
    for row in results:
        if datetime.fromisoformat(row['end_date']) + delta <= now:
            ids.append((row['id'],))
    query = """UPDATE quarantine
                SET is_active = 0
                WHERE id=?"""
    cursor.executemany(query, ids)
    conn.commit()
    
#endregion

def setup(bot):
    bot.add_cog(Quarantine(bot))