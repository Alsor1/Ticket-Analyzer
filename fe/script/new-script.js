document.addEventListener('DOMContentLoaded', function() {
    const mlButton = document.getElementById('ml-button');
    const resultDiv = document.getElementById('result');
    const errorDiv = document.getElementById('error');

    mlButton.addEventListener('click', async function(event) {
        event.preventDefault(); // Prevent form submission

        // Get form values
        const origin = document.getElementById('origin').value;
        const destination = document.getElementById('destination').value;
        const departureDate = document.getElementById('departure-date').value;
        const returnDate = document.getElementById('arrival-date').value;

        // Validate inputs
        if (!origin || !destination || !departureDate || !returnDate) {
            errorDiv.textContent = 'Please fill in all fields';
            errorDiv.style.display = 'block';
            resultDiv.style.display = 'none';
            return;
        }

        try {
            // Send request to backend
            const response = await fetch('http://localhost:5000/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    origin: origin,
                    destination: destination,
                    departure_date: departureDate,
                    return_date: returnDate
                })
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();

            // Display results
            resultDiv.innerHTML = `
                <p><strong>Best Time to Buy:</strong> ${data.best_time_to_buy}</p>
                <p><strong>Predicted Ticket Price:</strong> €${data.predicted_price.toFixed(2)}</p>
            `;
            resultDiv.style.display = 'block';
            errorDiv.style.display = 'none';

        } catch (error) {
            console.error('Error:', error);
            errorDiv.textContent = 'Failed to fetch prediction. Please try again.';
            errorDiv.style.display = 'block';
            resultDiv.style.display = 'none';
        }
    });
});