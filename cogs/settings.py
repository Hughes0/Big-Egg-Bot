import discord
from discord.ext import commands
import json
import requests
import sys
import os
sys.path.append('..')
import helpers

def get_role_name(bot, role_id):
    try:
        role_id = int(role_id)
    except:
        raise Exception("Invalid role id for get_role_name()")
    for server in bot.guilds:
        try:
            role = server.get_role(role_id)
        except:
            pass
        if role:
            return role
        else:
            return None

is_valid_permission_level = lambda permission_level: 0 <= int(permission_level) <= 10


class Settings(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.group(pass_context=True)
    async def permissions(self, ctx):
        # level 10 command
        helpers.check(ctx, 10)
        # case no action selected
        if ctx.invoked_subcommand is None:
            raise Exception("Invalid action")

    @permissions.command(pass_context=True)
    async def get(self, ctx, role_id):
        # get the permissions of a role by id (or all roles)
        if role_id != "all":
            await ctx.send(f"Role name: {get_role_name(self.bot, role_id)}")
        if role_id == "all":
            # send all permissions
            query = "SELECT * FROM permissions"
            results = helpers.read_query('databases/permissions.sqlite', query)
            for result in results:
                await ctx.send(result)
        else:
            # send permissions for selected role
            query = f"SELECT * FROM permissions WHERE role_id = {role_id}"
            result = helpers.read_query('databases/permissions.sqlite', query)
            try:
                entry = result[0]
            except IndexError:
                await ctx.send(f"Permissions entry for {role_id} not found")
                return
            await ctx.send(f"Role {entry[0]} has a permission level of {entry[1]}")
    
    @permissions.command(pass_context=True)
    async def set(self, ctx, role_id, permission_level):
        # option to create new permission entry (not update existing)
        await ctx.send(f"Role name: {get_role_name(self.bot, role_id)}")
        if not is_valid_permission_level(permission_level):
            raise Exception("Invalid permission level")
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

    @permissions.command(pass_context=True)
    async def update(self, ctx, role_id, permission_level):
        # update an existing permission entry for a selected role
        await ctx.send(f"Role name: {get_role_name(self.bot, role_id)}")
        if not is_valid_permission_level(permission_level):
            raise Exception("Invalid permission level")
        query = f"""
            UPDATE permissions
            SET permission_level = {permission_level}
            WHERE role_id = {role_id};
        """
        helpers.execute_query('databases/permissions.sqlite', query)
        await ctx.send(f"Updated {role_id} permission level to {permission_level}")

    @permissions.command(pass_context=True)
    async def remove(self, ctx, role_id):
        # remove a role's permission entry
        await ctx.send(f"Role name: {get_role_name(self.bot, role_id)}")
        query = f"""
            DELETE FROM permissions
            WHERE role_id = {role_id};
        """
        helpers.execute_query('databases/permissions.sqlite', query)
        await ctx.send(f"Removed permissions entry for {role_id}")

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
        await ctx.send(helpers.check(ctx, level))

    @testcheck.error
    async def testcheck_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}testcheck <level>`")


    @commands.group(pass_context=True)
    async def apikey(self, ctx):
        # level 10 command
        helpers.check(ctx, 10)
        # case no action selected
        if ctx.invoked_subcommand is None:
            raise Exception("Invalid action")

    @apikey.command(pass_context=True)
    async def setkey(self, ctx, owner, key):
        # add api key entry
        if not owner or not key:
            raise Exception(f"Missing arguments, correct syntax is `{self.bot.command_prefix}apikey set <owner> <key>`")
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

    @apikey.command(pass_context=True)
    async def getkey(self, ctx, owner):
        # get api key entry
        if not owner:
            raise Exception(f"Missing arguments, correct syntax is `{self.bot.command_prefix}apikey get <owner>`")
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

    @apikey.command(pass_context=True)
    async def updatekey(self, ctx, owner):
        # update apikey data (allianceposition, requests remaining)
        if not owner:
            raise Exception(f"Missing arguments, correct syntax is `{self.bot.command_prefix}apikey update <owner>`")
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
                url = f"https://politicsandwar.com/api/v2/nations/{keys[i]}/&alliance_id=7450&alliance_position=5&v_mode=false"
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
            url = f"https://politicsandwar.com/api/v2/nations/{key}/&alliance_id=7450&alliance_position=5&v_mode=false"
            data = requests.get(url).json()
            helpers.catch_api_error(data, 2)
            data = data['api_request']['api_key_details']
            arguments = (data['alliance_id'], data['alliance_position'], data['daily_requests_remaining'], owner)
            helpers.execute_query('databases/keys.sqlite', query, arguments)
            await ctx.send(f"Updated `{owner}` API key entry")
    
    @apikey.command(pass_context=True)
    async def removekey(self, ctx, owner):
        # remove api key entry
        query = """
            DELETE FROM keys
            WHERE owner = ?;
        """
        helpers.execute_query('databases/keys.sqlite', query, (owner,))
        await ctx.send(f"Removed API key entry for `{owner}`")


    @apikey.error
    async def apikey_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}apikey <action>`")

    
    @commands.command()
    async def addproject(self, ctx, name, description, image_url, *cost):
        # level 10 command
        helpers.check(ctx, 10)
        try:
            cost = helpers.get_arguments(cost)
        except:
            raise ValueError("Invalid cost input")
        query = """
            INSERT INTO projects
                (name, description, image_url, cost)
            VALUES
                (?, ?, ?, ?);
        """
        arguments = (name, description, image_url, json.dumps(cost))
        helpers.execute_query('databases/game_data.sqlite', query, arguments)
        await ctx.send("Added project data to database")

    @addproject.error
    async def addproject_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}addproject <name> <description> <image_url> <*cost>`")
        




def setup(bot):
    bot.add_cog(Settings(bot))