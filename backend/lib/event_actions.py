from discord.ext import commands
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
