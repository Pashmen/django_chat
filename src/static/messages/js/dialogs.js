import {CustomWebSocket, getWsUrl} from "./utils.js";


const wsUrl = getWsUrl();
let socket;

const dialogsHolder = document.getElementById("dialogs");
const dialogsLink = document.getElementById("dialogs-link");
dialogsLink.classList.add("in-dialogs");
const m = {};

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
        const dialog = data["dialog"];
        const dialogNode = document.getElementById(dialog["id"]);

        if (dialogNode !== null) {
            dialogNode.parentNode.removeChild(dialogNode);
        }
        dialogsHolder.prepend(m.createDialogNode(dialog));
        m.updateDialogsLink();
        m.checkIntegrity(data["integrity_hash"]);
    } else if (command === "delete_dialog") {
        const dialogId = data["dialog_id"];
        const dialogNode = document.getElementById(dialogId);
        dialogNode.parentNode.removeChild(dialogNode);
        m.updateDialogsLink();
        m.checkIntegrity(data["integrity_hash"]);
    } else if (command === "get_dialogs") {
        const dialogs = data["dialogs"];
        const dialogsNodes = [];
        for (var dialog of dialogs) {
            dialogsNodes.push(m.createDialogNode(dialog));
        }
        dialogsHolder.replaceChildren(...dialogsNodes);
        m.updateDialogsLink();
    } else if (command === "mark_dialog_as_read") {
        const dialog = document.getElementById(data["dialog_id"]);
        dialog.firstChild.classList.remove("is-unread");
        m.updateDialogsLink();
        m.checkIntegrity(data["integrity_hash"]);
    } else if (command === "check_integrity") {
        m.checkIntegrity(data["integrity_hash"]);
    } else if (command === "go_home") {
        window.location.href = "/home/";
    } else {
        console.warn("Invalid command");
    }
}


////////
m.sendDeleteDialog = function(ev) {
    console.info("Send delete_dialog");
    ev.preventDefault();
    socket.send(JSON.stringify({
        "command": "delete_dialog",
        "dialog_id": ev["srcElement"].id
    }));
};


m.createDialogNode = function(dialog) {
    console.info("createDialogNode", dialog["id"]);

    const dialogNode = document.createElement("form");
    dialogNode.onsubmit = m.sendDeleteDialog;
    dialogNode.classList.add("dialog");
    dialogNode.setAttribute("id", dialog["id"]);
    dialogNode.dataset.hash = dialog["hash"];

    const linkNode = document.createElement("a");
    dialogNode.appendChild(linkNode);
    linkNode.setAttribute("href", `/dialogs/u${dialog["id"]}`);

    if (dialog["is_unread"]) {
        linkNode.classList.add("is-unread");
    }
    var textNode = document.createTextNode(
        `${dialog["id"]}: ${dialog["text"]}`
    );
    linkNode.appendChild(textNode);

    const submitNode = document.createElement("button");
    dialogNode.appendChild(submitNode);
    submitNode.setAttribute("type", "submit");
    submitNode.setAttribute("name", "Delete");
    submitNode.appendChild(document.createTextNode("x"));

    dialogNode.appendChild(document.createElement("br"));

    return dialogNode;
};


m.checkIntegrity = function(serverIntegrityHash) {
    console.info("checkIntegrity");
    let integrityHash = 0;
    document.querySelectorAll(".dialog").forEach(
        dialogNode => {
            integrityHash += parseInt(
                dialogNode.dataset.hash,
                10
            );
        }
    );
    const unreadDialogsNumber = document.querySelectorAll(".is-unread").length;
    integrityHash += unreadDialogsNumber;

    if (integrityHash !== serverIntegrityHash) {
        console.info("Send give_dialogs");
        socket.send(JSON.stringify({
            "command": "give_dialogs"
        }));
    }
};


m.updateDialogsLink = function() {
    console.info("updateDialogsLink");
    const unreadDialogsNumber = document.querySelectorAll(".is-unread").length;
    const dialogsName = dialogsLink.innerHTML.split(" ")[0];
    if (unreadDialogsNumber === 0) {
        dialogsLink.classList.remove("unread-dialogs-exist");
        dialogsLink.firstChild.replaceWith(
            document.createTextNode(dialogsName)
        );
    } else  {
        dialogsLink.classList.add("unread-dialogs-exist");
        dialogsLink.firstChild.replaceWith(
            document.createTextNode(`${dialogsName} (${unreadDialogsNumber})`)
        );
    }
};


////////
/* istanbul ignore next */
if (navigator.userAgent.includes("jsdom")) {
    module.exports = {
        wsUrl: wsUrl,
        socket: socket,
        connect: connect,
        socketOnMessageHandler: socketOnMessageHandler,
        m: m
    };
}
