import os
import re
import sys
import time
import json
import random
from glob import glob
from colorama import *
from pathlib import Path
from datetime import datetime
from requests import get, post
from urllib.parse import unquote, parse_qs
from telethon.sync import TelegramClient  # type: ignore
from telethon.tl.types import InputBotAppShortName  # type: ignore
from requests.exceptions import ConnectionError, Timeout
from telethon.tl.functions.messages import RequestWebViewRequest  # type: ignore
from telethon.errors import SessionPasswordNeededError

init(autoreset=True)

merah = Fore.LIGHTRED_EX
hijau = Fore.LIGHTGREEN_EX
kuning = Fore.LIGHTYELLOW_EX
biru = Fore.LIGHTBLUE_EX
hitam = Fore.LIGHTBLACK_EX
reset = Style.RESET_ALL
putih = Fore.LIGHTWHITE_EX


class Vivaftntod:
    def __init__(self):
        self.session_path = "sessions"
        self.peer = "@vivaftn_bot"
        self.DEFAULT_APIID = 6
        self.DEFAULT_APIHASH = "eb06d4abfb49dc3eeb1aeb98ae0f581e"
        self.line = putih + "~" * 50

    def log(self, msg):  # type: ignore
        now = datetime.now().isoformat(" ").split(".")[0]
        print(f"{hitam}[{now}]{reset} {msg}")

    def http(self, url, headers, data=None):
        while True:
            try:
                if data is None:
                    res = get(url, headers=headers)
                    open("http.log", "a", encoding="utf-8").write(res.text + "\n")
                    if "cloudflare.com" in res.text or res.status_code > 500:
                        self.log(f"{merah} failed get json response !")
                        time.sleep(2)
                        continue
                    return res

                if data == "":
                    res = post(url, headers=headers)
                    open("http.log", "a", encoding="utf-8").write(res.text + "\n")
                    if "cloudflare.com" in res.text or res.status_code > 500:
                        self.log(f"{merah} failed get json response !")
                        time.sleep(2)
                        continue
                    return res

                res = post(url, headers=headers, data=data)
                open("http.log", "a", encoding="utf-8").write(res.text + "\n")
                if "cloudflare.com" in res.text or res.status_code > 500:
                    self.log(f"{merah} failed get json response !")
                    time.sleep(2)
                    continue
                return res
            except (ConnectionError, Timeout):
                self.log(f"{merah}connection error / connection timeout !")
                time.sleep(1)
                continue

    def secto(self, second):
        minute, second = divmod(second, 60)
        hour, minute = divmod(minute, 60)
        hour = str(hour).zfill(2)
        minute = str(minute).zfill(2)
        second = str(second).zfill(2)
        return f"{hour}:{minute}:{second}"

    def captcha_solver(self, captcha, headers):
        _captcha = captcha.replace("=", "")
        solve = eval(_captcha)
        self.log(f"{kuning}captcha : {captcha} {solve}")
        url = "https://tgames-vivaftn.bcsocial.net/panel/users/verifyCapcha"
        data = json.dumps({"code": solve})
        res = self.http(url, headers, data)
        if "ok" in res.text.lower():
            self.log(f"{hijau}success bypass captcha")

    def login(self, data):
        url = "https://tgames-vivaftn.bcsocial.net/panel/users/login"
        headers = {
            "host": "tgames-vivaftn.bcsocial.net",
            "connection": "keep-alive",
            "accept": "application/json, text/plain, */*",
            "user-agent": "Mozilla/5.0 (Linux; Android 10; Redmi 4A / 5A Build/QQ3A.200805.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/86.0.4240.185 Mobile Safari/537.36",
            "content-type": "application/json",
            "origin": "https://tgames-vivaftn.bcsocial.net",
            "x-requested-with": "org.telegram.messenger",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://tgames-vivaftn.bcsocial.net/",
            "accept-language": "en,en-US;q=0.9",
        }
        res = self.http(url, headers, json.dumps(data))
        if "ok" not in res.text.lower():
            self.log(f"{kuning}something error?? try again later !")
            return 0

        balance = res.json()["data"]["balance"]
        draft_balance = res.json()["data"]["balanceDraft"]
        next_claim = res.json()["data"]["nextClaimTime"]
        captcha = res.json()["data"]["capcha"]
        cookie = self.cookie_dict_to_string(res.cookies.get_dict())
        headers["cookie"] = cookie
        self.log(f"{hijau}balance : {putih}{balance}")
        self.log(f"{hijau}draft balance : {putih}{draft_balance}")
        if len(captcha) > 0:
            self.log(f"{kuning}captcha detected !")
            self.captcha_solver(captcha, headers)

        if next_claim > 0:
            self.log(f"{kuning}no time to claim !")
            self.log(f"{kuning}next claim : {putih}{self.secto(next_claim)}")
            return next_claim

        data = json.dumps({})
        url_claim = "https://tgames-vivaftn.bcsocial.net/panel/games/claim"
        res = self.http(url_claim, headers, data)
        if "ok" not in res.text.lower():
            self.log(f"{merah}claim failure !")
            return 0
        
        self.log(f"{hijau}claim successfully !")
        url_user = "https://tgames-vivaftn.bcsocial.net/panel/users/getUser"
        res = self.http(url_user, headers, data)
        if "data" not in res.text:
            self.log(f"{kuning}something error ? try again later !")
            return 3600

        balance = res.json()["data"]["balance"]
        draft_balance = res.json()["data"]["balanceDraft"]
        next_claim = res.json()["data"]["nextClaimTime"]
        self.log(f"{hijau}balance : {putih}{balance}")
        self.log(f"{hijau}draft balance : {putih}{draft_balance}")
        if next_claim > 0:
            self.log(f"{kuning}no time to claim !")
            self.log(f"{kuning}next claim : {putih}{self.secto(next_claim)}")
            return next_claim

        return 0

    def cookie_dict_to_string(self, dict_cookie):
        string_cookie = ""
        for coek in dict_cookie.items():
            key, value = coek
            string_cookie = f"{key}={value}; "

        return string_cookie

    def telegram_connect(self, phone, req_data=False):  # type: ignore
        if not os.path.exists(self.session_path):
            os.makedirs(self.session_path)

        if not os.path.exists("devices.json"):
            res = get(
                "https://gist.githubusercontent.com/akasakaid/808a34986091b13d03b537584ea754dc/raw/b0dd89abd83c6403338ff7d6d95e0a89d159e6a2/devices.json"
            )
            open("devices.json", "w").write(res.text)
        devices = json.loads(open("devices.json", "r").read())
        model = random.choice(list(devices.keys()))
        system_version = devices[model]
        config = json.loads(open("config.json", "r").read())
        client = TelegramClient(
            f"{self.session_path}/{phone}",
            api_id=(
                config["api_id"] if len(config["api_id"]) > 0 else self.DEFAULT_APIID
            ),
            api_hash=(
                config["api_hash"]
                if len(config["api_hash"]) > 0
                else self.DEFAULT_APIHASH
            ),
            device_model=model,
            system_version=system_version,
            app_version="10.6.0 (4261)",
        )
        client.connect()
        if not client.is_user_authorized():
            try:
                client.send_code_request(phone)
                otp = input(
                    f'[{hitam}{datetime.now().isoformat(" ").split(".")[0]}] {hijau}input login code : {putih}'
                )
                client.sign_in(phone=phone, code=otp)
            except SessionPasswordNeededError:
                pw2fa = input(
                    f'[{hitam}{datetime.now().isoformat(" ").split(".")[0]}] {hijau}input 2fa password : {putih}'
                )
                client.sign_in(password=pw2fa)
            except Exception as e:
                self.log(f"{merah}{e}")
                return False

        if req_data is False:
            me = client.get_me()
            self.log(f"{hijau}login as {me.first_name}")
            if client.is_connected():
                client.disconnect()
            return True

        if req_data:
            res = client(
                RequestWebViewRequest(
                    peer=self.peer,
                    platform="Android",
                    from_bot_menu=False,
                    bot=self.peer,
                    url="https://tgames-vivaftn.bcsocial.net",
                )
            )
            param = unquote(
                res.url.split("#tgWebAppData=")[1].split("&tgWebAppVersion=")[0]
            )

            if client.is_connected():
                client.disconnect()

            return param

    def countdown(self, t):
        while t:
            menit, detik = divmod(t, 60)
            jam, menit = divmod(menit, 60)
            jam = str(jam).zfill(2)
            menit = str(menit).zfill(2)
            detik = str(detik).zfill(2)
            print(f"{putih}waiting until {jam}:{menit}:{detik} ", flush=True, end="\r")
            t -= 1
            time.sleep(1)
        print("                          ", flush=True, end="\r")

    def parse(self, data):
        meqmeq = parse_qs(data)
        pepek = {key: value[0] for key, value in meqmeq.items()}
        return pepek

    def main(self):
        banner = f"""
    {hijau}Auto Claim {biru}Vivaftn {hijau}on Telegram
    
    {biru}By : {putih}t.me/AkasakaID
    {hijau}Github: {putih}@AkasakaID
        
        """
        menu = f"""
    {putih}1. {hijau}Create Session
    {putih}2. {hijau}Start Bot
        """
        while True:
            arg = sys.argv
            if "noclear" not in arg:
                os.system("cls" if os.name == "nt" else "clear")
            print(banner)
            print(menu)
            option = input(
                f'[{hitam}{datetime.now().isoformat(" ").split(".")[0]}] {hijau}input number : {putih}'
            )
            if option == "1":
                phone = input(
                    f'[{hitam}{datetime.now().isoformat(" ").split(".")[0]}] {hijau}input phone number : {putih}'
                )
                self.telegram_connect(phone)
                input(
                    f'[{hitam}{datetime.now().isoformat(" ").split(".")[0]}] {putih}press enter to continue'
                )
                continue
            if option == "2":
                while True:
                    list_countdown = []
                    sessions = glob("sessions/*.session")
                    _start = int(time.time())
                    for session in sessions:
                        phone = Path(session).stem
                        phonef = phone.replace(phone[5:8], "****")
                        self.log(f"{hijau}start using phone : {putih}{phonef}")
                        result = self.telegram_connect(phone, req_data=True)
                        if result is False:
                            continue
                        parser = self.parse(result)
                        user = json.loads(parser["user"])
                        self.log(f'{hijau}login as {putih}{user["first_name"]}')
                        data = {
                            "gameId": 2,
                            "initData": {
                                "query_id": parser["query_id"],
                                "user": parser["user"],
                                "auth_date": parser["auth_date"],
                                "hash": parser["hash"],
                            },
                            "externalId": user["id"],
                            "username": user.get("username", ""),
                            "firstName": user["first_name"],
                            "language": "en",
                            "lastName": user.get("last_name", ""),
                            "refId": "",
                        }
                        result = self.login(data)
                        list_countdown.append(result)
                        print(self.line)
                        self.countdown(5)
                    _end = int(time.time())
                    _tot = _end - _start
                    _min = min(list_countdown)
                    if (_min - _tot) <= 0:
                        continue
                    self.countdown(_min - _tot)

            self.log(f"{kuning}input number not have option !")
            input(
                f'[{hitam}{datetime.now().isoformat(" ").split(".")[0]}] {putih}press enter to continue'
            )


if __name__ == "__main__":
    try:
        app = Vivaftntod()
        app.main()
    except KeyboardInterrupt:
        sys.exit()
