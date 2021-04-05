import discord
from discord.ext import commands
import json
import sys
import os
sys.path.append('..')
import helpers




class Settings(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.command()
    async def permissions(self, ctx, action, role_id, permission_level=0):
        # level 10 command
        helpers.check(ctx, 10)
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
                helpers.execute_query('databases/permissions.sqlite', query)
            except Exception as e:
                if "UNIQUE" in str(e):
                    await ctx.send(f"Use `{self.bot.command_prefix}permissions update` instead")
                    return
            await ctx.send(f"Set {role_id} permission level to {permission_level}")
        elif action == "update":
            query = f"""
                UPDATE permissions
                SET permission_level = {permission_level}
                WHERE role_id = {role_id};
            """
            helpers.execute_query('databases/permissions.sqlite', query)
            await ctx.send(f"Updated {role_id} permission level to {permission_level}")
        elif action == "remove":
            query = f"""
                DELETE FROM permissions
                WHERE role_id = {role_id};
            """
            helpers.execute_query('databases/permissions.sqlite', query)
            await ctx.send(f"Removed permissions entry for {role_id}")
        elif action == "get":
            query = f"SELECT * FROM permissions WHERE role_id = {role_id}"
            result = helpers.read_query('databases/permissions.sqlite', query)
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


    @commands.command()
    async def updateapikey(self, ctx, owner="all"):
        helpers.check(ctx, 10)
        if owner == "all":
            apikeys = helpers.get_data()['apikeys']
            owners = apikeys.keys()
            for owner in owners:
                helpers.update_apikey(owner)
            await ctx.send("Updated API keys")
        else:
            helpers.update_apikey(owner)
            await ctx.send(f"Updated API key for {owner}")
    
    @updateapikey.error
    async def updateapikey_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}updateapikey [owner]`")




def setup(bot):
    bot.add_cog(Settings(bot))