import {CustomWebSocket, getWsUrl} from "./utils.js";


const wsUrl = getWsUrl();
let socket;

const form = document.getElementById("form");
const textInput = document.getElementById("id_text");
const dialogHolder = document.getElementById("dialog-messages");
const m = {unreadMessagesExist: false};

if (form !== null) {
    form.onsubmit = formOnSubmitHandler;
}

function formOnSubmitHandler(ev) {
    ev.preventDefault();
    const messageText = textInput.value;

    console.info("Send new message");
    socket.send(JSON.stringify({
        "command": "get_new_message",
        "message": {
            "text": messageText
        }
    }));
    textInput.value = "";
}

function focusHandler() {
    if (m.unreadMessagesExist) {
        m.sendMarkDialogAsRead();
    }
}

window.addEventListener("focus", focusHandler);

////////
function connect() {
    socket = new CustomWebSocket(wsUrl, connect);
    socket.onmessage = socketOnMessageHandler;
}

connect();

function socketOnMessageHandler(ev) {
    console.info("ws message", ev);
    const data = JSON.parse(ev.data);

    if (!("command" in data)) {
        console.warn("invalid data");
        return;
    }

    const command = data["command"];
    console.info("command", command);
    if (command === "get_new_message") {
        const message = data["message"];
        dialogHolder.appendChild(m.createMessageNode(message));
        m.checkIntegrity(data["integrity_hash"]);

        if (message["is_unread"]) {
            if (!m.unreadMessagesExist && !document.hasFocus()) {
                m.unreadMessagesExist = true;
            } else if (document.hasFocus() && m.unreadMessagesExist) {
                m.sendMarkDialogAsRead();
            }
        }
    } else if (command === "get_messages") {
        console.info("messages:", data["messages"]);
        const messages = data["messages"];
        const messagesNodes = [];
        for (const message of messages) {
            if (message["is_unread"]) {
                m.unreadMessagesExist = true;
            }
            messagesNodes.push(m.createMessageNode(message));
        }
        dialogHolder.replaceChildren(...messagesNodes);

        if (document.hasFocus() && m.unreadMessagesExist) {
            m.sendMarkDialogAsRead();
        }
    } else if (command === "check_integrity") {
        m.checkIntegrity(data["integrity_hash"]);
    } else if (command === "go_home") {
        window.location.href = "/home/";
    } else {
        console.warn("Invalid command");
    }
}


////////
m.createMessageNode = function(message) {
    console.info("createMessageNode", message["text"]);
    const messageNode = document.createElement("pre");
    messageNode.classList.add("message");
    messageNode.dataset.hash = message["hash"];
    messageNode.dataset.time = message["time"] + "Z";

    let ownershipStr;
    if (message["user_owns_message"]) {
        ownershipStr = "(from me)";
    } else {
        ownershipStr = "(to me)";
    }

    const timeNode = document.createElement("b");
    timeNode.classList.add("time");
    messageNode.append(timeNode);
    const time = new Date(messageNode.dataset.time);
    let timeStr;
    function pad(x) {
        return ("0" + x).slice(-2);
    }
    if (time.toDateString() === (new Date()).toDateString()) {
        timeStr = time.toTimeString().slice(0, 5);
    } else {
        timeStr = `${pad(time.getDate())}.${pad(time.getMonth() + 1)}`;
    }
    timeNode.appendChild(document.createTextNode(timeStr));

    const htmlText = ` ${ownershipStr}: ${message["text"]}`;
    const textNode = document.createTextNode(htmlText);
    messageNode.appendChild(textNode);

    return messageNode;
};

m.sendMarkDialogAsRead = function() {
    console.info("Send mark_dialog_as_read");
    m.unreadMessagesExist = false;
    socket.send(JSON.stringify({
        "command": "mark_dialog_as_read"
    }));
};


m.checkIntegrity = function(serverIntegrityHash) {
    console.info("checkIntegrity");
    let integrityHash = 0;
    document.querySelectorAll(".message").forEach(
        messageNode => integrityHash += parseInt(
            messageNode.dataset.hash,
            10
        )
    );

    if (integrityHash !== serverIntegrityHash) {
        console.info("Send give_messages");
        socket.send(JSON.stringify({
            "command": "give_messages"
        }));
    }
};


////////
/* istanbul ignore next */
if (navigator.userAgent.includes("jsdom")) {
    module.exports = {
        wsUrl: wsUrl,
        form: form,
        formOnSubmitHandler: formOnSubmitHandler,
        socket: socket,
        textInput: textInput,
        connect: connect,
        focusHandler: focusHandler,
        socketOnMessageHandler: socketOnMessageHandler,
        m: m
    };
}
