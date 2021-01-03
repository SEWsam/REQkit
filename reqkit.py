"""
Copyright (c) 2020 - 2021 Samuel Wirth

Author: Samuel "SEWsam" Wirth
API Version: 1.3.X-dev
"""
import json
import click
import requests
import time
import os
import sys

import selenium.common.exceptions
from colorama import Fore, Style, init

from zipfile import ZipFile
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from seleniumrequests import Chrome

init(convert=True)
mdot = u'\u00b7'

login_url = "https://login.live.com/oauth20_authorize.srf?client_id=000000004C0BD2F1&scope=xbox.basic+xbox" \
            ".offline_access&response_type=code&redirect_uri=https:%2f%2fwww.halowaypoint.com%2fauth%2fcallback" \
            "&locale=en-us&display=touch&state=https%253a%252f%252fwww.halowaypoint.com%252fen-us "

buy_url = "https://www.halowaypoint.com/en-us/games/halo-5-guardians/xbox-one/requisitions/buy-pack"


def update():
    print(f"[!] A REQkit update ({Fore.YELLOW}{remote_db['version']}{Style.RESET_ALL}) is required. Installing now.")
    time.sleep(.5)

    with open("resource/db.json", "w") as f_writeable:
        f_writeable.write(json.dumps(remote_db, indent=4))

    print(f"[{Fore.GREEN}+{Style.RESET_ALL}] Update Successful. Please relaunch REQkit. Exiting in 2 seconds.")
    time.sleep(2)
    sys.exit()

    # TODO: Save for v1.5.x
    # subprocess.Popen(["reqkit.exe", f"--{username}"])


def update_driver(task):
    try:
        os.mkdir("temp")
    except FileExistsError:
        pass

    latest = requests.get("https://chromedriver.storage.googleapis.com/LATEST_RELEASE").text
    driver_zip = requests.get(f"https://chromedriver.storage.googleapis.com/{latest}/chromedriver_win32.zip").content
    with open('temp/chromedriver_win32.zip', 'wb') as f:
        f.write(driver_zip)
    driver_zip = 'temp/chromedriver_win32.zip'
    with ZipFile(driver_zip, 'r') as zipObj:
        zipObj.extractall("C:\\bin")

    print(
        f"[{Fore.GREEN}+{Style.RESET_ALL}]Chromedriver {task} finished. Please run REQkit again. Auto-Exiting in 3 "
        f"seconds. "
    )
    time.sleep(1.5)


def login(user, passwd):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = Chrome("C:\\bin\\chromedriver", options=chrome_options)
    driver.get(login_url)

    un_field = (By.ID, "i0116")
    pw_field = (By.ID, "i0118")
    next_button = (By.ID, "idSIButton9")

    WebDriverWait(driver, 20).until(ec.presence_of_element_located(un_field)).send_keys(user)

    WebDriverWait(driver, 20).until(ec.element_to_be_clickable(next_button)).click()

    WebDriverWait(driver, 20).until(ec.element_to_be_clickable(pw_field)).send_keys(passwd)

    log_in = (By.XPATH, '//*[contains(@value, "Sign in")]')
    WebDriverWait(driver, 20).until(ec.presence_of_element_located(log_in)).click()

    return driver


def get_token(driver):
    store_url = "https://www.halowaypoint.com/en-us/games/halo-5-guardians/xbox-one/requisitions/store"
    driver.request("GET", store_url)
    try:
        token_element = driver.find_element_by_name("__RequestVerificationToken")
        return token_element.get_attribute("value")
    except selenium.common.exceptions.NoSuchElementException:
        print(
            f"[{Fore.RED}-{Style.RESET_ALL}] Failed to verify login with Xbox. Maybe Incorrect Password?")
        return "retry"


def generate_data(pack_name=None, check=False):
    for pack in db["packs"]:
        if pack[0] == pack_name:
            if not check:
                return pack
            else:
                return True

    return False


