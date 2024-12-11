document.getElementById('ticket-form').addEventListener('submit', async function (e) {
    e.preventDefault();

    const origin = document.getElementById('origin').value.trim();
    const destination = document.getElementById('destination').value.trim();
    const departureDate = document.getElementById('departure-date').value;
    const arrivalDate = document.getElementById('arrival-date').value;

    const resultDiv = document.getElementById('result');
    const errorDiv = document.getElementById('error');
    resultDiv.style.display = 'none';
    errorDiv.style.display = 'none';

    const today = new Date().toISOString().split('T')[0];
    if (departureDate < today || arrivalDate < today) {
        errorDiv.innerHTML = `<p><strong>Error:</strong> The dates cannot be in the past.</p>`;
        errorDiv.style.display = 'block';
        return;
    }

    try {
        // Use the POST method to send data to the Flask server
        const response = await fetch('http://127.0.0.1:5000/scrape', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ origin, destination, departure_date: departureDate, return_date: arrivalDate })
        });
        const result = await response.json();

        if (result.success) {
            const flights = result.flights;
            // Display the list of flights
            resultDiv.innerHTML = `
                <h3>Available Flights:</h3>
                <ul>${flights.map(flight => `<li>${flight.airline} - $${flight.price}</li>`).join('')}</ul>
            `;
            resultDiv.style.display = 'block';
        } else {
            // Display any errors from the server
            errorDiv.innerHTML = `<p><strong>Error:</strong> ${result.error}</p>`;
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        // Handle errors during the fetch process
        errorDiv.innerHTML = `<p><strong>Error:</strong> Could not connect to the server.</p>`;
        errorDiv.style.display = 'block';
    }
});
