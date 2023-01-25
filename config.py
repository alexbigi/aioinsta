import os

WEBHOOK_VERIFY_TOKEN = "check"
TOKEN = "token"
API_URL = "https://graph.facebook.com/v11.0/me/messages?access_token="


def get_path_states():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, "state/state_database.sqlite")
    return db_path
