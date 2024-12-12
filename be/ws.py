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
from datetime import date

app = Flask(__name__)
CORS(app)


def setup_browser():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def scrape_flights(origin, destination, departure_date, return_date):
    driver = setup_browser()

    url = f"https://www.kiwi.com/en/search/results/{origin}/{destination}/{departure_date}/{return_date}"
    driver.get(url)

    time.sleep(5)

    driver.find_element(By.XPATH, '//*[@id="cookies_accept"]').click()
    time.sleep(20)

    for _ in range(2):
        try:
            load_more_button = driver.find_element(By.XPATH, '//*[@id="react-view"]/div[2]/div[4]/div/div/div/div/div/div[3]/div/div/div[5]/div/div/button')
            load_more_button.click()
            time.sleep(5)
        except Exception as e:
            print("Could not find the 'Load more' button:", e)
            break

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    flights = []
    for flight in soup.find_all('div', {'data-test': 'ResultCardWrapper'}):
        try:
            flight_info = {}

            airline = flight.find('div', {'class': 'orbit-carrier-logo'}).find('img')['title']
            print(airline)
            flight_info['airline'] = airline
            times = flight.find_all('div', {'data-test': 'TripTimestamp'})
            if len(times) >= 4:
                flight_info['departure_time'] = times[0].find('time').text.strip() if times[0] else 'N/A'
                flight_info['arrival_time'] = times[1].find('time').text.strip() if times[1] else 'N/A'
                flight_info['return_departure_time'] = times[2].find('time').text.strip() if times[2] else 'N/A'
                flight_info['return_arrival_time'] = times[3].find('time').text.strip() if times[3] else 'N/A'
            price = flight.find('div', {'data-test': 'ResultCardPrice'}).find('span').get_text(strip=True)
            priceFIN = re.sub(r'[^\d]', '', price)
            flight_info['price'] = (int)(priceFIN)

            flights.append(flight_info)
        except Exception as e:
            print(f"Error parsing a flight: {e}")

    driver.quit()

    return flights


def save_to_csv(flight_data, origin, destination, departure_date, return_date):
    file_name = 'flights.csv'
    file_exists = os.path.exists(file_name)

    for flight in flight_data:
        flight['origin'] = origin
        flight['destination'] = destination
        flight['departure_date'] = departure_date
        flight['return_date'] = return_date
        flight['recorded_at'] = date.today()

    with open(file_name, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['recorded_at', 'airline', 'departure_time', 'arrival_time',
                                                  'return_departure_time', 'return_arrival_time', 'price', 'origin',
                                                  'destination', 'departure_date', 'return_date'])

        if not file_exists:
            writer.writeheader()

        writer.writerows(flight_data)


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
        origin = origin.split('-')[0].capitalize()
        destination = destination.split('-')[0].capitalize()
        save_to_csv(flights, origin, destination, departure_date, return_date)
        return jsonify({'success': True, 'flights': flights})
    return jsonify({'success': False, 'error': 'No flights found.'})


if __name__ == "__main__":
    app.run(debug=True)