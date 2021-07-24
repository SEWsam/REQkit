"""
Copyright (c) 2020 - 2021 SEWsam

Author: SEWsam
Source version: 2.0
"""
import json
import os
import sys
import time
import platform
from typing import Union
from json.decoder import JSONDecodeError
from zipfile import ZipFile

import click
import requests
import selenium.common.exceptions
from colorama import Fore, Style, init
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from seleniumrequests import Chrome  # noqa

init(convert=True)
dot = u'\u00b7'



class REQStore:
    def __init__(self, timeout=10):
        """Class interface for Halo 5 REQ Store

        :param int timeout: Timeout for login. Default=10
        """

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

        self.driver: Chrome = Chrome("chromedriver", options=chrome_options)
        self.token: str = ""
        self.timeout: int = timeout


        self.login_url = "https://login.live.com/oauth20_authorize.srf?client_id=000000004C0BD2F1&scope=xbox.basic+xbox" \
                    ".offline_access&response_type=code&redirect_uri=https:%2f%2fwww.halowaypoint.com%2fauth%2fcallback" \
                    "&locale=en-us&display=touch&state=https%253a%252f%252fwww.halowaypoint.com%252fen-us "

        self.buy_url = "https://www.halowaypoint.com/en-us/games/halo-5-guardians/xbox-one/requisitions/buy-pack"

        self.sell_url = "https://www.halowaypoint.com/en-us/games/halo-5-guardians/xbox-one/requisitions/sell"

    def login(self, username, password):
        # Type User and password into site. Incorrect username = unclickable button = timeout. Incorrect password = no token
        self.driver.get(self.login_url)

        un_field = (By.ID, "i0116")
        pw_field = (By.ID, "i0118")
        next_button = (By.ID, "idSIButton9")

        WebDriverWait(self.driver, self.timeout).until(ec.presence_of_element_located(un_field)).send_keys(username)

        WebDriverWait(self.driver, self.timeout).until(ec.element_to_be_clickable(next_button)).click()

        WebDriverWait(self.driver, self.timeout).until(ec.element_to_be_clickable(pw_field)).send_keys(password)

        log_in = (By.XPATH, '//*[contains(@value, "Sign in")]')
        WebDriverWait(self.driver, self.timeout).until(ec.presence_of_element_located(log_in)).click()

    def get_token(self):
        # Get authentication for account actions, this also checks if the user ever actually logged in (Correct password)
        verify_url = "https://account.microsoft.com/"
        self.driver.request("GET", verify_url)
        try:
            token_element = self.driver.find_element_by_name("__RequestVerificationToken")
            self.token = token_element.get_attribute("value")
            return True
        except selenium.common.exceptions.NoSuchElementException:
            # Remove this, move it below.
            print(
                f"[{Fore.RED}-{Style.RESET_ALL}] Failed to verify login with Xbox. Maybe Incorrect Password?")
            # Keep this. Message above should be removed and should be a response to 'retry' being returned.
            return False

    def buy_request(self, request_data): 
        headers = {
            'Connection': 'keep-alive',
            'Origin': 'https://www.halowaypoint.com',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 ( KHTML, '
                          'like Gecko) Chrome/79.0.3945.117 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept': '*/*',
            'X-Requested-With': 'XMLHttpRequest',
            'Request-Id': '|pXnSc.C9p//',
            'Request-Context': 'appId=cid-v1:43ddedb6-69f4-462e-a9bf-ab85dd647d12',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Referer': 'https://www.halowaypoint.com/en-us/games/halo-5-guardians/xbox-one/requisitions/store',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7,es;q=0.6',
        }
        
        request_data += self.token
        response = self.driver.request("POST", self.buy_url, headers=headers, data=request_data).content.decode()
        json_response = json.loads(response)

        return json_response

def update():
    print(f"[!] A REQkit update ({Fore.YELLOW}{remote_db['version']}{Style.RESET_ALL}) is required. Installing now.")
    time.sleep(.5)

    with open("resource/db.json", "w") as f_writeable:
        f_writeable.write(json.dumps(remote_db, indent=4))

    print(f"[{Fore.GREEN}+{Style.RESET_ALL}] Update Successful. Please relaunch REQkit. Exiting in 2 seconds.")
    time.sleep(2)
    sys.exit()


def update_driver(task):
    try:
        os.mkdir("temp")
    except FileExistsError:
        pass

    dl_platform: str = None
    latest = requests.get("https://chromedriver.storage.googleapis.com/LATEST_RELEASE").text
    if platform.system() == "Linux":
        # once again, proof i've switched around. linux must be the first condition. (writing this on arch btw)
        dl_platform = "linux64"
    elif platform.system() == "Windows":
        dl_platform = "win64"
    else:
        print("uhhh fuck, how do i figure out if it's an m1 mac?")
        sys.exit(1)

    driver_zip = requests.get(f"https://chromedriver.storage.googleapis.com/{latest}/chromedriver_{dl_platform}.zip").content

    with open('temp/chromedriver_' + dl_platform + '.zip', 'wb') as temp_zip:
        temp_zip.write(driver_zip)

    driver_zip = f'temp/chromedriver_{dl_platform}_.zip'
    with ZipFile(driver_zip, 'r') as zipObj:
        # i'll finish this tomorrow. it's 3am. i need to go to bed.
        zipObj.extractall("C:\\bin")  # TODO: Add Var for webdriver location

    # TODO: Remove this, allow this to be custom inserted
    print(
        f"[{Fore.GREEN}+{Style.RESET_ALL}] Chromedriver {task} finished. Please run REQkit again. Auto-Exiting in 3 "
        f"seconds. "
    )
    time.sleep(1.5)


def query_pack(pack_name: str = None) -> Union[dict, bool]:
    for pack in db["packs"]:
        if pack[0] == pack_name:
            return pack

    return False




def sell_cards(driver, token, card_id, quantity):
    card = db["reqs"][int(card_id)]
    card_name = card[0]
    card_price = card[1]
    request_data = card[2] + token

    while True:
        confirm_sell = input(
            f"[?] {quantity} {card_name}'s will be sold for {card_price} REQ Points each. You will gain "
            f"{int(card_price) * int(quantity)} REQ Points. Are you sure? (y/n) "
        )

        if confirm_sell[0] == 'y':
            print(f"[{dot}] Selling card(s)...")
            headers = {
                'Accept': '*/*',
                'X-Requested-With': 'XMLHttpRequest',
                'Request-Id': '|Qk9Nu.R2BZR',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/87.0.4280.88 Safari/537.36',
                'Request-Context': 'appId=cid-v1:43ddedb6-69f4-462e-a9bf-ab85dd647d12',
            }
            initial_sale = False
            for i in range(0, int(quantity)):
                try:
                    response = driver.request("POST", sell_url, headers=headers, data=request_data).content.decode()
                    json_response = json.loads(response)

                    if json_response["State"] is None:
                        print(f"[{Fore.GREEN}+{Style.RESET_ALL}] Success selling REQ!")
                        initial_sale = True

                except (KeyError, JSONDecodeError):
                    if not initial_sale:
                        i = 0
                    print(
                        f"\n[{Fore.RED}-{Style.RESET_ALL}] Sell Error. You may have sold all of this REQ. {i} packs "
                        f"were sucessfully sold. You have gained {i * int(card_price)} REQ Points. "
                        f"Type 'exit' to exit\n"
                    )
                    return

            print(f"\n[{Fore.GREEN}+{Style.RESET_ALL}] Success selling all REQs! Type 'exit' to exit.\n")
            return
        elif confirm_sell[0] == 'n':
            print(f"[{dot}] Cancelling. Type 'exit' to exit.")
            return
        else:
            continue


@click.group(options_metavar="<options>")
@click.option(
    "--username", "-u", metavar="Email",
    help="The Microsoft/Xbox email associated with your Halo 5 Profile"
)
@click.option(
    "--password", "-p", metavar="Text",
    help="The Password for the associated Microsoft/Xbox email account."
)
@click.pass_context
def main(ctx, username, password):
    """
    Buys 'REQ Packs' for the game "Halo 5: Guardians'.\n

    Minimal help display. Run '--help noarg', or '-h noarg' for more info
    """
    ctx.ensure_obj(REQStore)
    if username is None or password is None:
        print(f"[{Fore.RED}-{Style.RESET_ALL}] Error: Both Username and Password Option need to be filled.")
        sys.exit(1)

    print(f"[{dot}] Logging in to Halo with email '{username}'...")
    has_tried = False
    while True:
        try:
            ctx.obj.login(username, password)
        except selenium.common.exceptions.TimeoutException:
            print(f"[{Fore.RED}-{Style.RESET_ALL}] Failed to login with Xbox. Incorrect Username?")
            sys.exit(1)

        print(f"[{dot}] Verifying login with Xbox...")
        token = ctx.obj.get_token()
        if token:
            break
        else:
            if not has_tried:
                print(f"[{dot}] Retrying")
                has_tried = True
                continue
            if has_tried:
                print(f"[{Fore.RED}-{Style.RESET_ALL}] Retried login twice, but failed. Exiting...")
                sys.exit(1)

    print(f"[{Fore.GREEN}+{Style.RESET_ALL}] Success Logging in!")


@main.command()
@click.pass_context
def cli(ctx, token):  # TODO: add token to ctx.obj {}
    print(f"\n{Fore.YELLOW}Type 'help' for a list of commands.{Style.RESET_ALL}\n")
    while True:
        print(f"REQkit CLI Mode: {Fore.GREEN}%{Style.RESET_ALL} ", end="")
        cmd = input().lower()
        if cmd == "exit":
            return
        elif cmd == "list":
            for index, req in enumerate(db["reqs"]):
                print(f"[{index}] {req[0]} - {req[1]} Points")
            print()
            continue
        elif cmd == "help":
            print(
                "REQkit CLI Mode Commands:\n"
                "   * help - Shows this menu\n"
                "   * list - list all reqs and their IDs\n"
                "   * find <term> - find a REQ and its ID by search term.\n"
                "   * sell <id> <quantity> - sell a REQ by its ID, X amount of times.\n"
            )
            continue

        cmd_args = cmd.split(" ", 1)

        if cmd_args[0] == "find":
            try:
                term = str(cmd_args[1]).lower()
                for index, req in enumerate(db["reqs"]):
                    if term in str(req[0]).lower():
                        print(f"[{index}] {req[0]} - {req[1]} Points")
                print()
            except IndexError:
                print(f"[{Fore.RED}-{Style.RESET_ALL}] Invalid Argument. Please enter a search term.")
                print("Usage: 'find <term>'\n")
        elif cmd_args[0] == "sell":
            cmd_args = cmd.split(" ", 2)
            try:
                card_id = cmd_args[1]
                quantity = cmd_args[2]
            except IndexError:
                print(f"[{Fore.RED}-{Style.RESET_ALL}] Invalid Argument. Please enter a REQ id, and qunatity to sell.")
                print("Usage: 'sell <id> <quantity>'\n")
                continue

            sell_cards(driver, token, card_id, quantity)
        else:
            print(f"[{Fore.RED}-{Style.RESET_ALL}] Invalid Command. Type 'help' for more info.\n")

@main.command()
@click.argument('req-pack', metavar="<REQ Pack Name>")
@click.pass_context
def buy_pack(ctx, req_pack):
    data = query_pack(pack_name=req_pack)
    if not data:
        print(f"[{Fore.RED}-{Style.RESET_ALL}] Error: Invalid REQ Pack name.")
        sys.exit(1)

    pack_full_name = data[1]
    price = data[2]
    request_data = data[3]

    while True:
        confirm_buy = input(f"[?] {pack_full_name} will be purchased for {price} REQ Points. Are you sure? (y/n)")
        if confirm_buy[0] == 'y':
            print(f"[{dot}] Buying pack...")
            buy_response = ctx.obj.buy_request(request_data)
            try:
                if buy_response["State"] is None:
                    print(f"[{Fore.GREEN}+{Style.RESET_ALL}] Success buying REQ Pack!")
                break
            except KeyError:
                if buy_response["Message"] == "You do not have enough credits to purchase this":
                    print(f"[{Fore.RED}-{Style.RESET_ALL}] Error: Insufficient REQ Points Balance.")
                break
        elif confirm_buy[0] == 'n':
            print(f"[{dot}] Exiting...")
            return
        else:
            continue


if __name__ == '__main__':
    with open("resource/db.json") as f:
        db = json.load(f)

    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        #TODO: change this name to something other than docstring
        print(
            f"USAGE: {sys.argv[0]} --username <username> --password <password> (cli|buy|sell) [OPTIONS] ...\n"
            f"Run '{sys.argv[0]} (COMMAND) --help' for help with each command.\n"
            f"\n"
            f"OPTIONS:\n"
            f"    -u, --username    The username for the Xbox/MS Account you play Halo 5 with.  (REQUIRED)\n"
            f"    -p, --password    The password for the Xbox/MS Account used.                  (REQUIRED)\n"
            f"        --help        Show this menu.                                                       \n"
            f"\n"
            f"PACK NAMES:\n"
            f"{db['docstring']}\n"
        )
        sys.exit(0)

    with open("resource/logo") as f:
        print(f.read())

    print(f"{Fore.CYAN}REQkit Version {db['version']}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}A tool for managing REQ Packs using the Halo 5 API{Style.RESET_ALL}")
    print(
        f"{Fore.YELLOW}Run '{sys.argv[0]}' --help' for help.{Style.RESET_ALL}\n"
    )

    remote_db = requests.get("https://sewsam.github.io/download/db.json").json()
    remote_ver = remote_db["version"].split(".")
    local_ver = db["version"].split(".")

    major_gt = False
    if int(local_ver[0]) < int(remote_ver[0]) or int(local_ver[1]) < int(remote_ver[1]):
        major_gt = True
        print(
            f"[!] An optional feature upgrade {Fore.YELLOW}({remote_db['version']}){Style.RESET_ALL} is available."
            f" Download it from https://github.com/SEWsam/REQkit/releases"
        )
    if not major_gt:
        try:
            try:
                patch_ver = int(local_ver[2])
            except IndexError:
                patch_ver = 0

            if patch_ver < int(remote_ver[2]):
                update()
        except IndexError:
            pass

    while True:
        try:
            main(obj=REQStore())
            break
        except selenium.common.exceptions.SessionNotCreatedException:
            print("[!] Chromedriver update required. Updating now...")
            update_driver("update")
            continue
        except selenium.common.exceptions.WebDriverException:
            print("[!] Chromedriver is not installed. Installing now...")
            update_driver("installation")
            continue
        finally:
            time.sleep(2)
