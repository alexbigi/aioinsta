from loader import bot
from models.FastBotInst import Message, ButtonReplies, Generic, ButtonUrl, ButtonPostback
from loader import Scheduler


async def push(message: Message):
    await bot.send_message(message.sender_id, "push")
    try:
        Scheduler.remove_job(job_id="some_text")
    except:
        pass


@bot.message_handler(text=["Привет", "привет"])
async def check(message: Message):
    await bot.send_message(message.sender_id, "введи имя:")

    await bot.next_state("wait_name", message.sender_id)
    # await bot.clear_state(message.sender_id)


@bot.message_handler(state="wait_name")
async def wait_name(message: Message):
    data = await bot.get_state_vars(message.sender_id)
    data["name"] = message.msg_text
    await bot.set_state_vars(message.sender_id, data)
    await bot.send_message(message.sender_id, "твой тел: ")
    await bot.next_state("wait_num", message.sender_id)
    pass


@bot.message_handler(state="wait_num")
async def wait_name(message: Message):
    data = await bot.get_state_vars(message.sender_id)
    data["tel"] = message.msg_text
    await bot.set_state_vars(message.sender_id, data)
    await bot.send_message(message.sender_id, "твой адрес: ")
    await bot.next_state("wait_addrr", message.sender_id)
    pass


@bot.message_handler(state="wait_addrr")
async def wait_name(message: Message):
    data = await bot.get_state_vars(message.sender_id)
    data["addrr"] = message.msg_text
    await bot.set_state_vars(message.sender_id, data)
    await bot.send_message(message.sender_id,
                           f"твои данные: \nимя: {data['name']}\nтелефон: {data['tel']}\nадрес: {data['addrr']}")
    await bot.clear_state(message.sender_id)


@bot.message_handler(text=["help"], state="*")
async def start(message: Message):
    await bot.send_message(message.sender_id, "ПАМАГИИ МНЕ !!")
    await bot.send_heart(message.sender_id)


@bot.message_handler()
async def echo(message: Message):
    # Scheduler.add_job(push, 'interval', args=[message], seconds=5,
    #                   replace_existing=True,
    #                   id="some_text")
    await bot.send_react(message.sender_id, message.msg_mid)
    # response = await bot.send_message(message.sender_id, message.msg_text)
    # response = await bot.send_image_url(message.sender_id, "http://oboi-dlja-stola.ru/file/684/760x0/16:9/%D0%A1%D0%B5%D1%80%D0%B5%D0%BD%D1%8C%D0%BA%D0%B8%D0%B9-%D0%BA%D0%BE%D1%82%D0%B8%D0%BA.jpg")
    await bot.send_heart(message.sender_id)
    # await bot.send_generic(message.sender_id, title="TITLE", sub_title="SUBTITLE", image_url="http://oboi-dlja-stola.ru/file/684/760x0/16:9/%D0%A1%D0%B5%D1%80%D0%B5%D0%BD%D1%8C%D0%BA%D0%B8%D0%B9-%D0%BA%D0%BE%D1%82%D0%B8%D0%BA.jpg")
    # await bot.send_generic(message.sender_id, title="Заголовок", default_action=Default_action("https://creativebots.info"))
    await bot.send_generic(message.sender_id, [Generic(title="Заголовок",
                                                       buttons=[ButtonUrl("URL", "https://google.com"),
                                                                ButtonPostback("title", "payload")]),
                                               Generic(title="Заголовок",
                                                       buttons=[ButtonUrl("URL", "https://google.com"),
                                                                ButtonPostback("title", "payload")]),
                                               Generic(title="TITLE",
                                                       sub_title="SUBTITLE",
                                                       image_url="http://oboi-dlja-stola.ru/file/684/760x0/16:9/%D0%A1%D0%B5%D1%80%D0%B5%D0%BD%D1%8C%D0%BA%D0%B8%D0%B9-%D0%BA%D0%BE%D1%82%D0%B8%D0%BA.jpg"),

                                               ])
    await bot.send_quick_replies(message.sender_id, "Текст вопроса", [ButtonReplies("варик1", "payload"),
                                                                      ButtonReplies("варик1", "postback666")])