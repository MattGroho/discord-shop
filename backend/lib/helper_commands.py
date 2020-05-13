from discord.ext import commands


class HelperCommands(commands.Cog):
    def __init__(self, bot, cursor, cnx):
        self.bot = bot
        self.cursor = cursor
        self.cnx = cnx

    @commands.command(name='exit')
    async def exit_bot(self, ctx):
        """
        Prompt bot to logout
        :return: none
        """
        self.cursor.close()
        self.cnx.close()
        await self.bot.logout()  # log the bot out


# HELPER FUNCTIONS #


def check_admin_status(user_id, add, cursor):
    """
    Check to see if a given user is an admin.  Only admins can change the database.
    :param user_id: id of requesting user
    :param add: True if adding to database, False if deleting from database
    :param cursor: cursor object for executing search query
    :return: Raise AdminPermissionError if user is not admin or does not exist,Nothing if the user is an admin
    """
    cursor.execute('select admin from user where user_id = %s', (user_id,))
    result = cursor.fetchall()

    if add and (len(result) == 0 or result[0][0] == 0):  # adding to the database
        raise AdminPermissionError(user_id)
    elif not add and (len(result) > 0 and result[0][0] == 1):  # removing from the database
        raise AdminPermissionError(user_id)


def get_user_control_panel(user_id, cursor):
    """
    Gets a users control panel
    :param user_id: the id of the
    :param cursor: cursor object for executing search query
    :return: ControlPanelNotFoundError if control panel not found, control panel id if successful
    """
    cursor.execute('select shop_category_id from shop_control where owner = %s', (user_id,))
    result = cursor.fetchall()

    if len(result) == 0:  # user not in control panel
        raise ControlPanelNotFoundError

    return result[0][0]


def in_control_panel(user_id, channel_id, cursor):
    """
    Checks to see if a user is in their shop control panel
    :param user_id: the id of the user we want to check
    :param channel_id: the channel id of the channel they are typing in
    :param cursor: cursor object for executing search query
    :return: Raise CommandNotControlPanel if user is not in their control panel channel, or nothing if successful
    """
    cursor.execute('select owner from shop_control where owner = %s and shop_category_id = %s', (user_id, channel_id))
    result = cursor.fetchall()

    if len(result) == 0: # user not in control panel
        raise CommandNotControlPanelError


def get_user_shop(user_id, cursor):
    """
    Gets the shop id of a given user
    :param user_id: the id of the user we want to get the shop for
    :param cursor: cursor object for executing search query
    :return: Raise ShopNotFoundError if user doesn't have a shop, shop_id if they do
    """
    cursor.execute('select shop_id from shop where owner = %s', (user_id,))
    result = cursor.fetchall()

    if len(result) == 0:  # user not in control panel
        raise ShopNotFoundError

    return result[0][0]


def get_shop(shop_id, cursor):
    cursor.execute('select * from shop where shop_id = %s', (shop_id,))
    result = cursor.fetchall()

    if len(result) == 0:  # shop not found
        raise ShopNotFoundError

    return result[0]


def get_shop_status(shop_id, cursor):
    """
    Gets the status of the shop being open
    :param shop_id: the id of the shop we want to check the open status for
    :param cursor: cursor object for executing search query
    :return: Raise ShopNotFoundError if the shop doesn't exit, open status if the shop exists
    """
    cursor.execute('select status from shop where shop_id = %s', (shop_id,))
    result = cursor.fetchall()

    if len(result) == 0:  # user not in shop
        raise ShopNotFoundError

    return int(result[0][0])


def set_shop_status(shop_id, status, cursor, cnx):
    """
    Update the status of a shop
    :param shop_id: the id of the shop we want to change the status of
    :param status: the status we want to change to
    :param cursor: cursor object for executing update
    :param cnx: connection object for committing changes
    :return: void
    """
    cursor.execute('update shop '
                   'set status = %s '
                   'where shop_id = %s', (status, shop_id))
    cnx.commit() # commit changes to shop table


def get_shop_sign(shop_id, cursor):
    """
    Gets the sign id of the shop
    :param shop_id: the id of the shop we want to check the open status for
    :param cursor: cursor object for executing search query
    :return: Raise ShopNotFoundError if the shop doesn't exit, sign id if successful
    """
    cursor.execute('select sign_id from shop where shop_id = %s', (shop_id,))
    result = cursor.fetchall()

    if len(result) == 0:  # user not in shop
        raise ShopNotFoundError

    return int(result[0][0])


