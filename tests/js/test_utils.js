import * as utils from "messages/js/utils.js";


describe("CustomWebSocket constructor", () => {
    test("onclose", () => {
        global.setTimeout = jest.fn();
        const connect = jest.fn();
        const customWS = new utils.CustomWebSocket("ws://a.com/", connect);

        customWS.onclose();
        expect(setTimeout.mock.calls[0][0]).toBe(connect);
        expect(setTimeout.mock.calls[0][1]).toBe(3000);
    });
});

test("GetWsUrl", () => {
    const oldValue = window.location;
    delete window.location;
    window.location = {
        protocol: "http", host: "host", pathname: "/path/"
    };

    expect(utils.getWsUrl()).toBe("ws://host/ws/path/");

    window.location = oldValue;
});
