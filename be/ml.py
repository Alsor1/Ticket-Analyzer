import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import random
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import date

app = Flask(__name__)
CORS(app)

# Load the dataset
data = pd.read_csv("final.csv")

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
features = ['Airline', 'Departure City', 'Destination City', 'Days Until Departure', 'Info Day of Week', 'Departure Day of Week']
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
    Args:
        origin (str): Origin city.
        destination (str): Destination city.
        departure_date (str): Departure date (YYYY-MM-DD).
        return_date (str): Return date (YYYY-MM-DD).
        airline (str): Preferred airline (optional).
    Returns:
        tuple: Optimal purchase date and predicted price.
    """
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

# Example usage
@app.route('/predict', methods=['POST'])
def scrape():
    data = request.json
    origin = data.get('origin').split('-')[0].capitalize()
    destination = data.get('destination').split('-')[0].capitalize()
    departure_date = data.get('departure_date')
    return_date = data.get('return_date')
    airline = None  # Optional: specify an airline

    if not all([origin, destination, departure_date, return_date]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    flights = predict_best_time(origin, destination, departure_date, return_date, airline)
    return jsonify({'best_time_to_buy': flights[0].strftime('%Y-%m-%d'), 'predicted_price': flights[1]})

if __name__ == '__main__':
    app.run(debug=True)