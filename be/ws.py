import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re
import os
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Function to setup the browser
def setup_browser():
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

# Function to scrape flight data
def scrape_flights(origin, destination, departure_date, return_date):
    driver = setup_browser()
    url = f"https://www.kiwi.com/en/search/results/{origin}/{destination}/{departure_date}/{return_date}"
    driver.get(url)
    time.sleep(5)

    try:
        driver.find_element(By.XPATH, '//*[@id="cookies_accept"]').click()
    except Exception as e:
        print("Cookie accept button not found:", e)

    time.sleep(10)  # Wait for results to load
    try:
        load_more_button = driver.find_element(By.XPATH, '//button[contains(text(), "Load more")]')
        load_more_button.click()
        time.sleep(5)
    except Exception as e:
        print("Load more button not found:", e)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    flights = []
    for flight in soup.find_all('div', {'data-test': 'ResultCardWrapper'}):
        try:
            airline = flight.find('div', {'class': 'orbit-carrier-logo'}).find('img')['title']
            times = flight.find_all('div', {'data-test': 'TripTimestamp'})
            price = flight.find('div', {'data-test': 'ResultCardPrice'}).find('span').text.strip()
            flight_info = {
                'airline': airline,
                'departure_time': times[0].text.strip() if len(times) > 0 else 'N/A',
                'arrival_time': times[1].text.strip() if len(times) > 1 else 'N/A',
                'price': re.sub(r'[^\d]', '', price)
            }
            flights.append(flight_info)
        except Exception as e:
            print("Error scraping flight data:", e)

    driver.quit()
    return flights

# Save data to CSV
def save_to_csv(flights):
    file_name = 'flights.csv'
    file_exists = os.path.exists(file_name)
    with open(file_name, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['airline', 'departure_time', 'arrival_time', 'price'])
        if not file_exists:
            writer.writeheader()
        writer.writerows(flights)

# Flask route to handle scraping
@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.json
    origin = data.get('origin')
    destination = data.get('destination')
    departure_date = data.get('departure_date')
    return_date = data.get('return_date')

    if not all([origin, destination, departure_date, return_date]):
        return jsonify({'success': False, 'error': 'Missing required parameters.'}), 400

    flights = scrape_flights(origin, destination, departure_date, return_date)
    if flights:
        save_to_csv(flights)
        return jsonify({'success': True, 'flights': flights})
    return jsonify({'success': False, 'error': 'No flights found.'})

if __name__ == "__main__":
    app.run(debug=True)
