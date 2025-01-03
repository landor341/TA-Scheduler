const selectedUsers = [ ];

function fetchUsers(query = "") {
    fetch(`/api/search/user` + (search_role ? ("/" + search_role) : "") + `/?query=${encodeURIComponent(query)}`)
        .then((response) => response.json())
        .then((data) => {
            const resultsContainer = document.getElementById("dynamic-results");
            resultsContainer.innerHTML = "";
            let displayedUsers = 0;

            // Display results
            data.forEach((user) => {
                if (selectedUsers.find((u) => u.username === user.username)) return; // Don't show selected users
                if (!displayedUsers) {
                    const header = document.createElement("div");
                    header.style = "text-decoration: underline"
                    header.innerHTML = `
                        <p style="width: 130px; display: inline-block; text-decoration: underline;">Username</p>Full Name
                    `;
                    resultsContainer.appendChild(header);
                }
                displayedUsers++;
                const userDiv = document.createElement("div");
                userDiv.classList.add("result-item");
                userDiv.innerHTML = `
                    <li id="${"user-" + user.username}">
                        <p><a
                            href="/profile/${user.username}" 
                            style=" display: inline-block; width: 100px; text-overflow: clip; margin-right: 30px; color: black;"
                        >${user.username}</a> ${user.name}
                        <button type="button">Select</button></p>
                    </li>
                `;
                userDiv.onclick = function() {selectUser(user)}
                resultsContainer.appendChild(userDiv);
            });
            // Handle no results case
            if (displayedUsers === 0) {
                resultsContainer.innerHTML = "<p>No users found.</p>";
            }
        })
        .catch((error) => {
            console.error("Error fetching user data:", error);
        });
}

function deselectUser(user) {
    const index = selectedUsers.indexOf(user)
    if (index === -1) return // Couldn't find user
    selectedUsers.splice(index, 1)
    if (!selectedUsers.length) {
        document.getElementById("select-user-search-header").remove()
    }

    document.getElementById("selected-users-form-control").value = selectedUsers.map(u => u.username).join(',')
    document.getElementById("user-select-" + user.username).remove()
    updateSelectVisibility()
}

function selectUser(user, isFresh=false) {
    selectedUsers.push(user)
    updateSelectVisibility()
    if (!isFresh) {
        document.getElementById("selected-users-form-control").value = selectedUsers.map(u => u.username).join(',')
        document.getElementById("user-" + user.username).remove()
    }
    const selectedContainer = document.getElementById("dynamic-selected-users")

    if (selectedUsers[0] === user) {
        const header = document.createElement("div");
        header.id="select-user-search-header"
        header.style = "text-decoration: underline"
        header.innerHTML = `
            <p style="width: 130px; display: inline-block; text-decoration: underline;">Username</p>Full Name
        `;
        selectedContainer.appendChild(header);
    }


    const userDiv = document.createElement("div");
    userDiv.classList.add("result-item");
    userDiv.innerHTML = `
        <li id="${"user-select-" + user.username}">
            <p><a
                href="/profile/${user.username}" 
                style=" display: inline-block; width: 100px; text-overflow: clip; margin-right: 30px; color: black;"
            >${user.username}</a> ${user.name}
            <button type="button">Select</button></p>
        </li>
    `
    userDiv.onclick = function() { deselectUser(user) }
    selectedContainer.append(userDiv)
}

function updateSelectVisibility() {
    document.getElementById("user-selection-container").style = selectedUsers.length >= max_users ? "display: none" : "display: block"
}

prefilled_user_list = document.getElementById("selected-users-form-control").value.split(",")
prefilled_user_list = prefilled_user_list.filter(n => n)

var prefilled_user_loaded_count = 0
for (let u of prefilled_user_list) {
    if (u !== "") {
        fetch(`/api/search/user/?query=${encodeURIComponent(u)}`)
        .then((response) => response.json())
        .then((data) => {
            selectUser(data[0], true)
            prefilled_user_loaded_count++;
            if (prefilled_user_loaded_count === prefilled_user_list.length) {
                document.getElementById("search-input").addEventListener("input", function () {
                    fetchUsers(this.value);
                });

                window.addEventListener("DOMContentLoaded", function () {
                    fetchUsers();
                });
                fetchUsers();
            }
        })
    }
}

if (!prefilled_user_list.length) fetchUsers();