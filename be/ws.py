import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re
import os

# Function to setup the browser
def setup_browser():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode (no UI)
    driver = webdriver.Chrome()
    return driver

# Function to scrape flight data from Kiwi.com
def scrape_flights(origin, destination, departure_date, return_date):
    # Set up the browser and navigate to Kiwi.com
    driver = setup_browser()

    # Navigate to the Kiwi flight search page
    url = f"https://www.kiwi.com/en/search/results/{origin}/{destination}/{departure_date}/{return_date}"
    driver.get(url)

    # Wait for the page to load
    time.sleep(5)

    # Click the search button (use sleep to wait for the page to load results)
    driver.find_element(By.XPATH, '//*[@id="cookies_accept"]').click()
    time.sleep(10)

    for _ in range(2):
        try:
            load_more_button = driver.find_element(By.XPATH, '//*[@id="react-view"]/div[2]/div[4]/div/div/div/div/div/div[3]/div/div/div[4]/div/div/button/div')
            load_more_button.click()
            time.sleep(5)  # Wait for the next set of results to load
        except Exception as e:
            print("Could not find the 'Load more' button:", e)
            break

    # Parse the page with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Scrape the flight data (adjust the tags as needed for better accuracy)
    flights = []
    for flight in soup.find_all('div', {'data-test': 'ResultCardWrapper'}):  # Adjust the class name if necessary
        try:
            flight_info = {}

            # Airline
            airline = flight.find('div', {'class': 'orbit-carrier-logo'}).find('img')['title']
            print(airline)
            flight_info['airline'] = airline
            times = flight.find_all('div', {'data-test': 'TripTimestamp'})
            if len(times) >= 4:
                # Ensure we have at least 4 timestamps (departure, arrival, return departure, return arrival)
                flight_info['departure_time'] = times[0].find('time').text.strip() if times[0] else 'N/A'
                flight_info['arrival_time'] = times[1].find('time').text.strip() if times[1] else 'N/A'
                flight_info['return_departure_time'] = times[2].find('time').text.strip() if times[2] else 'N/A'
                flight_info['return_arrival_time'] = times[3].find('time').text.strip() if times[3] else 'N/A'
            # Price
            price = flight.find('div', {'data-test': 'ResultCardPrice'}).find('span').get_text(strip=True)
            priceFIN = re.sub(r'[^\d]', '', price)
            flight_info['price'] = (int) (priceFIN)

            flights.append(flight_info)
        except Exception as e:
            print(f"Error parsing a flight: {e}")

    # Close the browser
    driver.quit()

    return flights

# Function to save data to CSV
def save_to_csv(flight_data):
    file_name = 'flights.csv'
    file_exists = os.path.exists(file_name)
    
    # Open CSV file in append mode
    with open(file_name, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['airline', 'departure_time', 'arrival_time', 'return_departure_time', 'return_arrival_time', 'price'])
        
        # Write the header only if the file does not exist
        if not file_exists:
            writer.writeheader()
        
        # Write flight data
        writer.writerows(flight_data)

# Main function to input user data and scrape
def main():
    # Take input from the user
    origin = 'berlin-germany'
    destination = 'paris-france'
    departure_date = '2024-12-15'
    return_date = '2024-12-22'

    # Scrape the flight data
    flights = scrape_flights(origin, destination, departure_date, return_date)

    # If flights are found, save them to CSV
    if flights:
        save_to_csv(flights)
    else:
        print("No flights found.")

if __name__ == "__main__":
    main()