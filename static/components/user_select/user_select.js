const selectedUsers = [ ];

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
                if (selectedUsers.find((u) => u.username === user.username)) return; // Don't show selected users
                const userDiv = document.createElement("div");
                userDiv.classList.add("result-item");
                userDiv.innerHTML = `
                    <li id="${"user-" + user.username}">
                        <p><a href="/profile/${user.username}">${user.username}</a> ${user.name}
                        <button type="button">Select</button></p>
                    </li>
                `;
                userDiv.onclick = function() {selectUser(user)}
                resultsContainer.appendChild(userDiv);
            });
        })
        .catch((error) => {
            console.error("Error fetching user data:", error);
        });
}

function deselectUser(user) {
    const index = selectedUsers.indexOf(user)
    if (index === -1) return // Couldn't find user
    selectedUsers.splice(index, 1)
    document.getElementById("selected-users-form-control").value = selectedUsers.map(u => u.username).join(',')
    document.getElementById("user-select-" + user.username).remove()
}

function selectUser(user) {
    selectedUsers.push(user)
    document.getElementById("selected-users-form-control").value = selectedUsers.map(u => u.username).join(',')
    document.getElementById("user-"+user.username).remove()
    const selectedContainer = document.getElementById("dynamic-selected-users")

    const userDiv = document.createElement("div");
    userDiv.classList.add("result-item");
    userDiv.innerHTML = `
        <li id="${"user-select-" + user.username}">
            <p><a href="/profile/${user.username}">${user.username}</a>  ${user.name}
            <button type="button">Remove</button> </a>
        </li>
    `
    userDiv.onclick = function() { deselectUser(user) }
    selectedContainer.append(userDiv)
}


document.getElementById("search-input").addEventListener("input", function () {
    fetchUsers(this.value);
});

window.addEventListener("DOMContentLoaded", function () {
    fetchUsers();
});