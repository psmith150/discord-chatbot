from datetime import datetime, timedelta
from sqlite3 import register_converter
from discord.ext import commands, tasks
from pygrocy import Grocy as GrocyApp
from dotenv import load_dotenv
import os

class Grocy(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.output_channel_id = 769576139516674050
        self.overdue_chore_last_notified = {}
    
    #region Chores
    @tasks.loop(minutes=1)
    async def notify_chore_overdue(self) -> None:
        """Checks for any overdue chores and notifies the channel.
        Notifications will be sent every day until completed.
        """
        overdue_chores = get_overdue_chores()
        chores_to_notify = []
        notification_delta = timedelta(days=1)
        for chore in overdue_chores:
            last_notified = self.overdue_chore_last_notified.get(chore[0], None)
            if not last_notified or (datetime.now() - last_notified > notification_delta):
                chores_to_notify.append(chore)
        
        # Remove chores from tracking
        keys_to_remove = []
        for key in self.overdue_chore_last_notified.keys():
            match = next(chore for chore in overdue_chores if chore[0] == key)
            if not match:
                keys_to_remove.append(key)
        for key in keys_to_remove:
            del self.overdue_chore_last_notified[key]
        
        channel = self.bot.get_channel(self.output_channel_id)
        for chore in chores_to_notify:
            message = f'@here Chore {chore[1]} is overdue.'
            await channel.send(message)
            self.overdue_chore_last_notified[chore[0]] = datetime.now()
        pass

    @commands.command(name='chore-duedate')
    async def chore_due_date(self, ctx, *args) -> None:
        """Returns the next due date of the specified chore(s).

        Args:
            ctx (Context): The context of the command.
        """
        statuses = []
        if not args:
            statuses = get_chore_due_date()
        else:
            statuses = [get_chore_due_date(name) for name in args]
        messages = []
        for status in statuses:
            (name, due_date) = status
            messages.append(f'{name} is due at {due_date.strftime("%m-%d-%Y at %I:%M:%S %p")}.')
        if messages:
            await ctx.send('\n'.join(messages))
        else:
            await ctx.send('No due dates available.')
    #endregion Chores

    #region Stock
    @commands.command(name='stock-needed')
    async def get_stock_needed(self, ctx, *args) -> None:
        pass

    @tasks.loop()
    async def notify_stock_expired(self) -> None:
        pass
    #endregion Stock

def setup_grocy() -> GrocyApp:
    load_dotenv()
    grocy_token = os.getenv('GROCY_TOKEN')
    grocy_url = os.getenv('GROCY_URL')
    return GrocyApp(grocy_url, grocy_token, port=8080, verify_ssl=False)

#region Chore functions
def get_chore_due_date(name=None) -> 'list[tuple(str, datetime)]':
    grocy = setup_grocy()
    chores = grocy.chores(True)
    if name:
        queried_chores = [chore for chore in chores if chore.name == name]
    else:
        queried_chores = chores
    return [(chore.name, chore.next_estimated_execution_time) for chore in queried_chores]

def get_overdue_chores() -> 'list[tuple(int, str, datetime, str)]':
    grocy = setup_grocy()
    chores = grocy.chores(True)
    current_datetime = datetime.now()
    users = grocy.users()
    overdue_chores = []
    for chore in chores:
        if chore.next_estimated_execution_time < current_datetime:
            if not chore.next_execution_assigned_to_user_id:
                user = ''
            else:
                user = next(user for user in users if user.id == chore.next_execution_assigned_to_user_id)
            overdue_chores.append((chore.id, chore.name, chore.next_estimated_execution_time, user))
    return overdue_chores

#endregion Stock functions

def setup(bot):
    bot.add_cog(Grocy(bot))