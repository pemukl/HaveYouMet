import json
import logging
from os.path import exists

from game import Game
from telegramApp import TelegramApp

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def load_config():
    if not exists("config.json"):
        with open("config.json", "w") as f:
            f.write('{\n"botToken":"",\n"adminId":0,\n"picturePath":""\n}')
        print("config.json created. Please fill it out.")
    else:
        with open("config.json", "r") as f:
            res = json.load(f)
        if "botToken" not in res or res["botToken"] == "":
            print("Please fill out config.json")
        else:
            return res

if __name__ == '__main__':
    config = load_config()
    if config:
        tapp = TelegramApp(config)
        tapp.run()