def set_shop_sign(shop_id, sign_id, cursor, cnx):
    """
    Update the sign id of a shop
    :param shop_id: the id of the shop we want to change the status of
    :param sign_id: the sign id we want to set for the shop
    :param cursor: cursor object for executing update
    :param cnx: connection object for committing changes
    :return: void
    """
    cursor.execute('update shop '
                   'set sign_id = %s '
                   'where shop_id = %s', (sign_id, shop_id))
    cnx.commit() # commit changes to shop table


def create_user_control_panel(user_id, control_channel_id, cursor, cnx):
    """
    Creates a control panel for a user
    :param user_id: user id to create shop for
    :param control_channel_id: channel id of control panel channel
    :param cursor: cursor object for executing insert query
    :param cnx: connection object for committing changes
    :return: raise ExistingControlPanel if a control panel already exists, void if successful
    """
    try:
        get_user_control_panel(user_id, cursor)
    except ControlPanelNotFoundError:
        cursor.execute('insert into shop_control '
                       'values (%s, %s)',
                       (control_channel_id, user_id))
        cnx.commit()    # commit changes to database
        return

    raise ExistingControlPanelError


def create_user_shop(user_id, shop_channel_id, name, desc, status, shop_sign_id, cursor, cnx):
    """
    Creates a shop for a user
    :param user_id: user id to create shop for
    :param shop_channel_id: channel id of shop channel
    :param name: name of shop
    :param desc: desc of shop
    :param status: default status of shop
    :param shop_sign_id: id of the shop's sign
    :param cursor: cursor object for executing insert query
    :param cnx: connection object for committing changes
    :return:raise ExistingControlPanel if a control panel already exists, void if successful
    """
    try:
        get_user_shop(user_id, cursor)
    except ShopNotFoundError:
        cursor.execute('insert into shop '
                       'values (%s, %s, %s, %s, %s, %s)',
                       (shop_channel_id, user_id, name, desc, status, shop_sign_id))
        cnx.commit()  # commit changes to database
        return

    raise ExistingShopError


def delete_user_control_panel(user_id, cursor, cnx):
    """
    Deletes a control panel for a user
    :param user_id: user id to delete control panel for
    :param cursor: cursor object for executing deletion query
    :param cnx: connection object for committing changes
    :return:
    """
    try:
        shop_category_id = get_user_control_panel(user_id, cursor)
        cursor.execute('delete from shop_control where shop_category_id = %s', (shop_category_id,))  # execute deletion query
        cnx.commit()  # commit changes to database
    except ControlPanelNotFoundError:
        raise ControlPanelNotFoundError


def delete_user_shop(user_id, cursor, cnx):
    """
    Deletes a control panel for a user
    :param user_id: user id to delete control panel for
    :param cursor: cursor object for executing deletion query
    :param cnx: connection object for committing changes
    :return:
    """
    try:
        shop_id = get_user_shop(user_id, cursor)
        cursor.execute('delete from shop where shop_id = %s', (shop_id,))  # execute deletion query
        cnx.commit()  # commit changes to database

        delete_all_shop_items(shop_id, cursor, cnx)     # Delete all items that belonged to shop
    except ShopNotFoundError:
        raise ShopNotFoundError


def get_shop_item(item_id, shop_id, cursor):
    cursor.execute('select * from item where item_id = %s and shop_id = %s', (item_id, shop_id))
    result = cursor.fetchall()

    if len(result) == 0:  # item not in shop
        raise ItemNotFoundError

    return result[0]


def add_shop_item(item_id, shop_id, item_name, item_desc, item_price, item_qty, item_type, item_image, cursor, cnx):
    """
    Adds an item to a shop
    :param item_id: id of the item to be added
    :param shop_id: id of the shop to add the item to
    :param item_name: name of the item
    :param item_desc: description of the item
    :param item_price: price of the item
    :param item_qty: quantity of the item
    :param item_type: type of the item
    :param item_image: image of the item
    :param cursor: cursor object for executing adding query
    :param cnx: connection object for committing changes
    :return: void
    """
    cursor.execute('insert into item '
                   'values (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
                   (item_id, shop_id, item_name, item_desc, item_price, item_qty, item_type, item_image))
    cnx.commit()  # commit changes to database


def delete_all_shop_items(shop_id, cursor, cnx):
    """
    Deletes all items from a shop
    :param shop_id: id of the shop to delete items from
    :param cursor: cursor object for executing adding query
    :param cnx: connection object for committing changes
    :return: void
    """
    cursor.execute('delete from item where shop_id = %s', (shop_id,))  # execute deletion query
    cnx.commit()  # commit changes to database


