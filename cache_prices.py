import requests
import sqlite3
from sqlite3 import Error
import helpers


def store_prices():
    prices = helpers.prices("all")
    helpers.execute_query("DELETE FROM prices;")
    for resource in prices:
        data = prices[resource]
        if data['highestbuy']:
            buy_market = int(data['highestbuy']['price'])
        else:
            buy_market = 0
        if data['lowestbuy']:
            sell_market = int(data['lowestbuy']['price'])
        else:
            sell_market = 0
        query = """
            INSERT INTO prices
                (resource, sell_market, buy_market, avg_price)
            VALUES
                (?, ?, ?, ?)
        """
        arguments = (resource, sell_market, buy_market, int(data['avgprice']))
        helpers.execute_query(query, arguments)



if __name__ == "__main__":
    store_prices()