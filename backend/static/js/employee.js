const API_BASE = "/api/employee";

/* Get token from localStorage */
const token = localStorage.getItem("token");

if (!token) {
    window.location.href = "/";
}

/* ---------------- LOGIN ---------------- */

async function login(){

try{

    const res = await fetch(API_BASE + "/login",{
        method:"POST",
        headers:{
            "Authorization":"Bearer " + token
        }
    });

    const data = await res.json();

    document.getElementById("msg").innerText = data.message;

}catch(err){

    document.getElementById("msg").innerText = "Request failed: " + err.message;

}

}

/* ---------------- LOGOUT ---------------- */

async function logout(){

try{

    const res = await fetch(API_BASE + "/logout",{
        method:"POST",
        headers:{
            "Authorization":"Bearer " + token
        }
    });

    const data = await res.json();

    document.getElementById("msg").innerText = data.message;

}catch(err){

    document.getElementById("msg").innerText = "Request failed: " + err.message;

}

}

/* ---------------- WEBSITE LOGOUT ---------------- */

function logout() {

    localStorage.removeItem("token");
    localStorage.removeItem("role");

    window.location.href = "/";

}