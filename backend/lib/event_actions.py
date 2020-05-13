from discord.ext import commands

from backend.lib.helper_commands import ShopNotFoundError, get_shop, set_shop_sign, get_shop_sign
from backend.lib.shop_queries import create_shop_sign
from backend.lib.user_queries import sql_add_user, sql_delete_user


class EventActions(commands.Cog):
    def __init__(self, bot, cursor, cnx):
        self.bot = bot
        self.cursor = cursor
        self.cnx = cnx

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await member.send("Welcome to Affiliates Only!\n\nIf you wish to invite others our permanent invite link is https://discord.gg/vw8AN3j ")
        sql_add_user(member.id, member.name + "#" + member.discriminator, "", "false", 0, member.joined_at,
                     self.cursor, self.cnx)

    @commands.Cog.listener()
    async def on_member_leave(self, member):
        sql_delete_user(member.id, self.cursor, self.cnx)

    @commands.Cog.listener()
    async def on_message(self, message):
        try:
            shop_id = message.channel.id
            shop_results = get_shop(shop_id, self.cursor)

            formatted_status = "open" if int(shop_results[4]) == 1 else "closed"
            check = "**This shop is currently " + formatted_status + "!**"

            if check not in message.content:
                new_sign = await message.channel.send(create_shop_sign(self.bot.get_user(int(shop_results[1])), shop_results, self.cursor))

                old_msg = await message.channel.fetch_message(get_shop_sign(shop_id, self.cursor))

                set_shop_sign(shop_id, new_sign.id, self.cursor, self.cnx)
                await old_msg.delete()

        except ShopNotFoundError:
            pass    # do nothing