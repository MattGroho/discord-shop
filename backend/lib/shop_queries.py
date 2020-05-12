import discord
from discord.ext import commands
from discord.utils import get
from backend.lib.helper_commands import check_admin_status, AdminPermissionError, check_user_exists, in_control_panel, \
    CommandNotControlPanelError, get_user_shop, get_shop_status, set_shop_status, add_shop_item, ItemNotFoundError, \
    get_shop_item, set_shop_item_name, set_shop_item_desc, set_shop_item_price, set_shop_item_qty, set_shop_item_type, \
    set_shop_item_image, delete_shop_item


class ShopQueries(commands.Cog):
    def __init__(self, bot, cursor, cnx, shop_category_id, control_category_id):
        self.bot = bot
        self.cursor = cursor
        self.cnx = cnx
        self.shop_category_id = shop_category_id
        self.control_category_id = control_category_id

    @commands.command()
    async def shop(self, ctx, status):
        """
        Set the status of the shop to open / close
        :param status: the status of the shop (open / close)
        """
        user = ctx.author

        try:
            in_control_panel(user.id, ctx.message.channel.id, self.cursor)
        except CommandNotControlPanelError:
            return  # do nothing in current channel

        status = status.lower()

        if not (status == 'open' or status == 'close'):  # check for valid response
            await ctx.send("Error: Must provide a valid status for your shop! (eg. open / close)")
            return

        status = 0 if status == 'close' else 1
        shop_id = get_user_shop(user.id, self.cursor)

        cur_status = get_shop_status(shop_id, self.cursor)

        if status == cur_status:
            await ctx.send("Error: The shop is already " + ('open' if cur_status == 1 else 'closed') + " for business!")
            return

        guild = ctx.guild
        shop_channel = self.bot.get_channel(shop_id)    # TODO Update message inside shop to reflect status

        if status == 1:    # if the user is opening their shop
            await shop_channel.set_permissions(guild.default_role, read_messages=True)
            await ctx.send("You have successfully opened up shop!")
        else:   # if the user is closing their shop
            await shop_channel.set_permissions(guild.default_role, read_messages=False)
            await ctx.send("You have successfully closed down shop!")

        set_shop_status(shop_id, status, self.cursor, self.cnx)

    @commands.command()
    async def add_item(self, ctx, item_name, item_price, item_qty, item_type, item_image, item_desc):
        """
        Add an item to the shop
        :param item_name: name of the item
        :param item_price: price of the item (0.00)
        :param item_qty: available quantity for the item (negative value for INF)
        :param item_type: type of the item (digital / service)
        :param item_image: image url of the item (less than 64 characters)
        :param item_desc: description of the item (less than 256 characters)
        """
        user = ctx.author

        try:
            in_control_panel(user.id, ctx.message.channel.id, self.cursor)
        except CommandNotControlPanelError:
            return  # do nothing in current channel

        if not isinstance(item_name, str):
            await ctx.send("Error: The item name must have a valid name! (Use quotes to include spaces)")
            return

        try:
            item_price = float(item_price)
        except ValueError:
            await ctx.send("Error: The item price must have a valid price! (eg. 00.00)")
            return

        try:
            item_qty = int(item_qty)
        except ValueError:
            await ctx.send("Error: The item quantity must have a valid amount! (eg. 1)")
            return

        if not isinstance(item_type, str):
            await ctx.send("Error: The item type must have a valid type! (eg. digital / service)")
            return

        item_type = item_type.upper()

        if not (item_type == 'DIGITAL' or item_type == 'SERVICE'):
            await ctx.send("Error: The item type must have a valid type! (eg. digital / service)")
            return

        if not isinstance(item_desc, str):
            await ctx.send("Error: The item description must have a valid description text!")
            return

        if len(item_desc) >= 512:
            await ctx.send("Error: The item description must be less than 512 characters long!")
            return

        if len(item_image) >= 64:
            await ctx.send("Error: The item image must be less than 64 characters long!")
            return

        if item_image.lower() == 'none':
            item_image = item_image.lower()

        shop_id = get_user_shop(user.id, self.cursor)
        shop_channel = self.bot.get_channel(shop_id)

        embed = create_item_embed(item_name, item_desc, item_price, item_qty, item_type, item_image)   # Create item embed
        msg = await shop_channel.send(embed=embed)
        add_shop_item(msg.id, shop_id, item_name, item_desc, item_price , item_qty, item_type, item_image, self.cursor, self.cnx)

        await ctx.send("You have successfully added a new item to your shop!")

    @commands.command()
    async def delete_item(self, ctx, item_id):
        """
        Delete an item from the shop
        :param item_id: id of the item to delete
        """
        user = ctx.author

        try:
            in_control_panel(user.id, ctx.message.channel.id, self.cursor)
        except CommandNotControlPanelError:
            return  # do nothing in current channel

        shop_id = get_user_shop(user.id, self.cursor)
        shop_channel = self.bot.get_channel(shop_id)

        try:
            item_results = get_shop_item(item_id, shop_id, self.cursor)
            item_msg = await shop_channel.fetch_message(item_id)

            await item_msg.delete()

            delete_shop_item(item_id, shop_id, self.cursor, self.cnx)
            await ctx.send("Successfully deleted item " + item_results[2] + "!")
        except ItemNotFoundError:
            await ctx.send("Error: The item id was not found! Be sure to copy the correct id of your shop item message.")
            return

    @commands.command()
    async def set_item_name(self, ctx, item_id, item_name):
        """
        Sets an items name
        :param item_id: id for the item to update
        :param item_name: name of the item to update
        """
        user = ctx.author

        try:
            in_control_panel(user.id, ctx.message.channel.id, self.cursor)
        except CommandNotControlPanelError:
            return  # do nothing in current channel

        if not isinstance(item_name, str):
            await ctx.send("Error: The item name must have a valid name! (Use quotes to include spaces)")
            return

        shop_id = get_user_shop(user.id, self.cursor)
        shop_channel = self.bot.get_channel(shop_id)

        try:
            item_msg = await shop_channel.fetch_message(item_id)

            item_results = get_shop_item(item_id, shop_id, self.cursor)
            embed = create_item_embed(item_name, item_results[3], item_results[4],
                                      item_results[5], item_results[6], item_results[7])

            set_shop_item_name(item_id, shop_id, item_name, self.cursor, self.cnx)
            await item_msg.edit(embed=embed)
        except ItemNotFoundError:
            await ctx.send("Error: The item id was not found! Be sure to copy the correct id of your shop item message.")
            return

        await ctx.send("Successfully updated the item name from " + item_results[2] + " to " + item_name + "!")

    @commands.command()
    async def set_item_desc(self, ctx, item_id, item_desc):
        """
        Sets an items description
        :param item_id: id for the item to update
        :param item_desc: description of the item to update
        """
        user = ctx.author

        try:
            in_control_panel(user.id, ctx.message.channel.id, self.cursor)
        except CommandNotControlPanelError:
            return  # do nothing in current channel

        if not isinstance(item_desc, str):
            await ctx.send("Error: The item description must have a valid description text!")
            return

        if len(item_desc) >= 512:
            await ctx.send("Error: The item description must be less than 512 characters long!")
            return

        shop_id = get_user_shop(user.id, self.cursor)
        shop_channel = self.bot.get_channel(shop_id)

        item_msg = await shop_channel.fetch_message(item_id)

        try:
            item_results = get_shop_item(item_id, shop_id, self.cursor)
            embed = create_item_embed(item_results[2], item_desc, item_results[4],
                                      item_results[5], item_results[6], item_results[7])

            set_shop_item_desc(item_id, shop_id, item_desc, self.cursor, self.cnx)
            await item_msg.edit(embed=embed)
        except ItemNotFoundError:
            await ctx.send(
                "Error: The item id was not found! Be sure to copy the correct id of your shop item message.")
            return

        await ctx.send("Successfully updated the item description for " + item_results[2] + " to " + item_desc + "!")

    @commands.command()
    async def set_item_price(self, ctx, item_id, item_price):
        """
        Sets an items price
        :param item_id: id for the item to update
        :param item_price: price of the item to update
        """
        user = ctx.author

        try:
            in_control_panel(user.id, ctx.message.channel.id, self.cursor)
        except CommandNotControlPanelError:
            return  # do nothing in current channel

        try:
            item_price = float(item_price)
        except ValueError:
            await ctx.send("Error: The item price must have a valid price! (eg. 00.00)")
            return

        shop_id = get_user_shop(user.id, self.cursor)
        shop_channel = self.bot.get_channel(shop_id)

        item_msg = await shop_channel.fetch_message(item_id)

        try:
            item_results = get_shop_item(item_id, shop_id, self.cursor)
            embed = create_item_embed(item_results[2], item_results[3], item_price,
                                      item_results[5], item_results[6], item_results[7])

            set_shop_item_price(item_id, shop_id, item_price, self.cursor, self.cnx)
            await item_msg.edit(embed=embed)
        except ItemNotFoundError:
            await ctx.send(
                "Error: The item id was not found! Be sure to copy the correct id of your shop item message.")
            return

        formatted_price = "${:,.2f}".format(item_price)

        await ctx.send("Successfully updated the item price for " + item_results[2] + " to " + formatted_price + "!")

    @commands.command()
    async def set_item_quantity(self, ctx, item_id, item_qty):
        """
        Sets an items available quantity
        :param item_id: id for the item to update
        :param item_qty: available quantity of item to update
        """
        user = ctx.author

        try:
            in_control_panel(user.id, ctx.message.channel.id, self.cursor)
        except CommandNotControlPanelError:
            return  # do nothing in current channel

        try:
            item_qty = int(item_qty)
        except ValueError:
            await ctx.send("Error: The item quantity must have a valid amount! (eg. 1)")
            return

        shop_id = get_user_shop(user.id, self.cursor)
        shop_channel = self.bot.get_channel(shop_id)

        item_msg = await shop_channel.fetch_message(item_id)

        try:
            item_results = get_shop_item(item_id, shop_id, self.cursor)
            embed = create_item_embed(item_results[2], item_results[3], item_results[4],
                                      item_qty, item_results[6], item_results[7])

            set_shop_item_qty(item_id, shop_id, item_qty, self.cursor, self.cnx)
            await item_msg.edit(embed=embed)
        except ItemNotFoundError:
            await ctx.send(
                "Error: The item id was not found! Be sure to copy the correct id of your shop item message.")
            return

        formatted_qty = "INF" if item_qty < 0 else str(item_qty)

        await ctx.send("Successfully updated the item quantity for " + item_results[2] + " to " + formatted_qty + "!")

    @commands.command()
    async def set_item_type(self, ctx, item_id, item_type):
        """
        Sets an items type
        :param item_id: id for the item to update
        :param item_type: type of item to update (digital / service)
        """
        user = ctx.author

        try:
            in_control_panel(user.id, ctx.message.channel.id, self.cursor)
        except CommandNotControlPanelError:
            return  # do nothing in current channel

        item_type = item_type.upper()

        if not (item_type == 'DIGITAL' or item_type == 'SERVICE'):
            await ctx.send("Error: The item type must have a valid type! (eg. digital / service)")
            return

        shop_id = get_user_shop(user.id, self.cursor)
        shop_channel = self.bot.get_channel(shop_id)

        item_msg = await shop_channel.fetch_message(item_id)

        try:
            item_results = get_shop_item(item_id, shop_id, self.cursor)
            embed = create_item_embed(item_results[2], item_results[3], item_results[4],
                                      item_results[5], item_type, item_results[7])

            set_shop_item_type(item_id, shop_id, item_type, self.cursor, self.cnx)
            await item_msg.edit(embed=embed)
        except ItemNotFoundError:
            await ctx.send(
                "Error: The item id was not found! Be sure to copy the correct id of your shop item message.")
            return

        await ctx.send("Successfully updated the item type for " + item_results[2] + " to " + item_type + "!")

    @commands.command()
    async def set_item_image(self, ctx, item_id, item_image):
        """
        Sets an items image
        :param item_id: id for the item to update
        :param item_image: image url to update
        """
        user = ctx.author

        try:
            in_control_panel(user.id, ctx.message.channel.id, self.cursor)
        except CommandNotControlPanelError:
            return  # do nothing in current channel

        if len(item_image) >= 64:
            await ctx.send("Error: The item image must be less than 64 characters long!")
            return

        if item_image.lower() == 'none':
            item_image = item_image.lower()

        shop_id = get_user_shop(user.id, self.cursor)
        shop_channel = self.bot.get_channel(shop_id)

        item_msg = await shop_channel.fetch_message(item_id)

        try:
            item_results = get_shop_item(item_id, shop_id, self.cursor)
            embed = create_item_embed(item_results[2], item_results[3], item_results[4],
                                      item_results[5], item_results[6], item_image)

            set_shop_item_image(item_id, shop_id, item_image, self.cursor, self.cnx)
            await item_msg.edit(embed=embed)
        except ItemNotFoundError:
            await ctx.send(
                "Error: The item id was not found! Be sure to copy the correct id of your shop item message.")
            return

        await ctx.send("Successfully updated the item image for " + item_results[2] + " to " + item_image + "!")


def create_item_embed(item_name, item_desc, item_price, item_qty, item_type, item_image):
    """
    Creates a formatted embed message of an item
    :param item_name: name of the item
    :param item_price: price of the item
    :param item_qty: available quantity of the item
    :param item_type: type of the item
    :param item_image: image of the item
    :param item_desc: description of the item
    :return: embed for Discord
    """
    formatted_price = "${:,.2f}".format(item_price)
    formatted_qty = "INF" if int(item_qty) < 0 else str(item_qty)

    embed = discord.Embed(title="__                                                          __\n" +
                                "Item: " + item_name + "\n" +
                                "Type: " + item_type + "\n" +
                                "Price: " + formatted_price + "\n" +
                                "Qty Avl: " + formatted_qty + "\n" +
                                "__                                                          __\n",
                          description="`" + item_desc + "`", color=0x68ff7a)
    if item_image != "none":
        embed.set_image(url=item_image)
    embed.add_field(name="__Purchase Info__", value="Contact me via Discord for further information on the item listed.", inline=True)
    embed.add_field(name="__Middleman Info__", value="A trusted middleman can be used for extra buyers protection.", inline=True)

    return embed


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
