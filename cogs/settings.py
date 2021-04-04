import discord
from discord.ext import commands
import sqlite3
from sqlite3 import Error
import datetime


def execute_query(filename, query):
    connection = sqlite3.connect(filename)
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
        print(f"{datetime.datetime.now()}: Executed write query to {filename} successfully")
    except Error as e:
        raise Exception(e)


def read_query(filename, query):
    connection = sqlite3.connect(filename)
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        print(f"{datetime.datetime.now()}: Read from database in {filename} successfully")
        return result
    except Error as e:
        raise Exception(e)


def check(ctx, level):
    # 10: bot admin
    # 9: eclipse leaders
    # 8: eclipse bankaccess
    # 7: all highgov
    # 6: all lowgov
    # 5: 
    # 4: 
    # 3: 
    # 2: all members
    # 1: basic
    roles = [role.id for role in ctx.author.roles]
    query = f"SELECT role_id FROM permissions WHERE permission_level >= {level}"
    allowed_roles = [entry[0] for entry in read_query('databases/permissions.sqlite', query)]
    for role in roles:
        if role in allowed_roles:
            return True
    return False
    



class Settings(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.command()
    async def permissions(self, ctx, action, role_id, permission_level=0):
        # level 10 command
        if not check(ctx, 10):
            raise Exception("Missing permissions")
            return
        try:
            role_id = int(role_id)
            permission_level = int(permission_level)
        except:
            raise ValueError("Invalid input")
        if permission_level > 10 or (permission_level < 0 and not action == "get"):
            raise ValueError("Invalid input for permission_level")
        if action not in ['set', 'update', 'remove', 'get']:
            raise ValueError("Invalid action")
        for server in self.bot.guilds:
            try:
                role = server.get_role(role_id)
            except:
                pass
        if role:
            await ctx.send(f"Role name: {role}")
        else:
            await ctx.send("Role name not found")

        if action == "set":
            query = f"""
                INSERT INTO permissions (role_id, permission_level)
                VALUES ({role_id}, {permission_level});
            """
            try:
                execute_query('databases/permissions.sqlite', query)
            except Exception as e:
                if "UNIQUE" in str(e):
                    await ctx.send("Use `updatepermission` instead")
                    return
            await ctx.send(f"Set {role_id} permission level to {permission_level}")
        elif action == "update":
            query = f"""
                UPDATE permissions
                SET permission_level = {permission_level}
                WHERE role_id = {role_id};
            """
            execute_query('databases/permissions.sqlite', query)
            await ctx.send(f"Updated {role_id} permission level to {permission_level}")
        elif action == "remove":
            query = f"""
                DELETE FROM permissions
                WHERE role_id = {role_id};
            """
            execute_query('databases/permissions.sqlite', query)
            await ctx.send(f"Removed permissions entry for {role_id}")
        elif action == "get":
            query = f"SELECT * FROM permissions WHERE role_id = {role_id}"
            result = read_query('databases/permissions.sqlite', query)
            try:
                entry = result[0]
            except IndexError:
                await ctx.send(f"Permissions entry for {role_id} not found")
                return
            await ctx.send(f"Role {entry[0]} has a permission level of {entry[1]}")

    @permissions.error
    async def permissions_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}permissions <action> <role_id> [permission_level]`")


    @commands.command()
    async def testcheck(self, ctx, level):
        # level 0
        try:
            level = int(level)
        except:
            raise ValueError("Invalid input")
        await ctx.send(check(ctx, level))

    @testcheck.error
    async def testcheck_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}testcheck <level>`")


def setup(bot):
    bot.add_cog(Settings(bot))