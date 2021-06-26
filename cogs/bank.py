import discord
from discord.ext import commands
import requests
import json
import sys
sys.path.append('..')
import helpers


def account_amount(account_name):
    query = "SELECT * FROM accounts WHERE owner_name = ?"
    result = helpers.read_query('databases/accounts.sqlite', query, (account_name,))
    if not result:
        raise Exception("Account not found")
    account = list(result[0])
    resources = ["cash", "food", "coal", "oil", "uranium", "lead", "iron", "bauxite", "gasoline", "munitions", "steel", "aluminum"]
    account_amts = []
    for amt in account[3:]:
        if amt:
            account_amts.append(amt)
        else:
            account_amts.append(0)
    account_amts = {resources[i]:account_amts[i] for i in range(len(resources))}
    return account[:3], account_amts


def withdraw(sender_alliance_id, withdraw_type, recipient, *resources):
    resources_dict = helpers.rss_list_to_dict(resources)
    
    withdraw_url = f"https://politicsandwar.com/alliance/id={sender_alliance_id}&display=bank"
    withdraw_data = {
        "withmoney": resources_dict['cash'],
        "withfood": resources_dict['food'],
        "withcoal": resources_dict['coal'],
        "withoil": resources_dict['oil'],
        "withuranium": resources_dict['uranium'],
        "withlead": resources_dict['lead'],
        "withiron": resources_dict['iron'],
        "withbauxite": resources_dict['bauxite'],
        "withgasoline": resources_dict['gasoline'],
        "withmunitions": resources_dict['munitions'],
        "withsteel": resources_dict['steel'],
        "withaluminum": resources_dict['aluminum'],
        "withtype": withdraw_type.capitalize(),
        "withrecipient": recipient,
        "withnote": "",
        "withsubmit": "Withdraw"
    }
    with requests.Session() as s:
        helpers.login(s)
        s.post(url=withdraw_url,data=withdraw_data)
    return withdraw_data


def update_account(account_name, resources_dict):
    entries = ",\n".join([f"{resource} = ?" for resource in resources_dict])
    query = f"""
        UPDATE accounts
        SET {entries}
        WHERE owner_name = ?
    """
    arguments = [resources_dict[resource] for resource in resources_dict]
    arguments.append(account_name)
    helpers.execute_query('databases/accounts.sqlite', query, tuple(arguments))


class Bank(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    @commands.check(helpers.has_account)
    async def account(self, ctx):
        # case no action selected
        if ctx.invoked_subcommand is None:
            raise Exception("Invalid action")

    @account.command()
    @commands.check(helpers.perms_ten)
    async def get(self, ctx, account_name=None):
        if not account_name:
            query = "SELECT owner_discord_id, owner_name, owner_nation_id FROM accounts"
            result = helpers.read_query('databases/accounts.sqlite', query)
            for entry in result:
                await ctx.send(f"**{entry[1]}** (<@!{entry[0]}>) - https://politicsandwar.com/nation/id={entry[2]}")
            await ctx.send("All accounts displayed")
        else:
            bank = account_amount(account_name)
            await ctx.send(bank[0])
            text = ""
            for resource in bank[1]:
                text += f"{resource}: {bank[1][resource]}\n"
            await ctx.send(text)
    
    @account.command()
    async def me(self, ctx):
        query = "SELECT owner_name FROM accounts WHERE owner_discord_id = ?"
        result = helpers.read_query('databases/accounts.sqlite', query, (ctx.author.id,))
        bank = account_amount(result[0][0])
        await ctx.send(bank[0])
        text = ""
        for resource in bank[1]:
            text += f"{resource}: {bank[1][resource]}\n"
        await ctx.author.send(text)
        await ctx.send("DM sent")
    
    @account.command()
    @commands.check(helpers.perms_ten)
    async def create(self, ctx, account_name, owner_discord_id, owner_nation_id):
        query = """
            INSERT INTO accounts
                (owner_discord_id, owner_name, owner_nation_id)
            VALUES
                (?, ?, ?)
        """
        arguments = (owner_discord_id, account_name, owner_nation_id)
        helpers.execute_query('databases/accounts.sqlite', query, arguments)
        await ctx.send(account_amount(account_name))
        await ctx.send(f"Account `{account_name}` created, linked to discord id `{owner_discord_id}` and nation id `{owner_nation_id}`")

    @account.command()
    @commands.check(helpers.perms_ten)
    async def update(self, ctx, account_name, *resources):
        resources_dict = helpers.rss_list_to_dict(resources)
        update_account(account_name, resources_dict)
        await ctx.send(account_amount(account_name))

    @account.command()
    @commands.check(helpers.perms_ten)
    async def delete(self, ctx, account_name):
        query = "DELETE FROM accounts WHERE owner_name = ?"
        helpers.execute_query('databases/accounts.sqlite', query, (account_name,))
        await ctx.send(f"Account for `{account_name}` removed")

    @account.command('withdraw')
    async def account_withdraw(self, ctx, account_name, bank_alliance_id, *resources):
        query = "SELECT owner_name FROM accounts WHERE owner_name = ?"
        account_name = helpers.read_query('databases/accounts.sqlite', query, (account_name,))
        if not account_name:
            raise Exception("Account not found")
        account_name = account_name[0][0]
        to_withdraw = helpers.rss_list_to_dict(resources)
        account_data = account_amount(account_name)
        owner_discord_id, owner_name, owner_nation_id = account_data[0]
        account_bank = account_data[1]
        for resource in to_withdraw:
            if account_bank[resource] < to_withdraw[resource]:
                raise Exception(f"Too much {resource} selected")
        url = f"https://politicsandwar.com/api/nation/id={owner_nation_id}&key={helpers.apikey()}"
        data = requests.get(url).json()
        nation_name = data['name']
        helpers.catch_api_error(data, version=1)
        # result = withdraw(bank_alliance_id, "Nation", "Farmtopia", *resources)
        new_account_bank = {resource:account_bank[resource] for resource in account_bank}
        for resource in to_withdraw:
            new_account_bank[resource] -= to_withdraw[resource]
        update_account(owner_name, new_account_bank)
        await ctx.send(f"Sent `{to_withdraw}` to nation `{nation_name}` from `{owner_name}`'s account")
        new_amounts = account_amount(owner_name)
        await ctx.send(new_amounts[0])
        new_amounts = new_amounts[1]
        text = ""
        for resource in new_amounts:
            text += f"{resource}: {new_amounts[resource]}\n"
        await ctx.send(text)

    @account.command()
    @commands.check(helpers.perms_ten)
    async def add(self, ctx, account_name, *resources):
        resources_dict = helpers.rss_list_to_dict(resources)
        query = "SELECT * FROM accounts WHERE owner_name = ?"
        current_amounts = helpers.read_query('databases/accounts.sqlite', query, (account_name,))
        if not current_amounts:
            raise Exception("Account not found")
        resources = ["cash", "food", "coal", "oil", "uranium", "lead", "iron", "bauxite", "gasoline", "munitions", "steel", "aluminum"]
        current_amounts = current_amounts[0][3:]
        amounts = {resources[i]:current_amounts[i] for i in range(len(resources))}
        for resource in amounts:
            amounts[resource] += resources_dict[resource]
        update_account(account_name, amounts)
        new_amounts = account_amount(account_name)
        await ctx.send(new_amounts[0])
        new_amounts = new_amounts[1]
        text = ""
        for resource in new_amounts:
            text += f"{resource}: {new_amounts[resource]}\n"
        await ctx.send(text)

    @account.error
    async def account_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}account <action>`")


def setup(bot):
    bot.add_cog(Bank(bot))