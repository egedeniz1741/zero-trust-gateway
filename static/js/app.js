let jwtToken = "";

function logResponse(status, data) {
    const logElement = document.getElementById("response-log");
    logElement.textContent = `HTTP Status: ${status}\n\n` + JSON.stringify(data, null, 2);
}

async function login() {
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    const res = await fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    logResponse(res.status, data);

    if (res.ok) {
        jwtToken = data.access_token;

      
        const payload = JSON.parse(atob(jwtToken.split('.')[1]));
        document.getElementById("user-display").textContent = payload.sub;

        const badge = document.getElementById("role-badge");
        badge.textContent = payload.role;
        badge.className = "badge " + (payload.role === "admin" ? "badge-admin" : "badge-viewer");

        document.getElementById("login-section").classList.add("hidden");
        document.getElementById("dashboard-section").classList.remove("hidden");
    }
}

async function fetchVault() {
    const res = await fetch("/vault-data", {
        headers: { "Authorization": `Bearer ${jwtToken}` }
    });
    logResponse(res.status, await res.json());
}

async function purgeLogs() {
    const res = await fetch("/admin/purge-logs", {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${jwtToken}` }
    });
    logResponse(res.status, await res.json());
}

async function logout() {
    const res = await fetch("/logout", {
        method: "POST",
        headers: { "Authorization": `Bearer ${jwtToken}` }
    });
    logResponse(res.status, await res.json());

   
    setTimeout(() => {
        document.getElementById("login-section").classList.remove("hidden");
        document.getElementById("dashboard-section").classList.add("hidden");
    }, 3500);
}