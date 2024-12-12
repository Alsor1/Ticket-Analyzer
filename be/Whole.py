import time
import csv
import re
import os
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup


# --- Web Scraping Part ---
def setup_browser():
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def scrape_flights(origin, destination, departure_date, return_date):
    driver = setup_browser()
    url = f"https://www.kiwi.com/en/search/results/{origin}/{destination}/{departure_date}/{return_date}"
    driver.get(url)
    time.sleep(5)

    driver.find_element(By.XPATH, '//*[@id="cookies_accept"]').click()
    time.sleep(10)

    for _ in range(2):
        try:
            load_more_button = driver.find_element(By.XPATH,
                                                   '//*[@id="react-view"]/div[2]/div[4]/div/div/div/div/div/div[3]/div/div/div[4]/div/div/button/div')
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
            flight_info['airline'] = airline
            times = flight.find_all('div', {'data-test': 'TripTimestamp'})
            if len(times) >= 4:
                flight_info['departure_time'] = times[0].find('time').text.strip() if times[0] else 'N/A'
                flight_info['arrival_time'] = times[1].find('time').text.strip() if times[1] else 'N/A'
                flight_info['return_departure_time'] = times[2].find('time').text.strip() if times[2] else 'N/A'
                flight_info['return_arrival_time'] = times[3].find('time').text.strip() if times[3] else 'N/A'
            price = flight.find('div', {'data-test': 'ResultCardPrice'}).find('span').get_text(strip=True)
            priceFIN = re.sub(r'[^\d]', '', price)
            flight_info['price'] = int(priceFIN)
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
        writer = csv.DictWriter(file, fieldnames=['airline', 'departure_time', 'arrival_time', 'return_departure_time',
                                                  'return_arrival_time', 'price', 'origin', 'destination',
                                                  'departure_date', 'return_date', 'recorded_at'])
        if not file_exists:
            writer.writeheader()
        writer.writerows(flight_data)


# --- Machine Learning Part ---
# Load the dataset
data = pd.read_csv("flights_final.csv")

# Feature Engineering
data['Info Taken Date'] = pd.to_datetime(data['Info Taken Date'])
data['Departure Date'] = pd.to_datetime(data['Departure Date'])
data['Return Date'] = pd.to_datetime(data['Return Date'])

# Days until departure
data['Days Until Departure'] = (data['Departure Date'] - data['Info Taken Date']).dt.days

# Day of the week for info and departure dates
data['Info Day of Week'] = data['Info Taken Date'].dt.dayofweek
data['Departure Day of Week'] = data['Departure Date'].dt.dayofweek

# Encode categorical variables
encoder = LabelEncoder()
data['Airline'] = encoder.fit_transform(data['Airline'])
data['Departure City'] = encoder.fit_transform(data['Departure City'])
data['Destination City'] = encoder.fit_transform(data['Destination City'])

# Features and target
features = ['Airline', 'Departure City', 'Destination City', 'Days Until Departure', 'Info Day of Week',
            'Departure Day of Week']
target = 'Price (€)'

X = data[features]
y = data[target]

# Split the dataset
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train a Random Forest Regressor
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate the model
y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
print(f"Mean Absolute Error: {mae:.2f} €")


# Function to predict the best time to buy
def predict_best_time(origin, destination, departure_date, return_date, airline=None):
    origin_encoded = encoder.transform([origin])[0]
    destination_encoded = encoder.transform([destination])[0]

    departure_date = pd.to_datetime(departure_date)
    return_date = pd.to_datetime(return_date)

    future_prices = []
    future_dates = []

    # Simulate price predictions for days leading up to departure
    for days_before in range(1, 61):  # Look at prices up to 60 days before departure
        info_date = departure_date - timedelta(days=days_before)
        if info_date < datetime.now():
            continue

        input_data = pd.DataFrame([{
            'Airline': airline if airline else random.choice(X['Airline'].unique()),
            'Departure City': origin_encoded,
            'Destination City': destination_encoded,
            'Days Until Departure': (departure_date - info_date).days,
            'Info Day of Week': info_date.dayofweek,
            'Departure Day of Week': departure_date.dayofweek
        }])

        predicted_price = model.predict(input_data)[0]
        future_prices.append(predicted_price)
        future_dates.append(info_date)

    # Find the date with the lowest predicted price
    optimal_index = np.argmin(future_prices)
    optimal_date = future_dates[optimal_index]
    optimal_price = future_prices[optimal_index]

    return optimal_date, optimal_price


# --- Example Usage ---
origin = "berlin-germany"
destination = "madrid-spain"
departure_date = "2025-6-20"
return_date = "2025-6-30"

# Scrape flight data
flights = scrape_flights(origin, destination, departure_date, return_date)
if flights:
    save_to_csv(flights, origin, destination, departure_date, return_date)

# Predict the best time to buy
best_time, predicted_price = predict_best_time(origin, destination, departure_date, return_date)
print(f"Best time to buy: {best_time.strftime('%Y-%m-%d')}, Predicted price: {predicted_price:.2f} €")
