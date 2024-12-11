function fetchUsers(query = "") {
    fetch(`/api/search/user/?query=${encodeURIComponent(query)}`)
        .then((response) => response.json())
        .then((data) => {
            const resultsContainer = document.getElementById("dynamic-results");
            resultsContainer.innerHTML = "";

            // Handle no results case
            if (data.length === 0) {
                resultsContainer.innerHTML = "<p>No users found.</p>";
                return;
            }

            // Display results
            data.forEach((user) => {
                const userDiv = document.createElement("div");
                userDiv.classList.add("result-item");
                userDiv.innerHTML = `
                    <li>
                        <p><a href="/profile/${user.username}">${user.username}</a></p>
                        <p>${user.name}</p>
                    </li>
                `;
                resultsContainer.appendChild(userDiv);
            });
        })
        .catch((error) => {
            console.error("Error fetching user data:", error);
        });
}
document.getElementById("search-input").addEventListener("input", function () {
    fetchUsers(this.value);
});

window.addEventListener("DOMContentLoaded", function () {
    fetchUsers();
});