document.getElementById("policyForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const file = document.getElementById("policyFile").files[0];
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch("http://127.0.0.1:8000/analyze_policy/", {
        method: "POST",
        body: formData
    });
    const result = await response.json();
    document.getElementById("result").innerHTML = `
        <h3>Compliance Score: ${result.score}%</h3>
        <p>Gaps: ${result.gaps?.join(", ")}</p>
        <button onclick="pay()">Unlock Full Report (Pay 2 ADA)</button>
    `;
});

async function pay() {
    const paymentId = "TX12345";
    const file = document.getElementById("policyFile").files[0];
    const formData = new FormData();
    formData.append("file", file);
    formData.append("payment_id", paymentId);

    const response = await fetch("http://127.0.0.1:8000/analyze_policy/", {
        method: "POST",
        body: formData
    });
    const result = await response.json();
    document.getElementById("result").innerHTML = `
        <h3>Full Report:</h3>
        <pre>${JSON.stringify(result.full_report, null, 2)}</pre>
    `;
}
