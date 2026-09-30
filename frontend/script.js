const issueForm = document.getElementById("issueForm");

issueForm.addEventListener("submit", async function (event) {

    event.preventDefault();

    const problem =
        document.getElementById("problem").value.trim();

    const language =
        document.getElementById("language").value;

    const location =
        document.getElementById("location").value.trim();


    // Basic validation
if (problem === "" || location === "") {

    alert(
        "Please enter the problem description and location."
    );

    return;
}


// Check logged-in citizen
const citizenEmail = sessionStorage.getItem("userEmail");

if (!citizenEmail) {

    alert(
        "Please login before submitting a civic issue."
    );

    window.location.href = "login.html";

    return;
}


    try {

        const response = await fetch("/api/report", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                problem: problem,
                language: language,
                location: location,
                citizen_email: citizenEmail

            })

        });


        const responseText = await response.text();

let result;

try {
    result = JSON.parse(responseText);
} catch (parseError) {
    console.error("Invalid JSON response:", responseText);

    alert(
        "CivicAI server returned an unexpected response.\n\n" +
        "HTTP Status: " + response.status + "\n\n" +
        responseText.substring(0, 500)
    );

    return;
}


if (!response.ok) {

    alert(
        "Failed to submit civic issue.\n\n" +
        (result.message || "Unknown server error")
    );

    return;
}

        // SUCCESS
        alert(
            "Civic issue submitted successfully!\n\n" +

            "Report ID: " + result.id + "\n" +

            "AI Category: " + result.category + "\n" +

            "AI Severity: " + result.severity + "\n" +

            "Location: " + result.location + "\n" +

            "AI Priority Score: " +
            result.priority_score + "/100"
        );


        // Reset form
        issueForm.reset();


    } catch (error) {

    console.error("Report submission error:", error);

    alert(
        "Report submission failed:\n\n" +
        error.message
    );

}

});