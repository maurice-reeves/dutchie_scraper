def scrape_dutchie(url_or_urls):
    import time
    import json
    import pandas as pd
    from pandas import json_normalize
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.action_chains import ActionChains

    # Helper: Safe page load with retry
    def safe_get(driver, url, retries=3, delay=5):
        for attempt in range(retries):
            try:
                driver.get(url)
                return True
            except Exception as e:
                print(f"Network error on {url}, retry {attempt+1}/{retries}: {e}")
                time.sleep(delay)

        # If we get here, all retries failed → stop everything
        raise ConnectionError(f"Network unavailable after {retries} attempts for {url}")

    # Scrape a single category
    def scrape_single(driver, url):
        safe_get(driver, url)  # will raise if network unavailable

        def extract_logs(driver):
            logs_raw = driver.get_log("performance")
            logs = [json.loads(lr["message"])["message"] for lr in logs_raw]

            def log_filter(log_):
                return (
                    log_["method"] == "Network.responseReceived"
                    and "json" in log_["params"]["response"]["mimeType"]
                )

            urls, responses = [], []
            for log in filter(log_filter, logs):
                try:
                    request_id = log["params"]["requestId"]
                    resp_url = log["params"]["response"]["url"]
                    if "operationName=FilteredProducts&variables" in resp_url:
                        urls.append(resp_url)
                        response = driver.execute_cdp_cmd(
                            "Network.getResponseBody", {"requestId": request_id}
                        )
                        responses.append(response)
                except Exception as e:
                    print(f"Error processing log entry: {e}")
            return urls, responses

        try:
            # Handle cookie consent if present
            try:
                element = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/div[3]/div[2]/div[1]/button"))
                )
                element.click()
                time.sleep(2)
            except Exception:
                pass

            time.sleep(5)
            urls, responses = extract_logs(driver)

            if not responses:
                return pd.DataFrame()

            first_response = json.loads(responses[0]["body"])
            pages = first_response["data"]["filteredProducts"]["queryInfo"]["totalPages"]

            all_products = []

            # Loop through pages
            for _ in range(pages - 1):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                try:
                    next_button = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located(
                            (By.XPATH, "//button[@aria-label='go to next page' and contains(@class, 'pagination-controls__NavButton')]")
                        )
                    )
                    ActionChains(driver).move_to_element(next_button).perform()
                    next_button.click()
                    time.sleep(5)
                    more_urls, more_responses = extract_logs(driver)
                    urls.extend(more_urls)
                    responses.extend(more_responses)
                except Exception as e:
                    print(f"Pagination error on {url}: {e}")
                    break

            for response in responses:
                try:
                    parsed_body = json.loads(response["body"])
                    products = parsed_body["data"]["filteredProducts"]["products"]
                    all_products.extend(products)
                except Exception as e:
                    print(f"Error parsing response: {e}")

            if not all_products:
                return pd.DataFrame()

            flat_data = json_normalize(all_products, sep="_")
            flat_data = (
                flat_data
                .assign(
                    Prices=flat_data["Prices"].str[0],
                    updatedAt=pd.to_datetime(flat_data["updatedAt"]),
                    createdAt = pd.to_datetime(pd.to_numeric(flat_data["createdAt"]), unit="ms"),
                    POSMetaData_children=flat_data["POSMetaData_children"].apply(lambda x: x[0] if isinstance(x, list) and x else None),
                    scrapeDate=pd.Timestamp.now().strftime("%Y-%m-%d"),
                    url=url
                )
            )

            if "POSMetaData_children" in flat_data:
                expanded_pos_data = json_normalize(flat_data["POSMetaData_children"], sep="_")
                expanded_pos_data = expanded_pos_data.add_prefix("POSMetaData_children_")
                flat_data = pd.concat([flat_data.drop(columns=["POSMetaData_children"]), expanded_pos_data], axis=1)

            return flat_data.drop(columns=["_id"], errors="ignore")

        except Exception as e:
            print(f"Scraping error for {url}: {e}")
            return pd.DataFrame([{
                "url": url,
                "scrapeDate": pd.Timestamp.now().strftime("%Y-%m-%d"),
                "error": str(e)
            }])

    # Main scraping logic
    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        categories = ["pre-rolls", "flower", "vaporizers", "edibles", "concentrates", "tinctures", "topicals"]
        all_results = []

        if isinstance(url_or_urls, list):
            for idx, dispensary_url in enumerate(url_or_urls):
                print(f"\nScraping dispensary {idx+1}/{len(url_or_urls)}: {dispensary_url}")
                for category in categories:
                    product_url = f"{dispensary_url}/products/{category}"
                    print(f"  Scraping: {product_url}")
                    df = scrape_single(driver, product_url)
                    if not df.empty:
                        df["dispensary"] = dispensary_url
                        df["category"] = category
                        all_results.append(df)
                        print(f"{len(df)} items scraped")
                    else:
                        print(f"No data for {category}")
            return pd.concat(all_results, ignore_index=True) if all_results else pd.DataFrame()

        else:
            # Single URL: treat the passed value as the dispensary URL
            dispensary_url = url_or_urls
            print(f"\nScraping dispensary: {dispensary_url}")
            for category in categories:
                product_url = f"{dispensary_url}/products/{category}"
                print(f"  Scraping: {product_url}")
                df = scrape_single(driver, product_url)
                if not df.empty:
                    df["dispensary"] = dispensary_url
                    df["category"] = category
                    all_results.append(df)
                    print(f"{len(df)} items scraped")
                else:
                    print(f"No data for {category}")
            return pd.concat(all_results, ignore_index=True) if all_results else pd.DataFrame()

    except ConnectionError as ce:
        print(f"Fatal error: {ce}")
        return pd.concat(all_results, ignore_index=True) if all_results else pd.DataFrame()

    finally:
        driver.quit()
