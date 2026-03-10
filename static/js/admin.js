function getToken() {
    return localStorage.getItem("token");
}

/* LOAD ATTENDANCE */

async function loadAttendance() {
    console.log("DEBUG: loadAttendance started");
    const table = document.getElementById("attendanceTable");
    if (!table) return;

    table.innerHTML = "";

    const token = getToken();

    if(!token){
        window.location.href = "login.html";
        return;
    }

    try {
        const response = await fetch(
            "/api/admin/all-attendance",
            {
                method: "GET",
                headers: {
                    "Authorization": "Bearer " + token
                }
            }
        );

        if(!response.ok){
            const txt = await response.text();
            table.innerHTML =
            `<tr><td colspan="8" style="color:red">
            Failed to load attendance: ${response.status} ${txt}
            </td></tr>`;
            return;
        }

        const data = await response.json();

        if(!Array.isArray(data) || data.length === 0){
            table.innerHTML =
            `<tr><td colspan="8">No attendance records found.</td></tr>`;
            return;
        }

        data.forEach(emp=>{

            const row = document.createElement("tr");

            const statusClass = emp.status ? emp.status.toLowerCase() : "";

            row.innerHTML = `
            <td>${emp.employee_name}</td>
            <td>${emp.date}</td>
            <td>${emp.tap_in ? emp.tap_in : "-"}</td>
            <td>${emp.break_start ? emp.break_start : "-"}</td>
            <td>${emp.break_end ? emp.break_end : "-"}</td>
            <td>${emp.tap_out ? emp.tap_out : "-"}</td>
            <td class="${statusClass}">${emp.status || "-"}</td>
            <td>
                <button class="edit-btn"
                data-attendance-id="${emp.attendance_id}">
                Edit
                </button>
            </td>
            `;

            table.appendChild(row);
        });

    } catch (err) {
        table.innerHTML =
        `<tr><td colspan="8" style="color:red">
        Request failed: ${err.message}
        </td></tr>`;
    }
}

async function loadEmployees() {
    console.log("DEBUG: loadEmployees started");
    const list = document.getElementById("employeeList");
    if (!list) return;

    list.innerHTML = "";
    const token = getToken();

    try {
        const response = await fetch("/api/admin/employees", {
            headers: { "Authorization": "Bearer " + token }
        });
        const data = await response.json();

        if (data.length === 0) {
            list.innerHTML = '<tr><td colspan="4">No employees found.</td></tr>';
            return;
        }

        data.forEach(emp => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${emp.id.substring(0, 8)}...</td>
                <td>${emp.username}</td>
                <td>Employee</td>
                <td>
                    <button class="delete-btn" onclick="deleteEmployee('${emp.id}')">Delete</button>
                </td>
            `;
            list.appendChild(row);
        });
    } catch (err) {
        list.innerHTML = `<tr><td colspan="4" style="color:red">Failed: ${err.message}</td></tr>`;
    }
}

async function loadReport() {
    console.log("DEBUG: loadReport started");
    const token = getToken();
    try {
        const response = await fetch("/api/admin/attendance-report", {
            headers: { "Authorization": "Bearer " + token }
        });
        const data = await response.json();
        document.getElementById("totalEmployees").innerText = `Total Employees : ${data.total_employees}`;
        document.getElementById("presentToday").innerText = `Present Today : ${data.present_today}`;
        document.getElementById("absentToday").innerText = `Absent Today : ${data.absent_today}`;
    } catch (err) {
        console.error("Report load failed:", err);
    }
}

loadAttendance();
loadEmployees();
loadReport();


/* CREATE EMPLOYEE */

const createBtn = document.getElementById("createEmployeeBtn");

const createMsgEl = document.createElement("div");

createMsgEl.style.marginTop = "10px";

if(createBtn && createBtn.parentNode){
    createBtn.parentNode.appendChild(createMsgEl);
}


if(createBtn){

createBtn.addEventListener("click", async ()=>{

    const username = document.getElementById("newUsername").value.trim();
    const password = document.getElementById("newPassword").value;

    if(!username || !password){
        createMsgEl.innerText = "Enter username and password";
        createMsgEl.style.color = "red";
        return;
    }

    const token = getToken();

    if(!token){
        alert("Login required");
        return;
    }

    createBtn.disabled = true;
    createBtn.innerText = "Creating...";

    try{

        const res = await fetch(
            "/api/admin/create-employee",
            {
                method: "POST",
                headers:{
                    "Content-Type":"application/json",
                    "Authorization":"Bearer "+token
                },
                body: JSON.stringify({
                    username: username,
                    password: password
                })
            }
        );

        const data = await res.json();

        if(!res.ok){
            createMsgEl.innerText = data.message || "Creation failed";
            createMsgEl.style.color = "red";
        }
        else{

            createMsgEl.innerText = "Employee created successfully";
            createMsgEl.style.color = "green";

            document.getElementById("newUsername").value = "";
            document.getElementById("newPassword").value = "";

            loadAttendance();
            loadEmployees();
            loadReport();
        }

    }
    catch(err){

        createMsgEl.innerText = "Request failed: " + err.message;
        createMsgEl.style.color = "red";

    }

    createBtn.disabled = false;
    createBtn.innerText = "Create Employee";

});

}



/* EDIT ATTENDANCE */

document.addEventListener("click", function(e){

    const btn = e.target.closest(".edit-btn");

    if(!btn) return;

    const attendanceId = btn.getAttribute("data-attendance-id");

    const newStatus = prompt(
        "Enter new status (Present / Half Day / Leave)"
    );

    if(!newStatus) return;

    updateAttendance(attendanceId, newStatus);

});


async function updateAttendance(attendanceId, status){

    const token = getToken();

    if(!token){
        alert("Not authenticated");
        return;
    }

    try{

        const res = await fetch(
            "/api/admin/edit-attendance",
            {
                method: "PUT",
                headers:{
                    "Content-Type":"application/json",
                    "Authorization":"Bearer "+token
                },
                body: JSON.stringify({
                    attendance_id: attendanceId,
                    status: status
                })
            }
        );

        if(!res.ok){
            const txt = await res.text();
            alert("Update failed: " + txt);
            return;
        }

        alert("Attendance Updated");

        loadAttendance();

    }
    catch(err){

        alert("Request failed: " + err.message);

    }

}

async function deleteEmployee(userId) {
    if (!confirm("Are you sure you want to delete this employee?")) return;

    const token = getToken();
    try {
        const response = await fetch(`/api/admin/delete-employee/${userId}`, {
            method: "DELETE",
            headers: { "Authorization": "Bearer " + token }
        });

        if (response.ok) {
            alert("Employee deleted successfully");
            loadEmployees();
            loadReport();
        } else {
            const data = await response.json();
            alert("Delete failed: " + (data.message || "Unknown error"));
        }
    } catch (err) {
        alert("Request failed: " + err.message);
    }
}