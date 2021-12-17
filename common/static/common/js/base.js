const isDebugStr = document.getElementById("is_debug").dataset.isDebug;

const emptyFunc = function() {};
if (isDebugStr === "false") {
    console.log = console.info = console.error = console.debug = emptyFunc;
}

////////
async function reloadWrapper() {
    location.reload();
}

window.onerror = function() {
    const timeout = 5000;
    const message = (
        `Something happened.\n`
        + `The page will be reloaded after ${timeout/1000} sec`
    );
    const notificationNode = document.createElement("div");
    notificationNode.classList.add("notification", "error");
    notificationNode.innerHTML = message;
    document.body.prepend(notificationNode);

    setTimeout(
        reloadWrapper,
        timeout
    );
};


////////
window.addEventListener("storage", storageMessageHandler);

const logoutLink = document.getElementById("logout");
logoutLink.onclick = broadcastAboutLogout;

function broadcastAboutLogout() {
    localStorage.setItem("logout", "true");
    localStorage.removeItem("logout");
}

function storageMessageHandler(ev) {
    console.info("storageMessageHandler: ", ev);
    if (ev.key === "logout") {
        window.location.reload();
    } else {
        console.error("Invalid command");
    }
}


////////
/* istanbul ignore next */
if (navigator.userAgent.includes("jsdom")) {
    module.exports = {
        isDebugStr: isDebugStr,
        logoutLink: logoutLink,
        broadcastAboutLogout: broadcastAboutLogout,
        storageMessageHandler: storageMessageHandler,
        emptyFunc: emptyFunc,
        reloadWrapper: reloadWrapper,
    };
}
