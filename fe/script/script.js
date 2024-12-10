document.getElementById('ticket-form').addEventListener('submit', function (e) {
    e.preventDefault();

    const origin = document.getElementById('origin').value;
    const destination = document.getElementById('destination').value;
    const departureDate = document.getElementById('departure-date').value;
    const arrivalDate = document.getElementById('arrival-date').value;

    const result = analyzeTicket(origin, destination, departureDate, arrivalDate);

    const resultDiv = document.getElementById('result');
    resultDiv.innerHTML = `
        <h3>Recommended Ticket Details:</h3>
        <p><strong>Best Date to Buy:</strong> ${result.bestDate}</p>
        <p><strong>Recommended Airline:</strong> ${result.company}</p>
        <p>Based on your input:</p>
        <ul>
            <li><strong>From:</strong> ${origin}</li>
            <li><strong>To:</strong> ${destination}</li>
            <li><strong>Departure Date:</strong> ${departureDate}</li>
            <li><strong>Arrival Date:</strong> ${arrivalDate}</li>
        </ul>
    `;
    resultDiv.style.display = 'block';
});

function analyzeTicket(origin, destination, departureDate, arrivalDate) {
    const mockResults = [
        { company: 'Airline A', bestDate: '2024-12-15' },
        { company: 'Airline B', bestDate: '2024-12-18' },
        { company: 'Airline C', bestDate: '2024-12-12' }
    ];

    const randomIndex = Math.floor(Math.random() * mockResults.length);
    return mockResults[randomIndex];
}
