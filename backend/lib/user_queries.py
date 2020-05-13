import discord
from discord.ext import commands
from discord.utils import get
from backend.lib.helper_commands import check_admin_status, AdminPermissionError, check_user_exists, \
    create_user_control_panel, create_user_shop, get_user_control_panel, ControlPanelNotFoundError, ShopNotFoundError, \
    get_user_shop, delete_user_shop, delete_user_control_panel, get_name_from_id
from backend.lib.shop_queries import create_shop_sign


class UserQueries(commands.Cog):
    def __init__(self, bot, cursor, cnx, shop_category_id, control_category_id):
        self.bot = bot
        self.cursor = cursor
        self.cnx = cnx
        self.shop_category_id = shop_category_id
        self.control_category_id = control_category_id

    @commands.command()
    async def set_affiliate(self, ctx, user_id, status):
        """
        Update a user's affiliation status
        :param user_id: id of the user to set affiliation status
        :param status: status of their affiliation (true / false)
        :return: void
        """

        try:
            check_admin_status(ctx.author.id, False, self.cursor)
        except AdminPermissionError:
            await ctx.send("Error: You must be an admin to perform this command!")

        status = status.lower()

        if not (status == 'true' or status == 'false'):  # check for valid response
            await ctx.send("Error: Must provide a valid status for setting affiliate status! (eg. true / false)")
            return

        try:
            check_user_exists(user_id, self.cursor)
        except UserNotFoundError:
            await ctx.send("Error: Must provide a valid user id. This user doesn't exist!")
            return

        guild = ctx.guild
        user = guild.get_member(int(user_id))

        affiliate_role = get(guild.roles, name="Affiliate")

        if status == 'true':
            control_category = self.bot.get_channel(self.control_category_id)
            shop_category = self.bot.get_channel(self.shop_category_id)

            admin_role = get(guild.roles, name="Creator")

            control_overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                user: discord.PermissionOverwrite(read_messages=True),
                admin_role: discord.PermissionOverwrite(read_messages=True)
            }

            shop_overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
                user: discord.PermissionOverwrite(read_messages=True, send_messages=False),
                admin_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }

            control_channel = await control_category.create_text_channel(user.name + 's control panel',
                                                                         overwrites=control_overwrites)

            await control_channel.send("```Welcome to your shop control panel!\n\n"
                                       "Here you can run commands to modify your shop.\n\n"
                                       "Type *help to get started!```")

            await control_channel.send("```Please note additional help on commands can be found on our documentation page:\n\n"
                                       "https://docs.google.com/document/d/1CW68wzUiIkLB4gMXKQdhTLo8BhZQDTICi4i5kqe1iKA/edit?usp=sharing```")

            shop_name = user.name + 's shop'
            shop_desc = ""
            shop_channel = await shop_category.create_text_channel(shop_name, overwrites=shop_overwrites)

            shop_results = [shop_channel.id, user.id, shop_desc, 0, -1]
            shop_msg = await shop_channel.send(create_shop_sign(user, shop_results, self.cursor))

            create_user_control_panel(user_id, control_channel.id, self.cursor, self.cnx)
            create_user_shop(user_id, shop_channel.id, shop_name, shop_desc, 0, shop_msg.id, self.cursor, self.cnx)

            await user.add_roles(affiliate_role)
            await ctx.send("Successfully updated " + user.name + "'s affiliate status to true!")
        else:
            # Try to delete control channel
            try:
                control_channel_id = get_user_control_panel(user_id, self.cursor)
                await self.bot.get_channel(control_channel_id).delete()
                delete_user_control_panel(user_id, self.cursor, self.cnx)
            except ControlPanelNotFoundError:
                pass

            # Try to delete shop channel
            try:
                shop_channel_id = get_user_shop(user_id, self.cursor)
                await self.bot.get_channel(shop_channel_id).delete()
                delete_user_shop(user_id, self.cursor, self.cnx)
            except ShopNotFoundError:
                pass

            await user.remove_roles(affiliate_role)
            await ctx.send("Successfully updated " + user.name + "'s affiliate status to false!")

    @commands.command()
    async def set_admin_status(self, ctx, user_id, status):
        """
        Update a user's admin status
        :param user_id: id of user to be updated
        :param status: status of admin (true / false)
        :return: the updated user table or an error message
        """
        try:
            message = sql_set_admin_status(ctx.author.id, user_id, status, self.cursor, self.cnx)
        except AdminPermissionError:
            await ctx.send("Permission Error encountered.  You do not have permission to edit the database")
        except UserNotFoundError:
            await ctx.send("Error: you are attempting to modify a user that does not exist.")
        except ResponseError:
            await ctx.send("Error: please supply either TRUE or FALSE for new admin status")
        else:
            await ctx.send(message)


# SQL FUNCTIONS #


def sql_delete_user(user_id, cursor, cnx):
    """
    Delete a row from the user table based on display name.
    :param user_id: id of the user to be deleted
    :param cursor: cursor object for executing query
    :param cnx: connection object for committing changes
    :return: the new table after deletion or an error flag
    """
    if check_user_exists(user_id, cursor) == -1:
        raise UserNotFoundError()

    cursor.execute('delete from user where user_id = %s', (user_id,))  # execute deletion query
    cnx.commit()  # commit changes to database


def sql_add_user(user_id, display_name, email, is_admin, rank, joindate, cursor, cnx):
    if check_user_exists(user_id, cursor) != -1:
        raise ExistingUserError()

    if not (is_admin.lower() == 'true' or is_admin.lower() == 'false'):  # check for valid response
        raise ResponseError()

    cursor.execute('insert into user '
                   'values (%s, %s, %s, %s, %s, %s)',
                   (user_id, display_name, email, 1 if is_admin == "true" else 0, rank, joindate))
    cnx.commit()  # commit changes to database


def sql_set_admin_status(auth_user, user_id, new_status, cursor, cnx):
    """
    Update the admin status associated with a user.
    :param auth_user: id of user authorizing change
    :param user_id: id of user whose admin status will be changed
    :param new_status: true or false depending on admin status being set
    :param cursor: cursor object to execute query
    :param cnx: connection object to commit changes
    :return: the new table after updating the user table
    """
    check_admin_status(auth_user, True, cursor)  # see if the authorizing user is an admin

    if check_user_exists(user_id, cursor) == -1:
        raise UserNotFoundError()

    if not (new_status.lower() == 'true' or new_status.lower() == 'false'):  # check for valid response
        raise ResponseError()

    cursor.execute('update user '
                   'set admin = %s '
                   'where user_id = %s', (1 if new_status == "true" else 0, user_id))
    cnx.commit()  # commit changes to user table
    cursor.execute('select * from user where user_id = %s', (user_id,))  # get new user table
    return cursor.fetchall()


# ERRORS #

class Error(Exception):
    """Base class for exceptions in this module."""


class UserNotFoundError(Error):
    """User not found in database."""


class ResponseError(Error):
    """Invalid response or argument supplied."""


class ExistingUserError(Error):
    """Trying to create a user that already exists"""
