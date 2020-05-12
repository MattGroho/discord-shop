import configparser
import discord
import asyncio
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import mysql.connector

from backend.lib.shop_queries import ShopQueries
from backend.lib.user_queries import UserQueries
from backend.lib.helper_commands import HelperCommands
from backend.lib.event_actions import EventActions


def main():
    config = configparser.ConfigParser()        # read and parse configuration file
    config.read(r'configuration.conf')

    token = config['Discord']['token']      # get the bot's unique token for sign-in
    paypal_channel_id = int(config['Discord']['paypal_channel_id'])     # id of the paypal channel
    event_channel_id = int(config['Discord']['event_channel_id'])  # id of the event channel
    shop_category_id = int(config['Discord']['shop_category_id'])  # id of the shop category
    control_category_id = int(config['Discord']['control_category_id'])  # id of the control panel category
    command_prefix = config['Discord']['prefix']

    username = config['Database']['username']       # get details for signing in to database
    password = config['Database']['password']
    host = config['Database']['host']
    database = config['Database']['database']

    cnx = mysql.connector.connect(user=username,
                                  password=password,
                                  host=host,
                                  database=database)        # connect to the database
    cursor = cnx.cursor()       # create cursor object for executing queries

    client = commands.Bot(command_prefix=command_prefix, case_insensitive=True)       # create the bot client

    # BOT EVENTS #

    @client.event
    async def on_ready():
        """
        on_ready() is called when the bot is signed in to Discord and ready to send/receive event notifications
        :return: none; print ready status to console
        """
        await client.change_presence(activity=discord.Game(name='Managing Shops'))
        print('We have logged in as {0.user}'.format(client))

    """
    async def sendreminders():
        remchan = client.get_channel(reminder_channel_id)
        command = 'select registration.user_id, game.name, event.title, DATE_FORMAT(event.date,"%M %d %Y")' \
                  ' from event inner join game on event.game_id = game.game_id'\
                  ' inner join registration on registration.event_id = event.event_id '\
                  ' where event.date > CURDATE() and event.date <= DATE_ADD(CURDATE(),INTERVAL 1 DAY)'
        cursor.execute(command)
        for line in cursor.fetchall():
            message = "Reminding <@%d> you are registered to play %s in '%s' on %s " % (line[0], line[1], line[2], line[3])
            await remchan.send(message)

    async def remindertask():
        hour = 23
        minute = 58
        await client.wait_until_ready()
        while not client.is_closed():
            now = datetime.now()
            future = datetime(now.year, now.month, now.day, hour, minute)
            if now.hour >= hour and now.minute > minute:
                future += timedelta(days=1)
            await asyncio.sleep((future - now).seconds)
            await sendreminders()

    client.loop.create_task(remindertask())
    """

    # RUN THE BOT #
    client.add_cog(HelperCommands(client, cursor, cnx))
    client.add_cog(UserQueries(client, cursor, cnx, shop_category_id, control_category_id))
    client.add_cog(ShopQueries(client, cursor, cnx, shop_category_id, control_category_id))
    client.add_cog(EventActions(client, cursor, cnx))
    client.run(token)


if __name__ == '__main__':
    main()
