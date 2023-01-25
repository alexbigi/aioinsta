import json

import aiosqlite
import requests

import config
from requests_futures.sessions import FuturesSession


class FastBotInst:
    token = ""
    handlers = {}
    session = FuturesSession()
    exclude_text = []
    exclude_postback = []
    db = None

    def __init__(self, token):
        self.token = token
        self.handlers = {}

    async def create(self, state_storage):
        if state_storage == "sqlite":
            self.db = await aiosqlite.connect(config.get_path_states())
        elif state_storage == "memory":
            self.db = await aiosqlite.connect("file::memory:")
            await self.db.execute('CREATE TABLE "states" ("user_id" TEXT, "state" TEXT, "vars" TEXT)')
            await self.db.commit()

    async def call(self, type=None, data=None):
        # check states for user
        if not await self.check_state(data.sender_id):
            await self.db.execute("INSERT INTO states VALUES (?, ?, ?)", (data.sender_id, "", "{}"))
            await self.db.commit()

        # get user state
        state = await self.get_state(data.sender_id)

        if type in self.handlers:
            for h in self.handlers[type]:
                if type == "message":
                    if h["text"] is not None and data.msg_text in h["text"]:
                        if h["state"] == state or h["state"] == "*":
                            await h["handler"](data)
                elif type == "postback":
                    if h["text"] is not None and data.postback_payload in h["text"]:
                        if h["state"] == state or h["state"] == "*":
                            await h["handler"](data)
                if h["text"] is None:
                    if type == "postback" and data.postback_payload not in self.exclude_postback:
                        if h["state"] == state or h["state"] == "*":
                            await h["handler"](data)
                    if type == "message" and data.msg_text not in self.exclude_text:
                        if h["state"] == state or h["state"] == "*":
                            await h["handler"](data)

    def message_handler(self, type="message", text=None, state=None):
        def register_handler(handler):
            if text is not None:
                self.exclude_text = self.exclude_text + text
            if type in self.handlers:
                self.handlers[type].append({"handler": handler, "text": text,
                                            **({"state": state} if state is not None else {"state": ""})})
            else:
                self.handlers[type] = [{"handler": handler, "text": text,
                                        **({"state": state} if state is not None else {"state": ""})}]
            return handler

        return register_handler

    def postback_handler(self, type="postback", payload=None, state=None):
        def register_handler(handler):
            if payload is not None:
                self.exclude_postback = self.exclude_postback + payload
            if type in self.handlers:
                self.handlers[type].append({"handler": handler, "text": payload,
                                            **({"state": state} if state is not None else {"state": ""})})
            else:
                self.handlers[type] = [{"handler": handler, "text": payload,
                                        **({"state": state} if state is not None else {"state": ""})}]
            return handler

        return register_handler

    async def send_message(self, sender_id, msg_text):
        request_body = {'recipient': {'id': sender_id}, 'message': {"text": msg_text}}
        # response = requests.post(config.API_URL + self.token,
        #                          json=request_body).json()
        return self.send_to_api(request_body)

    async def send_image_url(self, sender_id, url):
        request_body = {'recipient': {'id': sender_id},
                        "message": {"attachment": {"type": "image", "payload": {"url": url}}}}
        return self.send_to_api(request_body)

    async def send_heart(self, sender_id):
        request_body = {'recipient': {'id': sender_id},
                        "message": {"attachment": {"type": "like_heart"}}}
        return self.send_to_api(request_body)

    async def send_react(self, sender_id, message_id):
        request_body = {'recipient': {'id': sender_id},
                        "sender_action": "react",
                        "payload": {
                            "message_id": message_id,
                            "reaction": "love"
                        }}
        # requests.post(config.API_URL + self.token,
        #               json=request_body).json()
        self.session.post(config.API_URL + self.token, json=request_body)

    async def send_unreact(self, sender_id, message_id):
        request_body = {'recipient': {'id': sender_id},
                        "sender_action": "react",
                        "payload": {
                            "reaction": "love"
                        }}
        # requests.post(config.API_URL + self.token,
        #               json=request_body).json()
        self.session.post(config.API_URL + self.token, json=request_body)

    async def send_generic(self, sender_id, generic):
        request_body = {'recipient': {'id': sender_id},
                        "message": {
                            "attachment": {
                                "type": "template",
                                "payload": {
                                    "template_type": "generic",
                                    "elements": generic
                                }
                            }
                        }}
        return self.send_to_api(request_body)

    async def send_ice_breakers(self, ice_breakers):
        request_body = {"ice_breakers": ice_breakers}
        # response = requests.post("https://graph.facebook.com/v11.0/me/messenger_profile?access_token=" + self.token,
        #                          json=request_body).json()
        response = self.session.post("https://graph.facebook.com/v11.0/me/messenger_profile?access_token=" + self.token,
                                     json=request_body).result()
        return json.loads(response.content.decode('utf-8'))

    async def delete_ice_breakers(self):
        request_body = {"fields": [
            "ice_breakers",
        ]}
        # response = requests.delete("https://graph.facebook.com/v11.0/me/messenger_profile?access_token=" + self.token,
        #                            json=request_body).json()
        response = self.session.delete("https://graph.facebook.com/v11.0/me/messenger_profile?access_token=" +
                                       self.token, json=request_body).result()
        return json.loads(response.content.decode('utf-8'))

    async def send_quick_replies(self, sender_id, text, replies):
        request_body = {'recipient': {'id': sender_id},
                        "messaging_type": "RESPONSE",
                        "message": {
                            "text": text,
                            "quick_replies": replies
                        }
                        }
        return self.send_to_api(request_body)

    async def next_state(self, state, recipient_id):
        if not self.check_state:
            await self.db.execute("INSERT INTO states VALUES (?, ?, ?)", (recipient_id, "", "{}"))
            await self.db.commit()

        await self.db.execute("UPDATE states SET state=? WHERE user_id=?", (state, recipient_id))
        await self.db.commit()

    async def clear_state(self, recipient_id):
        if not self.check_state:
            await self.db.execute("INSERT INTO states VALUES (?, ?, ?)", (recipient_id, "", "{}"))
            await self.db.commit()

        await self.db.execute("UPDATE states SET state=?,vars=? WHERE user_id=?", ("", "{}", recipient_id))
        await self.db.commit()

    async def get_state_vars(self, recipient_id) -> dict:
        if not self.check_state:
            await self.db.execute("INSERT INTO states VALUES (?, ?, ?)", (recipient_id, "", "{}"))
            await self.db.commit()

        cursor = await self.db.execute("SELECT vars FROM states WHERE user_id=?", (recipient_id,))
        res = await cursor.fetchall()
        await cursor.close()
        return eval(res[0][0])

    async def set_state_vars(self, recipient_id, vars):
        if not self.check_state:
            await self.db.execute("INSERT INTO states VALUES (?, ?, ?)", (recipient_id, "", "{}"))
            await self.db.commit()

        await self.db.execute("UPDATE states SET vars=? WHERE user_id=?", (str(vars), recipient_id))
        await self.db.commit()

    async def check_state(self, sender_id):
        cursor = await self.db.execute("SELECT * FROM states WHERE user_id=?", (sender_id,))
        res = await cursor.fetchall()
        await cursor.close()
        return res

    async def get_state(self, sender_id):
        cursor = await self.db.execute("SELECT state FROM states WHERE user_id=?", (sender_id,))
        res = await cursor.fetchall()
        await cursor.close()
        return res[0][0]

    def send_to_api(self, request_body):
        response = self.session.post(config.API_URL + self.token, json=request_body).result()
        return MessageAnswer(json.loads(response.content.decode('utf-8')))

    async def shutdown(self):
        await self.db.close()


