document
  .getElementById("ticket-form")
  .addEventListener("submit", async function (e) {
    e.preventDefault();

    const origin = document.getElementById("origin").value.trim();
    const destination = document.getElementById("destination").value.trim();
    const departureDate = document.getElementById("departure-date").value;
    const arrivalDate = document.getElementById("arrival-date").value;

    const resultDiv = document.getElementById("result");
    const errorDiv = document.getElementById("error");
    resultDiv.style.display = "none";
    errorDiv.style.display = "none";

    const today = new Date().toISOString().split("T")[0];
    if (departureDate < today || arrivalDate < today) {
      errorDiv.innerHTML = `<p><strong>Error:</strong> The dates cannot be in the past.</p>`;
      errorDiv.style.display = "block";
      return;
    }

    try {
      const response = await fetch("http://127.0.0.1:5000/scrape", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          origin,
          destination,
          departure_date: departureDate,
          return_date: arrivalDate,
        }),
      });
      const result = await response.json();

      if (result.success) {
        const flights = result.flights;
        resultDiv.innerHTML = `
                <h3>Available Flights:</h3>
                <ul>${flights
                  .map(
                    (flight) => `<li>${flight.airline} - $${flight.price}</li>`
                  )
                  .join("")}</ul>
            `;
        resultDiv.style.display = "block";
      } else {
        errorDiv.innerHTML = `<p><strong>Error:</strong> ${result.error}</p>`;
        errorDiv.style.display = "block";
      }
    } catch (error) {
      errorDiv.innerHTML = `<p><strong>Error:</strong> Could not connect to the server.</p>`;
      errorDiv.style.display = "block";
    }
  });

document.addEventListener("DOMContentLoaded", function () {
  const mlButton = document.getElementById("ml-button");
  const resultDiv = document.getElementById("result");
  const errorDiv = document.getElementById("error");

  mlButton.addEventListener("click", async function (event) {
    event.preventDefault();

    const origin = document.getElementById("origin").value;
    const destination = document.getElementById("destination").value;
    const departureDate = document.getElementById("departure-date").value;
    const returnDate = document.getElementById("arrival-date").value;

    if (!origin || !destination || !departureDate || !returnDate) {
      errorDiv.textContent = "Please fill in all fields";
      errorDiv.style.display = "block";
      resultDiv.style.display = "none";
      return;
    }

    try {
      const response = await fetch("http://localhost:5000/predict", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          origin: origin,
          destination: destination,
          departure_date: departureDate,
          return_date: returnDate,
        }),
      });

      if (!response.ok) {
        throw new Error("Network response was not ok");
      }

      const data = await response.json();

      resultDiv.innerHTML = `
                <p><strong>Best Time to Buy:</strong> ${
                  data.best_time_to_buy
                }</p>
                <p><strong>Predicted Ticket Price:</strong> €${data.predicted_price.toFixed(
                  2
                )}</p>
            `;
      resultDiv.style.display = "block";
      errorDiv.style.display = "none";
    } catch (error) {
      console.error("Error:", error);
      errorDiv.textContent = "Failed to fetch prediction. Please try again.";
      errorDiv.style.display = "block";
      resultDiv.style.display = "none";
    }
  });
});

const helpButton = document.getElementById("help-button");
const helpModal = document.getElementById("help-modal");
const closeHelp = document.getElementById("close-help");

helpButton.addEventListener("click", () => {
  helpModal.style.display = "block";
});

closeHelp.addEventListener("click", () => {
  helpModal.style.display = "none";
});

window.addEventListener("click", (event) => {
  if (event.target === helpModal) {
    helpModal.style.display = "none";
  }
});
