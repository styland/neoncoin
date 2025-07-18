function convert() {
    const amount = parseFloat(document.getElementById("amount").value);
    const from = document.getElementById("from").value;
    const to = document.getElementById("to").value;
    const resultDisplay = document.getElementById("result");

    if (isNaN(amount) || amount <= 0) {
        resultDisplay.textContent = "Enter a valid amount.";
        return;
    }

    const rates = {
        neo: { neo: 1, neon: 10, neolite: 100 },
        neon: { neo: 0.1, neon: 1, neolite: 10 },
        neolite: { neo: 0.01, neon: 0.1, neolite: 1 }
    };

    const converted = amount * rates[from][to];
    resultDisplay.textContent = `${amount} ${from} = ${converted.toFixed(2)} ${to}`;
}
function convert() {
    const amount = parseFloat(document.getElementById('amount').value);
    const from = document.getElementById('from').value;
    const to = document.getElementById('to').value;

    if (!amount || amount <= 0) {
        document.getElementById('result').textContent = "Enter a valid amount";
        return;
    }

    fetch('/convert', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ amount, from, to })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            document.getElementById('result').textContent = `Converted ${amount} ${from} to ${data.converted} ${to}`;
            location.reload(); // Refresh to show updated balances
        } else {
            document.getElementById('result').textContent = data.message;
        }
    })
    .catch(error => {
        document.getElementById('result').textContent = "Conversion failed.";
        console.error(error);
    });
}
function toggleFilter() {
    const form = document.getElementById('filter-form');
    form.style.display = form.style.display === 'none' ? 'block' : 'none';
}
