const hostname = "127.0.0.1";
const port = 3000;
const path = require("path");
const express = require("express");
const app = require('express')();
const http = require('http').Server(app);
const io = require('socket.io')(http);
const spawn = require("child_process").spawn;
const fs = require("fs");

app.use(express.static(path.join(__dirname, "public")));

app.get("/", (req, res) => {
    res.sendFile(path.join(__dirname, "views/index.html"));
});

app.get("/downloadPlaylists", (req, res) => {
    res.download(path.join(__dirname, `zips/${req.query.sc_user_url}.zip`), `${req.query.sc_user_url}_playlists.zip`, (err) => {
        if (err) {
            console.log(err);
        } else {
            fs.unlink(path.join(__dirname, `zips/${req.query.sc_user_url}.zip`), (err) => {
                if (err) {
                    console.log(err);
                }
            });
        }
    });
});

http.listen(port, hostname, function() {
    console.log(`Server running at http://${hostname}:${port}/`);
});

io.on('connection', (socket) => {
    console.log("NEW USER CONNECTED!");
    socket.emit("newdata", "NEW USER CONNECTED!");

    socket.on("download_request", (data) => {
        let process = spawn("/home/phil/.venvs/sc_downloader_env/bin/python3", ["-u", "sc_downloader.py", data.toString()]);

        process.stdout.on("data", (data) => {
            console.log(data.toString());
            socket.emit("download_data", data.toString());
        });

        process.on("exit", (code) => {
            let user;
            if (code === 0) {
                user = data.toString().split("/");
                user = user[user.length - 1];
                fname = `./zips/${user}.zip`;
            } else {
                console.log(process.err);
                socket.emit("download_data", "Program crashed unexpectedly. Please try again.");
                return;
            }
        });
    });
});