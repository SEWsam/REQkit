"""
Copyright (c) 2020 Samuel Wirth

Author: Samuel "SEWsam" Wirth
Version: 1.2
"""
import json
import sys
import click
import requests
import time

import selenium.common.exceptions
from colorama import Fore, Style, init

from zipfile import ZipFile
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from seleniumrequests import Chrome

init(convert=True)
mdot = u'\u00b7'

login_url = "https://login.live.com/oauth20_authorize.srf?client_id=000000004C0BD2F1&scope=xbox.basic+xbox" \
            ".offline_access&response_type=code&redirect_uri=https:%2f%2fwww.halowaypoint.com%2fauth%2fcallback" \
            "&locale=en-us&display=touch&state=https%253a%252f%252fwww.halowaypoint.com%252fen-us "

buy_url = "https://www.halowaypoint.com/en-us/games/halo-5-guardians/xbox-one/requisitions/buy-pack"


def update():
    latest = requests.get("https://chromedriver.storage.googleapis.com/LATEST_RELEASE").text
    driver_zip = requests.get(f"https://chromedriver.storage.googleapis.com/{latest}/chromedriver_win32.zip").content
    with open('temp/chromedriver_win32.zip', 'wb') as f:
        f.write(driver_zip)
    driver_zip = 'temp/chromedriver_win32.zip'
    with ZipFile(driver_zip, 'r') as zipObj:
        zipObj.extractall("C:\\bin")

    print("Chromedriver update finished. Please restart REQkit. Exiting in 1 second.")


def login(user, passwd):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = Chrome("C:\\bin\\chromedriver", options=chrome_options)
    driver.get(login_url)

    un_field = (By.ID, "i0116")
    pw_field = (By.ID, "i0118")
    next_button = (By.ID, "idSIButton9")

    WebDriverWait(driver, 20).until(EC.presence_of_element_located(un_field)).send_keys(user)

    WebDriverWait(driver, 20).until(EC.element_to_be_clickable(next_button)).click()

    WebDriverWait(driver, 20).until(EC.element_to_be_clickable(pw_field)).send_keys(passwd)

    log_in = (By.XPATH, '//*[contains(@value, "Sign in")]')
    WebDriverWait(driver, 20).until(EC.presence_of_element_located(log_in)).click()

    return driver


def get_token(driver):
    store_url = "https://www.halowaypoint.com/en-us/games/halo-5-guardians/xbox-one/requisitions/store"
    driver.request("GET", store_url)
    try:
        token_element = driver.find_element_by_name("__RequestVerificationToken")
        return token_element.get_attribute("value")
    except:
        print(
            f"[{Fore.RED}-{Style.RESET_ALL}] Failed to verify login with Xbox. Maybe Incorrect Password?")
        return "retry"


def generate_data(pack_name=None, token=None, check=False):
    if pack_name == 'xp-boost':
        if not check:
            return (
                "An 'Arena XP Boost Pack'",
                "150,000",
                "RequisitionPackId=3cf88495-70e9-4972-8809-22380b063f3d&ExpectedPrice=150000&__RequestVerificationToken"
                f"={token}"
            )
        else:
            return True
    elif pack_name == 'wz-xp-boost':
        if not check:
            return (
                "A Warzone XP Boost Pack",
                "150,000",
                "RequisitionPackId=38e0edae-786c-40a3-b020-cbd9d2ab9268&ExpectedPrice=150000&__RequestVerificationToken"
                f"={token}"
            )
        else:
            return True
    elif pack_name == 'bronze':
        if not check:
            return (
                "A Bronze Pack",
                "1250",
                "RequisitionPackId=5f96269a-58f8-473e-9897-42a4deb1bf09&ExpectedPrice=1250&__RequestVerificationToken"
                f"={token}"
            )
        else:
            return True
    elif pack_name == 'silver':
        if not check:
            return (
                "A Silver REQ Pack",
                "5,000",
                "RequisitionPackId=3ce05b60-a118-4ad1-9617-bc04f64ac4d8&ExpectedPrice=150000&__RequestVerificationToken"
                f"={token}"
            )
        else:
            return True
    elif pack_name == 'gold':
        if not check:
            return (
                "A Gold REQ Pack",
                "10,000",
                "RequisitionPackId=3a1614d9-20a4-4817-a189-88cb781e9152&ExpectedPrice=150000&__RequestVerificationToken"
                f"={token}"
            )
        else:
            return True
    elif pack_name == 'hcs':
        if not check:
            return (
                "An HCS REQ Pack",
                "80,000",
                "RequisitionPackId=0d7018ae-74f6-4b6a-b819-22022f82cd45&ExpectedPrice=150000&__RequestVerificationToken"
                f"={token}"
            )
        else:
            return True
    else:
        return False


