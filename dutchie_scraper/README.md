# Dutchie Scraper

This project is a Python package designed to scrape product data from Dutchie-based websites. It provides a simple interface to extract and return product information in a structured format.

## Installation

To install the Dutchie Scraper package, you can clone the repository and install the required dependencies using pip. Make sure you have Python 3.6 or higher installed.

```bash
git clone <repository-url>
cd dutchie_scraper
pip install -r requirements.txt
```

Alternatively, you can install it directly from the source:

```bash
pip install .
```

## Usage

To use the Dutchie Scraper, you need to import the `scrape_dutchie` function from the package and provide a URL of a Dutchie-based website. Here’s an example:

```python
from src.dutchie_scraper import scrape_dutchie

url = "https://dutchie.com/dispensary/puff-monroe-rec/products/vaporizers"
data = scrape_dutchie(url)

print(data)
```

## Functionality

The `scrape_dutchie(url)` function performs the following tasks:

1. Navigates to the specified URL.
2. Waits for the necessary elements to load.
3. Extracts network logs to find relevant product data.
4. Returns the product information as flat data.

## Contributing

Contributions are welcome! If you have suggestions for improvements or find bugs, please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.