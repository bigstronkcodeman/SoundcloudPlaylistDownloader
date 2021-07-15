const socket = io();
const fname = "playlists.zip";
const err_responses = [
    "Soundcloud user does not exist.\n",
    "Please enter a valid soundcloud user URL.\n",
    "Program crashed unexpectedly. Please try again.\n"
];

let active = false;
let first = true;
let user_url = null;
let user = null;

socket.on("newdata", (data) => {
    console.log(`Data received: ${data.toString()}`);
});

socket.on("download_data", (data) => {
    data = data.toString();
    console.log(`DOWNLOAD data received: ${data}`);
    if (err_responses.includes(data)) {
        first = true;
        active = false;
    } else if (first) {
        $("#terminal").children("p:first").remove();
        first = false;
        active = true;
    } else if (data == "Zip archive written.\n") {
        let dltag = document.createElement("a");
        dltag.href = `/downloadPlaylists?sc_user_url=${user}`;
        dltag.setAttribute("download", `${user}_playlists.zip`);
        dltag.click();
        first = true;
        active = false;
        return;
    }
    $("#terminal").append(`<p>➜ ${data}</p>`);
    $("#terminal").scrollTop($("#terminal")[0].scrollHeight);
});

function urlSubmit() {
    if (!active) {
        $("#terminal").empty();
        user_url = $("#sc_user_url").val();
        user = user_url.split("/");
        user = user[user.length ? user.length - 1 : 0];
        socket.emit("download_request", $("#sc_user_url").val());
    } else {
        alert("You're already downloading a set of playlists!");
    }
}