def buy_pack(driver, token, pack_name):
    data = generate_data(pack_name=pack_name)
    pack_full_name = data[1]
    price = data[2]
    request_data = data[3] + token

    while True:
        confirm_buy = input(f"[?] {pack_full_name} will be purchased for {price} REQ Points. Are you sure? (y/n)")
        if confirm_buy[0] == 'y':
            print(f"[{mdot}] Buying pack...")
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

            response = driver.request("POST", buy_url, headers=headers, data=request_data).content.decode()
            json_response = json.loads(response)
            try:
                if json_response["State"] is None:
                    print(f"[{Fore.GREEN}+{Style.RESET_ALL}] Success buying REQ Pack!")
                break
            except KeyError:
                if json_response["Message"] == "You do not have enough credits to purchase this":
                    print(f"[{Fore.RED}-{Style.RESET_ALL}] Error: Insufficient REQ Points Balance.")
                break
        elif confirm_buy[0] == 'n':
            print(f"[{mdot}] Exiting...")
            return
        else:
            continue


CONTEXT_SETTINGS = dict(help_option_names=['--usage'])


@click.command(options_metavar="<options>", context_settings=CONTEXT_SETTINGS)
@click.argument('pack-name', metavar="<REQ Pack Name|noarg>")
@click.option("--help", "-h", is_flag=True, help="More detailed help. Run 'reqkit.py -h noarg'")
@click.option(
    "--username", "-u", metavar="Email",
    help="The Microsoft/Xbox email associated with your Halo 5 Profile"
)
@click.option(
    "--password", "-p", metavar="Text",
    help="The Password for the associated Microsoft/Xbox email account."
)
def main(pack_name, help, username, password):
    """
    Buys 'REQ Packs' for the game "Halo 5: Guardians'.\n

    Minimal help display. Run '--help noarg', or '-h noarg' for more info
    """

    if help:
        print(
            f"Usage: reqkit.py [-u <username> -p <password>] <REQ Pack Name|Function>\n\nBuys 'REQ Packs' for 'Halo 5 "
            f"Guardians'.\n\nUse the 'sell' function to sell packs.\nThe REQ Pack Names are:\n{db['docstring']}"
        )
        sys.exit()

    if username is None or password is None:
        print(f"[{Fore.RED}-{Style.RESET_ALL}] Error: Both Username and Password Option need to be filled.")
        return

    if not generate_data(pack_name=pack_name, check=True):
        print(f"[{Fore.RED}-{Style.RESET_ALL}] Error: Invalid Pack Name")
        return

    print(f"[{mdot}] Logging in to Halo with email '{username}'...")
    second_try = False
    while True:
        try:
            driver = login(username, password)
        except selenium.common.exceptions.TimeoutException:
            print(
                f"[{Fore.RED}-{Style.RESET_ALL}] Failed to login with Xbox. Maybe Incorrect Username?")
            return

        print(f"[{mdot}] Verifying login with Xbox...")

        token = get_token(driver)
        if token != "retry":
            break
        else:
            if not second_try:
                print(f"[{mdot}] Retrying")
                second_try = True
                continue
            if second_try:
                print(f"[{Fore.RED}-{Style.RESET_ALL}] Retried login twice, but failed. Exiting...")
                return

    print(f"[{Fore.GREEN}+{Style.RESET_ALL}] Success Logging in!")

    # TODO: Add logic to determine whether a pack is being bought, or packs are being sold
    buy_pack(driver, token, pack_name)


if __name__ == '__main__':
    with open("resource/db.json") as f:
        db = json.load(f)

    with open("resource/logo") as f:
        print(f.read())

    print(f"{Fore.CYAN}REQkit Version {db['version']}-dev{Style.RESET_ALL}")
    print(f"{Fore.GREEN}A tool for purchasing REQ Packs using the undocumented Halo 5 API{Style.RESET_ALL}")
    print(
        f"{Fore.YELLOW}Run 'reqkit.py -h noarg' for help, or 'reqkit.py --usage' for command structure'"
        f"{Style.RESET_ALL}\n"
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

    try:
        main()
    except selenium.common.exceptions.SessionNotCreatedException:
        print("Chromedriver update required. Updating now...")
        update_driver("update")
    except selenium.common.exceptions.WebDriverException:
        print("Chromedriver is not installed. Installing now...")
        update_driver("installation")
    finally:
        time.sleep(2)

