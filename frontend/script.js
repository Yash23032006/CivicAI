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


        const result = await response.json();


        if (!response.ok) {

            alert(
                "Failed to submit civic issue.\n\n" +
                result.message
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

        console.error("Submission error:", error);

        alert(
            "Unable to connect to CivicAI backend.\n\n" +
            "Please make sure backend.py is running."
        );

    }

});