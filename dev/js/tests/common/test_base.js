const serializer = require("custom-serializer");
expect.addSnapshotSerializer(serializer);


let base;

function loadModule() {
    jest.isolateModules(() => {
        base = require("common/js/base");
    });
}


beforeEach(() => {
    document.body.innerHTML =
`<a href="/url" id="logout">Log Out</a>
<div id="is_debug" data-is-debug="true"></div>`;
});


test("isDebugStr", () => {
    loadModule();
    expect(base.isDebugStr).toBe("true");
});

test("console.log", () => {
    document.body.innerHTML = `
        <a href="/url" id="logout">Log Out</a>
        <div id="is_debug" data-is-debug="false"></div>
    `;
    const bufConsoleLog = console.log;
    const bufConsoleInfo = console.info;
    const bufConsoleError = console.error;
    const bufConsoleDebug = console.debug;

    loadModule();
    expect(console.log).toBe(base.emptyFunc);
    expect(console.info).toBe(base.emptyFunc);
    expect(console.error).toBe(base.emptyFunc);
    expect(console.debug).toBe(base.emptyFunc);

    console.log = bufConsoleLog;
    console.info = bufConsoleInfo;
    console.error = bufConsoleError;
    console.debug = bufConsoleDebug;
});

test("reloadWrapper", async () => {
    loadModule();
    const location = window.location;
    delete window.location;
    window.location = {reload: jest.fn()};

    await base.reloadWrapper();
    expect(window.location.reload).toHaveBeenCalled();

    window.location = location;
});

test("Handling errors with window.onerror", () => {
    global.setTimeout = jest.fn();

    loadModule();
    window.onerror();
    expect(document.body).toMatchSnapshot();
    expect(setTimeout.mock.calls[0][0].toString()).toBe(
        base.reloadWrapper.toString()
    );
    expect(setTimeout.mock.calls[0][1]).toBe(5000);
});

describe("logout", () => {
    test("addEventListener: storage", () => {
        const spy = jest.spyOn(window, "addEventListener");

        loadModule();
        expect(spy.mock.calls[0]).toEqual(
            ["storage", base.storageMessageHandler]
        );
    });

    test("logoutLink", () => {
        loadModule();
        jest.spyOn(base.logoutLink, "onclick", "set");
        loadModule();

        expect(base.logoutLink).toBe(
            document.getElementById("logout")
        );
        expect(base.logoutLink.onclick).toBe(base.broadcastAboutLogout);
    });

    test("broadcastAboutLogout", () => {
        loadModule();
        const spySet = jest.spyOn(Storage.prototype, "setItem");
        const spyRemove = jest.spyOn(Storage.prototype, "removeItem");

        base.broadcastAboutLogout();
        expect(spySet.mock.calls[0]).toEqual(["logout", "true"]);
        expect(spyRemove.mock.calls[0][0]).toBe("logout");
    });

    test("storageMessageHandler", () => {
        loadModule();
        const spyConsoleError = jest.spyOn(console, "error");
        const location = window.location;
        delete window.location;
        window.location = {reload: jest.fn()};

        base.storageMessageHandler({key: "logout"});
        expect(window.location.reload).toHaveBeenCalled();

        base.storageMessageHandler({key: "invalid"});
        expect(spyConsoleError).toHaveBeenCalled();

        window.location = location;
    });
});
