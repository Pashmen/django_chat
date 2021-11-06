class CustomWebSocket extends WebSocket {
    constructor(url, connect) {
        super(url);

        this.onopen = function(e) {
            console.info("ws open", e);
        };

        this.onclose = function (e) {
            const timeout = 3000;
            console.info("ws close", e);
            setTimeout(connect, timeout);
        };

        this.onerror = function (e) {
            console.error("ws error", e);
        };
    }
}

function getWsUrl() {
    const loc = window.location;
    let wsStart = "ws://";
    if (loc.protocol === "https") {
        wsStart = "wss://";
    }

    return wsStart + loc.host + "/ws" + loc.pathname;
}

////////
export {
    CustomWebSocket,
    getWsUrl
};