@click.command(options_metavar="<options>")
@click.argument('pack-name', metavar="<REQ Pack Name>")
@click.option(
    "--username", "-u", metavar="Email",
    help="The Microsoft/Xbox email associated with your Halo 5 Profile"
)
@click.option(
    "--password", "-p", metavar="Text",
    help="The Password for the associated Microsoft/Xbox email account."
)
def main(pack_name, username, password):
    """
    Buys 'REQ Packs' for the game "Halo 5: Guardians'.\n
    In order for REQkit to work, you need to provide one argument and two
    options:


    Argument: REQ Pack name: The name of the REQ Pack to be bought.\n
    The Options are:\n
        * "bronze": A bronze REQ Pack.\n
        * "silver": A Silver REQ Pack. \n
        * "gold": A Gold REQ Pack\n
        * "hcs": An HCS Special REQ Pack.\n
        * "xp-boost": An Arena XP Boost Pack\n
        * "wz-xp-boost": A Warzone XP Boost Pack

    The options are below. Both are required.:
    """
    if username is None or password is None:
        print(f"[{Fore.RED}-{Style.RESET_ALL}] Error: Both Username and Password Option need to be filled.")
        sys.exit()

    if not generate_data(pack_name=pack_name, check=True):
        print(f"[{Fore.RED}-{Style.RESET_ALL}] Error: Invalid Pack Name")
        sys.exit()

    print(f"[{mdot}] Logging in to Halo with email '{username}'...")
    second_try = False
    while True:
        try:
            driver = login(username, password)
        except selenium.common.exceptions.TimeoutException:
            print(
                f"[{Fore.RED}-{Style.RESET_ALL}] Failed to login with Xbox. Maybe Incorrect Username?")
            sys.exit()

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
                sys.exit()

    print(f"[{Fore.GREEN}+{Style.RESET_ALL}] Success Logging in!")

    data = generate_data(pack_name=pack_name, token=token)
    pack_full_name = data[0]
    price = data[1]
    request_data = data[2]

    while True:
        confirm_buy = input(f"[?] {pack_full_name} will be purchased for {price} REQ Points. Are you sure? (y/n)")
        if confirm_buy[0] == 'y':
            print(f"[{mdot}] Buying pack...")
            headers = {
                'Connection': 'keep-alive',
                'Origin': 'https://www.halowaypoint.com',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36',
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
                    time.sleep(.5)
                break
            except KeyError:
                if json_response["Message"] == "You do not have enough credits to purchase this":
                    print(f"[{Fore.RED}-{Style.RESET_ALL}] Error: Insufficient REQ Points Balance.")
                break
        elif confirm_buy[0] == 'n':
            print(f"[{mdot}] Exiting...")
            time.sleep(.5)
            sys.exit()
        else:
            continue


if __name__ == '__main__':
    with open("dist/logo") as f:
        print(f.read())
    print(f"{Fore.CYAN}REQkit Version 1.2 (final){Style.RESET_ALL}")
    print(f"{Fore.GREEN}A tool for interacting with the undocumented Halo 5 REQ Pack API{Style.RESET_ALL}\n")
    try:
        main()
    except selenium.common.exceptions.SessionNotCreatedException:
        print("Chromedriver Update required. Updating now...")
        update()
