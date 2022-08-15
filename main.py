#!/usr/bin/env python3
from scraper import TennisScraper


if __name__ == "__main__":
    scraper = TennisScraper()
    scraper.get_website()
    scraper.extract_data()
