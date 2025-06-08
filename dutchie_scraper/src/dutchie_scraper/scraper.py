def scrape_dutchie(url):
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

    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )

    driver.get(url)

    def extract_logs(driver):
        logs_raw = driver.get_log("performance")
        logs = [json.loads(lr["message"])["message"] for lr in logs_raw]

        def log_filter(log_):
            return (
                log_["method"] == "Network.responseReceived"
                and "json" in log_["params"]["response"]["mimeType"]
            )

        urls = []
        responses = []
        for log in filter(log_filter, logs):
            try:
                request_id = log["params"]["requestId"]
                resp_url = log["params"]["response"]["url"]
                if 'https://dutchie.com/api-3/graphql?operationName=FilteredProducts&variables' in resp_url:
                    urls.append(resp_url)
                    response = driver.execute_cdp_cmd(
                        "Network.getResponseBody", {"requestId": request_id}
                    )
                    responses.append(response)
            except Exception as e:
                print(f"Error processing log entry: {e}")
        return urls, responses

    try:
        element = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/div[3]/div[2]/div[1]/button"))
        )
        element.click()

        time.sleep(10)
        urls, responses = extract_logs(driver)

        if responses:
            first_response = json.loads(responses[0]["body"])
            pages = first_response["data"]["filteredProducts"]["queryInfo"]["totalPages"]

            all_products = []

            for _ in range(pages - 1):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                next_button = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//button[@aria-label='go to next page' and contains(@class, 'pagination-controls__NavButton')]")
                    )
                )
                actions = ActionChains(driver)
                actions.move_to_element(next_button).perform()
                next_button.click()

                time.sleep(5)
                more_urls, more_responses = extract_logs(driver)
                urls.extend(more_urls)
                responses.extend(more_responses)

            for response in responses:
                try:
                    parsed_body = json.loads(response["body"])
                    products = parsed_body["data"]["filteredProducts"]["products"]
                    all_products.extend(products)
                except KeyError as e:
                    print(f"KeyError: {e} in response: {response}")
                except json.JSONDecodeError as e:
                    print(f"JSONDecodeError: {e} in response: {response}")

            flat_data = json_normalize(all_products, sep='_')
            flat_data = (flat_data
                         .assign(Prices=flat_data['Prices'].str[0],
                                 updatedAt=pd.to_datetime(flat_data['updatedAt']),
                                 createdAt=pd.to_datetime(flat_data['createdAt'], unit='ms'),
                                 POSMetaData_children=flat_data['POSMetaData_children'].apply(lambda x: x[0]),
                                 scrapeDate=pd.Timestamp.now().strftime("%Y-%m-%d")))

            expanded_pos_data = json_normalize(flat_data['POSMetaData_children'], sep='_')
            flat_data = pd.concat([flat_data.drop(columns=['POSMetaData_children']), expanded_pos_data], axis=1)

            return flat_data.drop(columns=['_id'])

    finally:
        driver.quit()