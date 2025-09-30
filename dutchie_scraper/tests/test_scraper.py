import pytest
import pandas as pd
from dutchie_scraper.scraper import scrape_dutchie
from unittest.mock import patch

def test_scrape_dutchie_valid_url():
    url = "https://dutchie.com/dispensary/puff-monroe-rec"
    result = scrape_dutchie(url)
    assert isinstance(result, pd.DataFrame)
    assert not result.empty

def test_scrape_dutchie_valid_multiple_urls():
    urls = [
        "https://dutchie.com/dispensary/puff-monroe-rec",
        "https://dutchie.com/dispensary/nobo-denver"
    ]
    result = scrape_dutchie(urls)
    assert isinstance(result, pd.DataFrame)
    assert not result.empty
    assert len(result) > 0

def test_scrape_dutchie_invalid_url():
    url = "https://invalid-url.com"
    result = scrape_dutchie(url)
    assert result.empty
    

def test_scrape_dutchie_edge_case():
    url = "https://dutchie.com/dispensary/puff-monroe-rec"
    result = scrape_dutchie(url)
    assert isinstance(result, pd.DataFrame)
    assert 'Prices' in result.columns