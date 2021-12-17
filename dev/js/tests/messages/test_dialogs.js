import * as utils from "messages/js/utils.js";

const serializer = require("custom-serializer");
expect.addSnapshotSerializer(serializer);

let dialogs;
let dialogsHolder;
let dialogsLink; document.getElementById("dialogs-link");

function loadModule() {
    jest.isolateModules(() => {
        dialogs = require("messages/js/dialogs.js");
        dialogs.socket.close();
        dialogs.socket.send = jest.fn();
    });
}

function standartSetUpDialogs() {
    const dialog = {
        "id": 1, "hash": 300, "is_unread": false,
        "text": "some text"
    };

    dialogsHolder.appendChild(dialogs.m.createDialogNode(dialog));
    dialog["id"] = 2;
    dialog["hash"] = 200;
    dialog["is_unread"] = true;
    dialogsHolder.appendChild(dialogs.m.createDialogNode(dialog));
}


beforeEach(() => {
    document.body.innerHTML =
`<a href="/url/" id="dialogs-link">Dialogs</a>
<div id="dialogs"></div>`;

    loadModule();
    dialogsHolder = document.getElementById("dialogs");
    dialogsLink = document.getElementById("dialogs-link");
    console.warn = jest.fn();
});


test("wsUrl", () => {
    expect(dialogs.wsUrl).toBe(utils.getWsUrl());
});

test("connect", () => {
    expect(dialogs.socket.onmessage).toBe(dialogs.socketOnMessageHandler);
});

describe("socketOnMessageHandler", () => {
    test("invalid", () => {
        let ev = {data: JSON.stringify({})};
        dialogs.socketOnMessageHandler(ev);
        expect(console.warn.mock.calls[0][0]).toBe("invalid data");

        ev = {data: JSON.stringify({"command": "pampam"})};
        dialogs.socketOnMessageHandler(ev);
        expect(console.warn.mock.calls[1][0]).toBe("Invalid command");
    });

    describe("get_new_message", () => {
        const data = {
            "command": "get_new_message",
            "dialog": {
                "id": 2, "hash": 400, "is_unread": true,
                "text": "some text"
            }
        };

        test("dialog existed", () => {
            standartSetUpDialogs();
            jest.spyOn(dialogs.m, "checkIntegrity");
            jest.spyOn(dialogs.m, "updateDialogsLink");

            dialogs.socketOnMessageHandler({data: JSON.stringify(data)});
            expect(dialogs.m.checkIntegrity).toHaveBeenCalledTimes(1);
            expect(dialogs.m.updateDialogsLink).toHaveBeenCalledTimes(1);
            expect(document.body).toMatchSnapshot();
        });

        test("dialog didn't exist", () => {
            dialogs.socketOnMessageHandler({data: JSON.stringify(data)});
            expect(document.body).toMatchSnapshot();
        });
    });

    test("delete_dialog", () => {
        standartSetUpDialogs();
        jest.spyOn(dialogs.m, "checkIntegrity");
        jest.spyOn(dialogs.m, "updateDialogsLink");
        const data = {
            "command": "delete_dialog",
            "dialog_id": 1
        };

        dialogs.socketOnMessageHandler({data: JSON.stringify(data)});
        expect(dialogs.m.checkIntegrity).toHaveBeenCalledTimes(1);
        expect(dialogs.m.updateDialogsLink).toHaveBeenCalledTimes(1);
        expect(document.body).toMatchSnapshot();

        data["dialog_id"] = 2;
        dialogs.socketOnMessageHandler({data: JSON.stringify(data)});
        expect(document.body).toMatchSnapshot();
    });

    test("get_dialogs", () => {
        standartSetUpDialogs();
        jest.spyOn(dialogs.m, "updateDialogsLink");
        const data = {
            "command": "get_dialogs",
            "dialogs": [
                {
                    "id": 2, "hash": 500, "is_unread": true,
                    "text": "some text"
                }
            ]
        };

        dialogs.socketOnMessageHandler({data: JSON.stringify(data)});
        expect(dialogs.m.updateDialogsLink).toHaveBeenCalledTimes(1);
        expect(document.body).toMatchSnapshot();
    });

    test("mark_dialog_as_read", () => {
        standartSetUpDialogs();
        jest.spyOn(dialogs.m, "checkIntegrity");
        jest.spyOn(dialogs.m, "updateDialogsLink");
        const data = {
            "command": "mark_dialog_as_read",
            "dialog_id": 2
        };

        dialogs.socketOnMessageHandler({data: JSON.stringify(data)});
        expect(dialogs.m.updateDialogsLink).toHaveBeenCalledTimes(1);
        expect(dialogs.m.checkIntegrity).toHaveBeenCalledTimes(1);
        expect(document.body).toMatchSnapshot();
    });

    test("check_integrity", () => {
        dialogs.m.checkIntegrity = jest.fn();
        const ev = {data: JSON.stringify({
            "command": "check_integrity",
            "integrity_hash": 100
        })};

        dialogs.socketOnMessageHandler(ev);
        expect(dialogs.m.checkIntegrity.mock.calls[0][0]).toBe(100);
    });

    test("go_home", () => {
        const oldValue = window.location;
        delete window.location;
        window.location = {href: ""};
        const ev = {data: JSON.stringify({"command": "go_home"})};

        dialogs.socketOnMessageHandler(ev);
        expect(window.location.href).toBe("/home/");

        window.location = oldValue;
    });
});

test("sendDeleteDialog", () => {
    const ev = {
        preventDefault: jest.fn(),
        "srcElement": {id: 123}
    };

    dialogs.m.sendDeleteDialog(ev);
    expect(ev.preventDefault).toHaveBeenCalled();
    expect(dialogs.socket.send.mock.calls[0][0]).toEqual(
        JSON.stringify({
            "command": "delete_dialog",
            "dialog_id": 123
        })
    );
});

test("createDialogNode", () => {
    const dialog = {
        "id": 3, "hash": 321, "is_unread": false,
        "text": "some text"
    };
    let dialogNode = dialogs.m.createDialogNode(dialog);
    expect(dialogNode).toMatchSnapshot();

    dialog["is_unread"] = true;
    dialogNode = dialogs.m.createDialogNode(dialog);
    expect(dialogNode).toMatchSnapshot();
});

test("checkIntegrity", () => {
    standartSetUpDialogs();

    dialogs.m.checkIntegrity(501);
    expect(dialogs.socket.send).toHaveBeenCalledTimes(0);

    dialogs.m.checkIntegrity(500);
    expect(dialogs.socket.send.mock.calls[0][0]).toBe(
        JSON.stringify({"command": "give_dialogs"})
    );
});

describe("updateDialogsLink", () => {
    test("no unread", () => {
        dialogsLink.classList.add("unread-dialogs-exist");
        dialogs.m.updateDialogsLink();
        expect(dialogsLink).toMatchSnapshot();
    });

    test("with unread", () => {
        standartSetUpDialogs();

        dialogs.m.updateDialogsLink();
        expect(dialogsLink).toMatchSnapshot();
    });
});
