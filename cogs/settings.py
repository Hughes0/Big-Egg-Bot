import discord
from discord.ext import commands
import json
import requests
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
        # helpers.check(ctx, 10)
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
        else:
            raise ValueError("Invalid action")

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
    async def apikey(self, ctx, action, owner=None, key=None):
        # level 10 command
        helpers.check(ctx, 10)
        if not action:
            raise ValueError("Invalid action, options are `set`, `get`, `update`, and `remove`")
        if action == "set":
            if not owner or not key:
                raise ValueError(f"Missing arguments, correct syntax is `{self.bot.command_prefix}apikey set <owner> <key>`")
            owner = owner.lower()
            query = """
            INSERT INTO keys
                (key, owner, alliance_id, alliance_position, requests_remaining)
            VALUES
                (?, ?, ?, ?, ?);
            """
            url = f"https://politicsandwar.com/api/v2/nations/{key}/&alliance_id=7450&alliance_position=2,3,4,5&v_mode=false"
            data = requests.get(url).json()
            helpers.catch_api_error(data, 2)
            data = data['api_request']['api_key_details']
            arguments = (key, owner, data['alliance_id'], data['alliance_position'], data['daily_requests_remaining'])
            helpers.execute_query('databases/keys.sqlite', query, arguments)
            await ctx.send(f"Saved API key entry for `{owner}` to database")
        elif action == "get":
            if not owner:
                raise ValueError(f"Missing arguments, correct syntax is `{self.bot.command_prefix}apikey get <owner>`")
            if owner == "all":
                query = "SELECT * FROM keys"
                result = helpers.read_query('databases/keys.sqlite', query)
                await ctx.send(result)
            else:
                query = "SELECT * FROM keys WHERE owner = ?"
                result = helpers.read_query('databases/keys.sqlite', query, (owner,))
                if not result:
                    await ctx.send(f"No entry found for {owner}")
                else:
                    await ctx.send(result)
        elif action == "update":
            if not owner:
                raise ValueError(f"Missing arguments, correct syntax is `{self.bot.command_prefix}apikey update <owner>`")
            if owner == "all":
                query = "SELECT owner, key FROM keys"
                result = helpers.read_query('databases/keys.sqlite', query)
                if not result:
                    raise Exception("No API key entries found")
                owners = [entry[0] for entry in result]
                keys = [entry[1] for entry in result]
                for i in range(len(owners)):
                    query = """
                        UPDATE keys
                        SET alliance_id = ?,
                            alliance_position = ?,
                            requests_remaining = ?
                        WHERE owner = ?;
                    """
                    url = f"https://politicsandwar.com/api/v2/nations/{keys[i]}/&alliance_id=7450&alliance_position=2,3,4,5&v_mode=false"
                    data = requests.get(url).json()
                    helpers.catch_api_error(data, 2)
                    data = data['api_request']['api_key_details']
                    arguments = (data['alliance_id'], data['alliance_position'], data['daily_requests_remaining'], owners[i])
                    helpers.execute_query('databases/keys.sqlite', query, arguments)
                    await ctx.send(f"Updated `{owners[i]}` API key entry")
                await ctx.send("Updated all API key entries")
            else:
                query = "SELECT key FROM keys WHERE owner = ?"
                result = helpers.read_query('databases/keys.sqlite', query, (owner,))
                if not result:
                    raise Exception(f"API key entry for `{owner}` not found")
                key = result[0][0]
                query = """
                    UPDATE keys
                    SET alliance_id = ?,
                        alliance_position = ?,
                        requests_remaining = ?
                    WHERE owner = ?;
                """
                url = f"https://politicsandwar.com/api/v2/nations/{key}/&alliance_id=7450&alliance_position=2,3,4,5&v_mode=false"
                data = requests.get(url).json()
                helpers.catch_api_error(data, 2)
                data = data['api_request']['api_key_details']
                arguments = (data['alliance_id'], data['alliance_position'], data['daily_requests_remaining'], owner)
                helpers.execute_query('databases/keys.sqlite', query, arguments)
                await ctx.send(f"Updated `{owner}` API key entry")
        elif action == "remove":
            query = """
                DELETE FROM keys
                WHERE owner = ?;
            """
            helpers.execute_query('databases/keys.sqlite', query, (owner,))
            await ctx.send(f"Removed API key entry for `{owner}`")
        else:
            raise ValueError("Invalid action, options are `set`, `get`, `update`, and `remove`")




def setup(bot):
    bot.add_cog(Settings(bot))