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
    roles = [role.id for role in ctx.author.roles]
    query = f"SELECT role_id FROM permissions WHERE permission_level >= {level}"
    allowed_roles = [entry[0] for entry in read_query('databases/permissions.sqlite', query)]
    for role in roles:
        if role in allowed_roles:
            return True
    return False
    


def set_permission(role_id, permission_level):
    query = f"""
    INSERT INTO permissions (role_id, permission_level)
    VALUES ({role_id}, {permission_level});
    """
    execute_query('databases/permissions.sqlite', query)

    

class Settings(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.command()
    async def setpermission(self, ctx, role_id, permission_level):
        try:
            role_id = int(role_id)
            permission_level = int(permission_level)
            if permission_level > 10 or permission_level < 1:
                raise ValueError("Invalid input")
        except:
            raise ValueError("Invalid input")
        set_permission(role_id, permission_level)
        await ctx.send(f"Set {role_id} permission level to {permission_level}")

    @setpermission.error
    async def setpermission_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}setpermission <role_id> <permission_level>`")

    
    @commands.command()
    async def getpermission(self, ctx, role_id):
        try:
            role_id = int(role_id)
        except:
            raise ValueError("Invalid input")
        query = f"SELECT * FROM permissions WHERE role_id = {role_id}"
        result = read_query('databases/permissions.sqlite', query)
        entry = result[0]
        await ctx.send(f"Role {entry[0]} has a permission level of {entry[1]}")

    @getpermission.error
    async def getpermission_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}getpermission <role_id>`")


    @commands.command()
    async def testcheck(self, ctx, level):
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