import logging
from urllib import parse

import uvicorn as uvicorn
from fastapi import Request, Response, BackgroundTasks

import config
from models.FastBotInst import Message, Postback, IceBreaker
from loader import bot, Scheduler, app

from handlers import bot


@app.on_event("startup")
async def start_app():
    await bot.create(state_storage="sqlite")
    Scheduler.start()
    # response = await bot.send_ice_breakers([IceBreaker("Hello", "hello"), IceBreaker("Start", "start")])
    # print("ice_breakers: " + str(response))
    # response = await bot.delete_ice_breakers()


@app.on_event("shutdown")
async def shutdown_event():
    logging.debug("SHUTDOWN !!!: ")
    await bot.shutdown()


@app.get("/webhook")
async def webhook_check(request: Request):
    params = dict(parse.parse_qsl(str(request.query_params)))
    verify_token = params["hub.verify_token"]
    # Check if sent token is correct
    if verify_token == config.WEBHOOK_VERIFY_TOKEN:
        # Responds with the challenge token from the request
        return Response(content=str(params["hub.challenge"]), media_type="application/xml")
    return Response(content='Unable to authorise.', media_type="application/xml")


@app.post("/webhook")
async def webhook_work(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    # print(data)
    try:
        message = Message(data["object"], data["entry"][0]["time"], data["entry"][0]["id"],
                          data["entry"][0]["messaging"][0]["sender"]["id"],
                          data["entry"][0]["messaging"][0]["recipient"]["id"],
                          data["entry"][0]["messaging"][0]["timestamp"],
                          data["entry"][0]["messaging"][0]["message"]["mid"],
                          data["entry"][0]["messaging"][0]["message"]["text"])
        try:
            tmp = data["entry"][0]["messaging"][0]["message"]["is_echo"]
            echo_checker = True
        except:
            echo_checker = False
        if not echo_checker:
            try:
                if data["entry"][0]["messaging"][0]["message"]["quick_reply"]:
                    postback = Postback(data["object"], data["entry"][0]["time"], data["entry"][0]["id"],
                                        data["entry"][0]["messaging"][0]["sender"]["id"],
                                        data["entry"][0]["messaging"][0]["recipient"]["id"],
                                        data["entry"][0]["messaging"][0]["timestamp"],
                                        data["entry"][0]["messaging"][0]["message"]["mid"],
                                        data["entry"][0]["messaging"][0]["message"]["text"],
                                        data["entry"][0]["messaging"][0]["message"]["quick_reply"]["payload"])
                    background_tasks.add_task(bot.call, type="postback", data=postback)
                    return "ok", 200
            except:
                pass
            background_tasks.add_task(bot.call, type="message", data=message)
            return "ok", 200
    except:
        pass

    try:
        postback = Postback(data["object"], data["entry"][0]["time"], data["entry"][0]["id"],
                            data["entry"][0]["messaging"][0]["sender"]["id"],
                            data["entry"][0]["messaging"][0]["recipient"]["id"],
                            data["entry"][0]["messaging"][0]["timestamp"],
                            data["entry"][0]["messaging"][0]["postback"]["mid"],
                            data["entry"][0]["messaging"][0]["postback"]["title"],
                            data["entry"][0]["messaging"][0]["postback"]["payload"])
        background_tasks.add_task(bot.call, type="postback", data=postback)
    except:
        pass
    return "ok", 200


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5000)
