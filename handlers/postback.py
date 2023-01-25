from loader import bot
from models.FastBotInst import Postback


@bot.postback_handler(payload=["payload"])
async def postback(postback: Postback):
    await bot.send_message(postback.sender_id, "clock payload1")


@bot.postback_handler(payload=["postback666"])
async def postback(postback: Postback):
    await bot.send_message(postback.sender_id, "clock payload2")


@bot.postback_handler()
async def postback(postback: Postback):
    print(postback)
