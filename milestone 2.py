import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from organizer import organize_downloaded_files
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# Set up Chrome options and preferences
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("user-agent = your user agent")

download_dir = "downloads"
if not os.path.exists(download_dir):
    os.makedirs(download_dir)

# Set Chrome preferences for downloading files
prefs = {
    "download.default_directory": os.path.abspath(download_dir),
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
chrome_options.add_experimental_option("prefs", prefs)

service = Service('chromedriver.exe')

try:
    driver = webdriver.Chrome(service=service, options=chrome_options)
except WebDriverException as e:
    print(f"Error initializing the WebDriver: {str(e)}")
    exit(1)

# Wait for download completion by checking for .crdownload files
def wait_for_downloads(timeout=30):
    seconds = 0
    while seconds < timeout:
        if not any([filename.endswith(".crdownload") for filename in os.listdir(download_dir)]):
            return
        time.sleep(1)
        seconds += 1
    print("Timeout reached while waiting for downloads to complete.")

# Function to attempt download with retries
def download_with_retry(url, max_retries=3):
    attempts = 0
    while attempts < max_retries:
        try:
            print(f"Attempting to download from {url} (Attempt {attempts + 1}/{max_retries})")
            driver.get(url)
            wait_for_downloads()
            return True  # Return if download succeeds
        except (TimeoutException, WebDriverException) as e:
            print(f"Download attempt {attempts + 1} failed for {url}: {str(e)}")
            attempts += 1
            time.sleep(2)  # Short delay before retrying
    print(f"Failed to download from {url} after {max_retries} attempts.")
    return False  # Return if all attempts fail

try:
    driver.get("https://www.nseindia.com/all-reports")  
    time.sleep(10)

    # Locate the reports div and download the files
    try:
        report_div = driver.find_element(By.XPATH, "//div[@id='cr_equity_daily_Current']")
        report_divs = report_div.find_elements(By.XPATH, ".//div[contains(@class, 'reportsDownload')]")
    except NoSuchElementException:
        print("Error: Unable to locate report div. Please check the page structure.")
        driver.quit()
        exit(1)

    for report in report_divs:
        data_link = report.get_attribute("data-link")
        print(f"Downloading from: {data_link}")
        
        # Attempt download with retry logic
        if download_with_retry(data_link):
            organize_downloaded_files(download_dir)
        else:
            print(f"Skipping download for {data_link} after failed retries.")

finally:
    try:
        driver.quit()
    except Exception as e:
        print(f"Error closing the WebDriver: {str(e)}")