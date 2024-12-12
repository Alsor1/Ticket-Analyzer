import numpy as np
from datetime import datetime, timedelta
import pandas as pd
import random
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error

# ---- Machine Learning Part ----

# Load the dataset with the correct header
try:
    data = pd.read_csv("flights_final.csv")
except FileNotFoundError:
    print("File not found. Make sure 'flights_final.csv' exists.")
    data = pd.DataFrame()

# Ensure that the columns are correctly set and in the right order
data.columns = ['Info Taken Date', 'Airline', 'Departure Time', 'Departure Arrival Time',
                'Return Departure Time', 'Return Arrival Time', 'Price (€)',
                'Departure City', 'Destination City', 'Departure Date', 'Return Date']

# Feature Engineering
data['Info Taken Date'] = pd.to_datetime(data['Info Taken Date'], errors='coerce')
data['Departure Date'] = pd.to_datetime(data['Departure Date'], errors='coerce')
data['Return Date'] = pd.to_datetime(data['Return Date'], errors='coerce')

# Remove rows with missing values (if any)
data.dropna(subset=['Info Taken Date', 'Departure Date', 'Return Date', 'Price (€)'], inplace=True)

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
    """
    Predicts the best time to buy a ticket based on future price trends.
    """
    # Check if the origin and destination are in the encoder's classes
    if origin not in encoder.classes_:
        origin_encoded = -1  # Or assign any default value
    else:
        origin_encoded = encoder.transform([origin])[0]

    if destination not in encoder.classes_:
        destination_encoded = -1  # Or assign any default value
    else:
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


# ---- Web Scraping Part ----
def setup_browser():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def scrape_flights(origin, destination, departure_date, return_date):
    driver = setup_browser()

    # Navigate to the Kiwi flight search page
    url = f"https://www.kiwi.com/en/search/results/{origin}/{destination}/{departure_date}/{return_date}"
    driver.get(url)

    time.sleep(5)  # Wait for the page to load
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

    # Parse the page with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    flights = []
    for flight in soup.find_all('div', {'data-test': 'ResultCardWrapper'}):
        try:
            flight_info = {}

            # Airline
            airline = flight.find('div', {'class': 'orbit-carrier-logo'}).find('img')['title']
            flight_info['airline'] = airline

            # Departure and return times
            times = flight.find_all('div', {'data-test': 'TripTimestamp'})
            if len(times) >= 4:
                flight_info['departure_time'] = times[0].find('time').text.strip() if times[0] else 'N/A'
                flight_info['arrival_time'] = times[1].find('time').text.strip() if times[1] else 'N/A'
                flight_info['return_departure_time'] = times[2].find('time').text.strip() if times[2] else 'N/A'
                flight_info['return_arrival_time'] = times[3].find('time').text.strip() if times[3] else 'N/A'

            # Price
            price = flight.find('div', {'data-test': 'ResultCardPrice'}).find('span').get_text(strip=True)
            priceFIN = re.sub(r'[^\d]', '', price)
            flight_info['price'] = int(priceFIN)

            # Info Taken Date (extract the date in the middle column, if it's part of the scraped data)
            # Replace 'your-class-for-info-date' with the actual class name or structure
            info_taken_date = flight.find('div', {'class': 'your-class-for-info-date'})  # Adjust class
            if info_taken_date:
                flight_info['Info Taken Date'] = info_taken_date.text.strip()  # Extract the correct date from middle column
            else:
                flight_info['Info Taken Date'] = datetime.now().strftime('%Y-%m-%d')  # Default to today's date if not found

            # Add missing columns and use .split('-')[0].capitalize() for cities
            flight_info['Departure City'] = origin.split('-')[0].capitalize()
            flight_info['Destination City'] = destination.split('-')[0].capitalize()
            flight_info['Departure Date'] = departure_date
            flight_info['Return Date'] = return_date

            flights.append(flight_info)
        except Exception as e:
            print(f"Error parsing a flight: {e}")

    driver.quit()
    return flights


# ---- Test the Web Scraping and ML Model ----
if __name__ == "__main__":
    origin = "berlin-germany"
    destination = "madrid-spain"
    departure_date = "2025-06-25"
    return_date = "2025-07-05"

    # Scrape flight data
    print("Scraping flights...")
    flights = scrape_flights(origin, destination, departure_date, return_date)

    if flights:
        print(f"Scraped {len(flights)} flights.")
        # Append scraped flights to the existing CSV file
        df_flights = pd.DataFrame(flights)
        df_flights.to_csv('flights_final.csv', mode='a', header=False, index=False)
        print("Data appended to flights_final.csv.")

    # Predict the best time to buy a ticket based on the ML model
    print("\nPredicting the best time to buy...")
    best_time, predicted_price = predict_best_time(origin, destination, departure_date, return_date)

    print(f"Best time to buy: {best_time.strftime('%Y-%m-%d')}")
    print(f"Predicted price: {predicted_price:.2f} €")