def delete_shop_item(item_id, shop_id, cursor, cnx):
    """

    :param item_id: id of the item to be deleted
    :param shop_id: id of the shop the item belongs to
    :param cursor: cursor object for executing deletion query
    :param cnx: connection object for committing changes
    :return: void
    """
    cursor.execute('delete from item where item_id = %s and shop_id = %s', (item_id, shop_id))
    cnx.commit()


def set_shop_item_name(item_id, shop_id, item_name, cursor, cnx):
    cursor.execute('update item '
                   'set name = %s '
                   'where item_id = %s and shop_id = %s', (item_name, item_id, shop_id))
    cnx.commit()  # commit changes to shop table


def set_shop_item_desc(item_id, shop_id, item_desc, cursor, cnx):
    cursor.execute('update item '
                   'set desc = %s '
                   'where item_id = %s and shop_id = %s', (item_desc, item_id, shop_id))
    cnx.commit()  # commit changes to shop table


def set_shop_item_price(item_id, shop_id, item_price, cursor, cnx):
    cursor.execute('update item '
                   'set price = %s '
                   'where item_id = %s and shop_id = %s', (item_price, item_id, shop_id))
    cnx.commit()  # commit changes to shop table


def set_shop_item_qty(item_id, shop_id, item_qty, cursor, cnx):
    cursor.execute('update item '
                   'set qty = %s '
                   'where item_id = %s and shop_id = %s', (item_qty, item_id, shop_id))
    cnx.commit()  # commit changes to shop table


def set_shop_item_type(item_id, shop_id, item_type, cursor, cnx):
    cursor.execute('update item '
                   'set type = %s '
                   'where item_id = %s and shop_id = %s', (item_type, item_id, shop_id))
    cnx.commit()  # commit changes to shop table


def set_shop_item_image(item_id, shop_id, item_image, cursor, cnx):
    cursor.execute('update item '
                   'set image = %s '
                   'where item_id = %s and shop_id = %s', (item_image, item_id, shop_id))
    cnx.commit()  # commit changes to shop table


def get_id_from_name(display_name, cursor):
    """
    Gets a user id from display name of a user
    :param display_name: display name of user whose id will be gotten
    :param cursor: cursor object for executing search query
    :return: Raise UserNotFoundError if user does not exist, user_id if user is found
    """
    cursor.execute('select user_id from user where display_name = %s', (display_name,))
    result = cursor.fetchall()

    if len(result) == 0:  # user not found
        raise UserNotFoundError

    return result[0][0]  # return user id


def get_name_from_id(user_id, cursor):
    """
    Gets a user id from display name of a user
    :param user_id: id of user whose display name will be gotten
    :param cursor: cursor object for executing search query
    :return: Raise InvalidUserIDError, display_name if user is found
    """
    cursor.execute('select name from user where user_id = %s', (user_id,))
    result = cursor.fetchall()

    if len(result) == 0:  # user not found
        raise InvalidUserIDError

    return result[0][0]  # return display name


def check_user_exists(user_id, cursor):
    """
    Checks if a given user_id exists in the database
    :param user_id: the event id to be checked
    :param cursor: cursor object for executing query
    :return: -1 if event does not exist, 1 if event exists
    """
    cursor.execute('select * from user where user_id = %s', (user_id,))
    result = cursor.fetchall()
    if len(result) == 0:  # user not found
        return -1
    return 1


# ERRORS #


class Error(Exception):
    """Base class for exceptions in this module."""


class AdminPermissionError(Error):
    """Invalid permission to modify database."""

    def __init__(self, user_id):
        self.user_id = user_id


class CommandNotControlPanelError(Error):
    """Occurs if a user tries to run a command that is intended for their shop control panel
    and they are not currently executing from that channel"""


class ExistingControlPanelError(Error):
    """Occurs if a user already has a control panel"""


class ExistingShopError(Error):
    """Occurs if a user already has a shop"""


class ControlPanelNotFoundError(Error):
    """Occurs when a user doesn't have a control panel"""


class ShopNotFoundError(Error):
    """Occurs when a user doesn't have a shop"""


class ItemNotFoundError(Error):
    """Occurs when an item is not found in a shop"""


class UserNotFoundError(Error):
    """No user was found with the given name"""


class InvalidUserIDError(Error):
    """A queried user ID is invalid"""