class Message:
    object = ""
    entry_time = ""
    entry_id = 0
    sender_id = ""
    recipient_id = ""
    timestamp = ""
    msg_mid = ""
    msg_text = ""

    def __init__(self, object, entry_time, entry_id, sender_id, recipient_id, timestamp, msg_mid, msg_text):
        self.object = object
        self.entry_time = entry_time
        self.entry_id = entry_id
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.timestamp = timestamp
        self.msg_mid = msg_mid
        self.msg_text = msg_text


class Postback:
    object = ""
    entry_time = ""
    entry_id = 0
    sender_id = ""
    recipient_id = ""
    timestamp = ""
    postback_mid = ""
    postback_title = ""
    postback_payload = ""

    def __init__(self, object, entry_time, entry_id, sender_id, recipient_id, timestamp, postback_mid, postback_title,
                 postback_payload):
        self.object = object
        self.entry_time = entry_time
        self.entry_id = entry_id
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.timestamp = timestamp
        self.postback_mid = postback_mid
        self.postback_title = postback_title
        self.postback_payload = postback_payload


class MessageAnswer:
    recipient_id = ""
    message_id = ""

    def __init__(self, json):
        try:
            self.recipient_id = json["recipient_id"]
            self.message_id = json["message_id"]
        except KeyError:
            print("!!! ERROR:", json)


class DefaultAction(dict):
    def __init__(self, url):
        super().__init__({"type": "web_url", "url": url})


class ButtonUrl(dict):
    def __init__(self, title, url):
        super().__init__({"type": "web_url", "title": title, "url": url})


class ButtonPostback(dict):
    def __init__(self, title, payload):
        super().__init__({"type": "postback", "title": title, "payload": payload})


class Generic(dict):
    def __init__(self, title, image_url=None, sub_title=None, default_action=None, buttons=None):
        super().__init__({
            "title": title,
            **({"image_url": image_url} if image_url is not None else {}),
            **({"subtitle": sub_title} if sub_title is not None else {}),
            **({"default_action": default_action} if default_action is not None else {}),
            **({"buttons": buttons} if buttons is not None else {}),
        })


class IceBreaker(dict):
    def __init__(self, q, postback):
        super().__init__({
            "question": q,
            "payload": postback
        })


class ButtonReplies(dict):
    def __init__(self, title, payload, image=None):
        super().__init__({
            "content_type": "text",
            "title": title,
            "payload": payload,
            **({"image_url": image} if image is not None else {})
        })
