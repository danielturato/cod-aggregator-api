import asyncio
from datetime import datetime, timedelta

import motor.motor_asyncio
import pytz
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver

from app.models.tournament_models import QueryStatus, TournamentSite, Tournament
from app.config import Settings
from bs4 import BeautifulSoup
from fastapi.encoders import jsonable_encoder


async def load_driver(settings: Settings):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--headless")
    chrome_options.binary_location = settings.google_chrome_bin

    return webdriver.Chrome(executable_path=settings.chromedriver_path, chrome_options=chrome_options)


def scrape_cmg(session_id, new_status: QueryStatus, cmg_url):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(scrape_cmg_async(session_id, new_status, cmg_url))


async def scrape_cmg_async(session_id: str, new_status: QueryStatus, cmg_url):
    async def get_tournament(t):
        block = t.find("div", class_="tournament-box")
        details = block.find("div", class_="tournament-details")
        desc = details.find("div", class_="tournament-description-block")
        prize_block = details.find("div", class_="prize-block")
        prize = prize_block.find("p")
        stats = details.find("div", class_="tournament-stats-block")
        name_c = desc.find("div", class_="name-block")
        region_block = desc.find("div", class_="region-content")
        timer = region_block.find("span", class_="countdown-timer")
        real_date = region_block.find("span", class_="start-date")
        timer_block = timer.find_all("span")
        name = name_c.find("p", class_="tournament-name")

        link_block = block.find("div", class_="view-button-container")
        link = link_block.find("a", href=True)

        stats_divs = stats.find_all("div", class_="tournament-stats")

        if not real_date:
            starts_in = timer_block[1].text
            mins = int(starts_in.split("M")[0])
            secs = int(starts_in.split(" ")[1].replace("S", ""))

            d_t = datetime.now().replace(tzinfo=pytz.timezone("GMT"))
            d_t = (d_t + timedelta(minutes=mins, seconds=secs)).timestamp()
        else:
            d_t = datetime.strptime(real_date.text.replace("EST", "").strip(), "%b %d, %I:%M %p").replace(
                tzinfo=pytz.timezone("US/Eastern"), year=2021).timestamp()

        return Tournament(site=TournamentSite.cmg, name=name.text, url=settings.base_cmg_url + link['href'],
                          region=stats_divs[2].find("p").text.strip(), prize=prize.text, start_time=d_t)

    settings = Settings()
    db = motor.motor_asyncio.AsyncIOMotorClient(settings.mongodb_url).vanguard_db
    browser = await load_driver(settings)
    if (tournament_q := await db["tournaments"].find_one({"session_id": session_id})) is not None:

        soup = None
        browser.get(cmg_url)
        try:
            WebDriverWait(browser, 5).until(
                EC.presence_of_element_located((By.ID, "competition-lobby-tournaments-container"))
            )
            soup = BeautifulSoup(browser.page_source, "html.parser")
        finally:
            browser.close()

        if not soup:
            raise Exception("Page didn't load :(")

        tournaments_container = soup.find(id="competition-lobby-tournaments-container")
        tournament_divs = tournaments_container.find_all("div", class_="padding-tournament")

        tournaments = []

        for t in tournament_divs:
            tournaments.append(jsonable_encoder(await get_tournament(t)))

        tournament_q["tournaments"].extend(tournaments)
        tournament_q["status"] = new_status
        update_res = \
            await db["tournaments"].update_one({"_id": tournament_q["_id"]}, {"$set": tournament_q})
