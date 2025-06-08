import pytest
import pandas as pd
from src.dutchie_scraper.scraper import scrape_dutchie

def test_scrape_dutchie_valid_url():
    url = "https://dutchie.com/dispensary/puff-monroe-rec/products/vaporizers"
    result = scrape_dutchie(url)
    assert isinstance(result, pd.DataFrame)
    assert not result.empty

def test_scrape_dutchie_invalid_url():
    url = "https://invalid-url.com"
    with pytest.raises(Exception):
        scrape_dutchie(url)

def test_scrape_dutchie_no_products():
    url = "https://dutchie.com/dispensary/puff-monroe-rec/products/no-products"
    result = scrape_dutchie(url)
    assert isinstance(result, pd.DataFrame)
    assert result.empty

def test_scrape_dutchie_edge_case():
    url = "https://dutchie.com/dispensary/puff-monroe-rec/products/vaporizers?page=1"
    result = scrape_dutchie(url)
    assert isinstance(result, pd.DataFrame)
    assert 'Prices' in result.columns