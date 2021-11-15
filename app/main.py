from fastapi import FastAPI, status

from app.routers import tournaments

import uvicorn

# PROFILE = os.getenv('API_PROFILE', 'DEV')
# GOOGLE_CHROME_BIN = os.getenv('GOOGLE_CHROME_BIN', '/app/.apt/opt/google/chrome/google-chrome')
# CHROMEDRIVER_PATH = os.getenv('CHROMEDRIVER_PATH', '/app/.chromedriver/bin/chromedriver')
#
# BASE_CMG_URL = "https://www.checkmategaming.com"
# CMG_GAME_PATH = BASE_CMG_URL + os.getenv('CMG_GAME_PATH', '/tournament/cross-platform/call-of-duty-vanguard')
# BASE_GB_URL = "https://gamebattles.majorleaguegaming.com/tournaments"
# BASE_UMG_URL = "https://www.umggaming.com/g"
# UMG_GAME_PATH = BASE_UMG_URL + os.getenv('UMG_GAME_PATH', '/vanguard/tournaments')
# origins = [
#     "https://laughing-fermi-342ce1.netlify.app/",
#     "https://findcodtourneys.com/", "https://www.findcodtourneys.com/"
# ]
#
# app = FastAPI()
#
#
# class Tournament:
#     def __init__(self, name, link, region, prize, start_time, site):
#         self.site = site
#         self.name = name
#         self.link = link
#         self.region = region
#         self.prize = prize
#         self.start_time = start_time
#
#     def __str__(self) -> str:
#         return f'name={self.name},link={self.link},region={self.region},prize={self.prize},start_time={self.start_time}'
#
#
# async def load_driver():
#     chrome_options = webdriver.ChromeOptions()
#     if PROFILE == 'PROD':
#         chrome_options.add_argument('--disable-gpu')
#         chrome_options.add_argument('--no-sandbox')
#         chrome_options.add_argument("--remote-debugging-port=9222")
#         chrome_options.add_argument("--headless")
#         chrome_options.binary_location = GOOGLE_CHROME_BIN
#
#     return webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, chrome_options=chrome_options) \
#         if PROFILE == 'PROD' else webdriver.Chrome()
#
#
# async def build_cmg_url(team_size, regions):
#     url_query_build = urlparse(CMG_GAME_PATH)
#     queries = urlencode({**team_size, **regions})
#     return url_query_build._replace(query=queries).geturl()
#
#
# async def scrape_cmg(browser, team_size=None, regions=None):
#     if regions is None:
#         regions = dict(region="global,na_eu,eu,na")
#     if team_size is None:
#         team_size = dict(team="all")
#     cmg_url = await build_cmg_url(team_size, regions)
#
#     browser.get(cmg_url)
#     time.sleep(2)
#     html_source = browser.page_source
#
#     soup = BeautifulSoup(html_source, "html.parser")
#
#     tournaments_container = soup.find(id="competition-lobby-tournaments-container")
#     tournament_divs = tournaments_container.find_all("div", class_="padding-tournament")
#
#     tournaments = []
#
#     for t in tournament_divs:
#         block = t.find("div", class_="tournament-box")
#         details = block.find("div", class_="tournament-details")
#         desc = details.find("div", class_="tournament-description-block")
#         cover = details.find("div", class_="tournament-cover-block")
#         prize_block = details.find("div", class_="prize-block")
#         prize = prize_block.find("p")
#         stats = details.find("div", class_="tournament-stats-block")
#         name_c = desc.find("div", class_="name-block")
#         region_block = desc.find("div", class_="region-content")
#         timer = region_block.find("span", class_="countdown-timer")
#         real_date = region_block.find("span", class_="start-date")
#         timer_block = timer.find_all("span")
#         name = name_c.find("p", class_="tournament-name")
#
#         link_block = block.find("div", class_="view-button-container")
#         link = link_block.find("a", href=True)
#
#         stats_divs = stats.find_all("div", class_="tournament-stats")
#
#         if not real_date:
#             starts_in = timer_block[1].text
#             mins = int(starts_in.split("M")[0])
#             secs = int(starts_in.split(" ")[1].replace("S", ""))
#
#             d_t = datetime.now().replace(tzinfo=pytz.timezone("GMT"))
#             d_t = (d_t + timedelta(minutes=mins, seconds=secs)).timestamp()
#         else:
#             d_t = datetime.strptime(real_date.text.replace("EST", "").strip(), "%b %d, %I:%M %p").replace(
#                 tzinfo=pytz.timezone("US/Eastern"), year=2021).timestamp()
#
#         tournaments.append(
#             Tournament(name.text, BASE_CMG_URL + link['href'], stats_divs[2].find("p").text.strip(), prize.text,
#                        d_t, "CMG"))
#
#     return tournaments
#
#
# async def scrape_gb(browser, team_size=None, region=None):
#     if not team_size:
#         team_size = []
#
#     if not region:
#         region = "all"
#
#     import time
#
#     browser.get(BASE_GB_URL)
#     games = browser.find_elements_by_class_name("game-box")
#     not_found = True
#     while not_found:
#         not_found = False
#         try:
#             time.sleep(1)
#             games[1].click()
#         except:
#             not_found = True
#
#     time.sleep(2)
#     html_source = browser.page_source
#
#     soup = BeautifulSoup(html_source, "html.parser")
#     page = soup.find("gb-tournaments")
#     t_container = page.find("gb-layout")
#     tournaments_block = t_container.find("div").find_all("div")[1].find("gb-layout-content")
#     unwanted = tournaments_block.find("gb-game-filter")
#     unwanted.extract()
#
#     tournaments_cards = tournaments_block.find("div").find_all("gb-tournament-card")
#
#     ts = []
#     for t in tournaments_cards:
#         first_div = t.find("div")
#         second_div = first_div.find("div")
#         info_divs = second_div.find_all("div")
#
#         title = second_div.find("div", class_="title").text
#         prize = info_divs[6].text
#
#         t_region = info_divs[11].find("div").text
#
#         gb_time = info_divs[9].find("div").text
#         datet = datetime.strptime(gb_time.replace("UTC", "").replace("EST", "").replace("GMT", "").strip(),
#                                   "%a %b %d @ %I:%M %p").replace(tzinfo=pytz.timezone("UTC"), year=2021).timestamp()
#
#         ts.append(
#             Tournament(title, "https://gamebattles.majorleaguegaming.com/tournaments", t_region, prize, datet, "GB", ))
#
#     filtered_ts = [t for t in ts if region != "all" and t.region == region]
#     filtered_ts_new = []
#     for t in filtered_ts:
#         add = True
#         for s in team_size:
#             if s in t.name:
#                 add = False
#                 break
#         if add:
#             filtered_ts_new.append(t)
#
#     return filtered_ts_new
#
#
# async def scrape_umg(browser, team_size=None, region=None):
#     if not team_size:
#         team_size = []
#
#     if not region:
#         region = "all"
#
#     def filter_by_size(t):
#         for s in team_size:
#             if s == t.name:
#                 return False
#         return True
#
#     browser.get(UMG_GAME_PATH)
#     time.sleep(2)
#     html_source = browser.page_source
#
#     soup = BeautifulSoup(html_source, "html.parser")
#     upcoming_section = soup.find_all('div', class_="game-section mobile-margin-section")[1]
#     ts = upcoming_section.find_all('div', class_="tournament-tile-container col-12")
#     res = []
#
#     for t in ts:
#         prize = t.find('div', class_="prize-holder").text
#         sections = t.find_all('div', class_="container-fluid")
#         name = sections[1].find('div', class_="col-12").text
#         start_time = sections[2].find('div', class_="__react_component_tooltip").find('div').text
#         d_t = datetime.strptime(start_time.replace("UTC", "").replace("EST", "").replace("GMT", "").strip(),
#                                 "%Y-%m-%d %I:%M %p").replace(
#             tzinfo=pytz.timezone("GMT")).timestamp()
#
#         # size = sections[2].find('div', class_="col-sm-3 col-3").find('div', class_="data-item").text
#         t_reg = sections[2].find('div', class_="col-sm-3 col-2").find('div', class_="data-item").text
#
#         res.append(Tournament(name, UMG_GAME_PATH, t_reg, prize, d_t, "UMG"))
#
#     filtered_ts = []
#     for t in res:
#         add = True
#         for s in team_size:
#             if s in t.name:
#                 add = False
#                 break
#         if add:
#             filtered_ts.append(t)
#
#     filtered_ts_new = [t for t in filtered_ts if region != "all" and t.region == region]
#
#     return filtered_ts_new
#
#
# async def gb_team_size(team_sizes):
#     default_sizes = ["1v1", "2v2", "3v3", "4v4"]
#
#     for s in team_sizes:
#         if s == "1":
#             default_sizes.remove("1v1")
#         elif s == "2":
#             default_sizes.remove("2v2")
#         elif s == "3":
#             default_sizes.remove("3v3")
#         elif s == "4":
#             default_sizes.remove("4v4")
#
#     return default_sizes
#
#
# async def cmg_team_size(team_sizes):
#     if team_sizes == ["1", "2", "3", "4"]:
#         return dict(team="all")
#
#     t_s = []
#     for s in team_sizes:
#         if s == "1":
#             t_s.append("solo")
#         elif s == "2":
#             t_s.append("duo")
#         elif (s == "3" or s == "4") and "squad" not in t_s:
#             t_s.append("squad")
#
#     t_s = ",".join(t_s)
#
#     return dict(team=t_s)
#
#
# @app.get("/tournaments")
# async def tournaments(team_sizes: str, region: str):
#     for c in team_sizes:
#         if c not in "1234,":
#             return {}
#
#     if region not in ["na", "eu", "na_eu"]:
#         return {}
#
#     team_sizes = team_sizes.split(',')
#
#     gb_team_sizes = umg_team_sizes = await gb_team_size(team_sizes)
#     cmg_team_sizes = await cmg_team_size(team_sizes)
#
#     res = []
#     gb_region = "POOP"
#     if region == "eu":
#         gb_region = "Europe"
#     elif region == "na":
#         gb_region = "USA"
#     cmg_region = "all"
#     if region == "eu":
#         cmg_region = "eu"
#     elif region == "na":
#         cmg_region = "na"
#     else:
#         cmg_region = "na_eu"
#
#     umg_region = "all"
#     if region == "eu":
#         umg_region = "EU"
#     elif region == "na":
#         umg_region = "NA"
#     elif region == "na_eu":
#         umg_region = "NA+EU"
#
#     browser = await load_driver()
#     res.extend(await scrape_cmg(browser, team_size=cmg_team_sizes, regions=dict(region=cmg_region)))
#     res.extend(await scrape_gb(browser, team_size=gb_team_sizes, region=gb_region))
#     # res.extend(await scrape_umg(browser, team_size=umg_team_sizes, region=umg_region))
#
#     browser.quit()
#
#     res.sort(key=lambda t: t.start_time)
#
#     return res
#
#
# app = CORSMiddleware(
#     app=app,
#     allow_origins=["https://findcodtourneys.com"],
#     allow_methods=["*"],
#     allow_headers=["*"])

app = FastAPI()
app.include_router(tournaments.router)


@app.get("/health", status_code=status.HTTP_200_OK)
async def get_health():
    return {'healthcheck': 'healthy'}


# if __name__ == '__main__':
#     uvicorn.run("app.main:app", host='0.0.0.0', port=4557, reload=True, debug=True, workers=3)
