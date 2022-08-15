import logging
import json
import datetime

from typing import Dict, List, Tuple

from selenium import webdriver
from selenium.webdriver.firefox.options import Options 
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.firefox import GeckoDriverManager


logger = logging.getLogger(__name__)

SCROLL_PAUSE_TIME = 0.5


class Scraper:
    website_for_scraping : str = None
    check_for_live_event : bool = False
    extracted_data : Dict[str, str] = None
    live_event : Tuple[str] = None

    def __init__(self) -> None:
        if self.website_for_scraping is None or (self.check_for_live_event and self.live_event is None):
            logger.warning("%s::__init__() One of the scraping defaults not specified", type(self).__name__)
            raise Exception("One of the scraping defaults not specified")

        firefox_options = Options()
        # firefox_options.add_argument("--headless")

        self.driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=firefox_options)
        logger.debug("Initialised the driver")
        self.timestamp = datetime.datetime.now(datetime.timezone.utc)
        self.current_year = datetime.datetime.now().year
        self.current_month = datetime.datetime.now().month
        self.current_day = datetime.datetime.now().day

    def get_website(self) -> None:
        """
        Navigate to the desired website in the current session and wait for it to load all of the betting content.
        """
        self.driver.get(self.website_for_scraping)
        self.driver.implicitly_wait(20)
        # timestamp when data was accessed
        logger.debug("%s::get_website() Website successfully loaded", type(self).__name__)

    def build_json_file(self) -> None:
        if self.extracted_data is None:
            logger.warning("%s::build_json_file() Can't build a json file without data being first extracted", type(self).__name__)
            raise Exception("Can't build a json file without data being first extracted")

        logger.debug("%s::build_json_file() Building a JSON file with provided data", type(self).__name__)
        with open("output.json", "w") as outfile:
            json.dump(self.extracted_data, outfile)

    def write_html_file_for_debugging(self) -> None:
        with open('betting_page.html', 'w') as f:
            f.write(self.driver.page_source)

class TennisScraper(Scraper):
    website_for_scraping = "https://sports.bwin.com/en/sports/tennis-5/betting"
    check_for_live_event = True
    location_of_bets_on_dom = (By.CSS_SELECTOR, "ms-event[class='grid-event ms-active-highlight ng-star-inserted']")
    live_event = (By.CSS_SELECTOR, "i[class='live-icon ng-star-inserted']")
    groups_of_tournaments = (By.CSS_SELECTOR, "ms-event-group[class='event-group collapsible ng-star-inserted']")

    def get_groups_of_tournaments(self) -> List[WebElement]:
        """
        This method grabs all the tournament groups.
        """
        if self.groups_of_tournaments is None:
            logger.warning("%s::get_groups_of_tournaments() Argument groups_of_tournaments is not specified", type(self).__name__)
            raise Exception("Argument groups_of_tournaments is not specified")
        logger.debug("%s::get_groups_of_tournaments()", type(self).__name__)
        return self.driver.find_elements(*self.groups_of_tournaments)

    def extract_match_data_from_the_tournament(self, tournament: WebElement) -> List[WebElement]:
        """
        Attempts to grab the elements containing bets and players info, from the currently loaded website. 
        """
        if self.location_of_bets_on_dom is None:
            logger.warning("%s::extract_match_data_from_the_tournament() Argument location_of_bets_on_dom is not specified", type(self).__name__)
            raise Exception("Argument location_of_bets_on_dom is not specified")
        logger.debug("%s::extract_match_data_from_the_tournament()", type(self).__name__)
        return tournament.find_elements(*self.location_of_bets_on_dom)

    def is_live(self, element: WebElement) -> bool:
        """
        Checks if the match is currently live. 
        """
        try:
            element.find_element(*self.live_event)
            logger.info("%s::is_live() Event match %s is live", type(self).__name__, element)
            return True
        except NoSuchElementException:
            logger.info("%s::is_live() Event match %s is not live", type(self).__name__, element)
            return False

    def extract_player_names_from_dom_element(self, match: WebElement) -> Dict[str, str]:
        """
        Extracts player names from the DOM for the given match. 
        """
        logger.debug("%s::extract_player_names_from_dom_element() ", type(self).__name__)
        name1, name2 = match.find_elements(By.CSS_SELECTOR, "div[class='participant']")
        return {
            "eventName": name1.text + ' vs ' + name2.text,
            "player1": name1.text,
            "player2": name2.text,
        }

    def extract_event_time(self, match: WebElement) -> Dict[str, str]:
        """
        Extracts event time from the DOM for the given match. 
        """
        logger.debug("%s::extract_event_time() ", type(self).__name__)
        time_of_match = match.find_element(By.CSS_SELECTOR, "ms-prematch-timer[class='starting-time timer-badge ng-star-inserted']")
        try:
            return {
                "eventDate": self.parse_string_time_into_utc_timezone(time_of_match.text)
            }
        except BaseException as e:
            print(f"error with this time {time_of_match.text}")
            print(e, type(e))
            raise e

    def extract_bets_from_dom_element(self, match: WebElement) -> Dict[str, str]:
        """
        Extracts bets from the DOM for the given match. 
        """
        try:
            logger.debug("%s::extract_bets_from_dom_element() ", type(self).__name__)
            time_of_match = match.find_elements(By.CSS_SELECTOR, "div[class='grid-group-container']")
            winning_bets = time_of_match[0]
            bets = winning_bets.find_elements(By.CSS_SELECTOR, "div[class='option option-value ng-star-inserted']")
            return {
                "player1_odds": bets[0].text,
                "player2_odds": bets[1].text
            }
        except IndexError:
            logger.warning("%s::extract_bets_from_dom_element() No available bets for this match", type(self).__name__)
            return None

    def extract_tournament_name_from_dom_element(self, tournament: WebElement) -> Dict[str, str]:
        """
        Extracts tournament name from the DOM for the given block of tournament games. 
        """
        logger.debug("%s::extract_tournament_name_from_dom_element() ", type(self).__name__)
        tournament_name = tournament.find_element(By.CSS_SELECTOR, "div[class='title']")
        return {
            "tournament": tournament_name.text
        }

    def parse_string_time_into_utc_timezone(self, game_time: str) -> str:
        """
        Parses string into a datetime object in UTC timezone 
        """
        logger.debug("%s::parse_string_time_into_utc_timezone() ", type(self).__name__)
        if 'Starting in' in game_time:
            time_difference = int(''.join(filter(str.isdigit, game_time)))
            return (self.timestamp + datetime.timedelta(minutes=time_difference)).strftime("%Y-%m-%d %H:%M")

        elif 'Today' in game_time:
            game_time = game_time.replace("Today / ", "").strip()
            date_string = f"{self.current_year}-{self.current_month}-{self.current_day} {game_time}"
            datetime_object = datetime.datetime.strptime(date_string, "%Y-%m-%d %I:%M %p")

            # account for UTC and takeaway an hour from the datetime
            utc_datetime_object = datetime_object - datetime.timedelta(hours=1)
            return utc_datetime_object.strftime("%Y-%m-%d %H:%M")
            
        elif 'Tomorrow' in game_time:
            game_time = game_time.replace("Tomorrow / ", "").strip()
            date_string = f"{self.current_year}-{self.current_month}-{self.current_day} {game_time}"
            datetime_object = datetime.datetime.strptime(date_string, "%Y-%m-%d %I:%M %p")

            # account for UTC and takeaway an hour from the datetime, but also add 24 hours to make it next day
            utc_datetime_object = datetime_object + datetime.timedelta(hours=23)
            return utc_datetime_object.strftime("%Y-%m-%d %H:%M")
        
        elif 'Starting now' in game_time:
            return None

        logger.warning("%s::parse_string_time_into_utc_timezone() time parser encountered unspecified timeslot", type(self).__name__)
        raise Exception("time parser encountered unspecified timeslot")

    def extract_data(self) -> None:
        """
        This function extracts data for all the matches.  
        """
        if not self.location_of_bets_on_dom:
            logger.warning("%s::extract_data() argument location_of_bets_on_dom unspecified", type(self).__name__)
            raise Exception("Argument location_of_bets_on_dom unspecified")
        array_of_dict = []
        tournaments = self.get_groups_of_tournaments()
        number_of_tournaments = len(tournaments)
        for tournament_counter, tournament in enumerate(tournaments):
            tournament_name = self.extract_tournament_name_from_dom_element(tournament)
            print(f"scraping tournament {tournament_counter + 1} out of {number_of_tournaments}")
            games = self.extract_match_data_from_the_tournament(tournament)
            games_number_for_tournament = len(games)
            for games_counter ,game in enumerate(games):
                print(f"scraping game {games_counter + 1} out of {games_number_for_tournament} in this tournament")
                if not self.is_live(game):
                    temp_dictionary = {}
                    
                    # If the game is starting now it means no bets can be made so we skip this game as well
                    event_time = self.extract_event_time(game)
                    if event_time is None:
                        continue

                    temp_dictionary.update(event_time)
                    temp_dictionary.update(self.extract_player_names_from_dom_element(game))
                    
                    # If there are not bets for a player we skip to the next game
                    game_bets = self.extract_bets_from_dom_element(game)
                    if game_bets is None:
                        continue

                    temp_dictionary.update(game_bets)
                    temp_dictionary.update(tournament_name)
                    if temp_dictionary:
                        temp_dictionary.update({"lastUpdate": self.timestamp.strftime("%Y-%m-%d %H:%M")})
                        array_of_dict.append(temp_dictionary)

        logger.info("%s::extract_data() Updating betting dataset", type(self).__name__)
        self.extracted_data = array_of_dict

        self.build_json_file()
