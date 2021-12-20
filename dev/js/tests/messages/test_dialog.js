import * as utils from "messages/js/utils.js";

const serializer = require("custom-serializer");
expect.addSnapshotSerializer(serializer);

let dialog;

function loadModule() {
    jest.isolateModules(() => {
        dialog = require("messages/js/dialog.js");
        dialog.socket.close();
        dialog.socket.send = jest.fn();
    });
}

let dialogHolder;


beforeEach(() => {
    document.body.innerHTML =
`<div id="dialog-messages"></div>
<form id="form">
  <p>
    <textarea name="text" maxlength="400" required id="id_text">
message_text</textarea>
  </p>
  <button type="submit" name="Send"> Send </button>
</form>`;

    loadModule();
    dialogHolder = document.getElementById("dialog-messages");
    console.warn = jest.fn();
});


test("wsUrl", () => {
    expect(dialog.wsUrl).toBe(utils.getWsUrl());
});

test("form.onsubmit", () => {
    expect(dialog.form.onsubmit).toBe(dialog.formOnSubmitHandler);
});

test("formOnSubmitHandler", () => {
    const ev = {
        preventDefault: jest.fn()
    };

    dialog.formOnSubmitHandler(ev);
    expect(ev.preventDefault).toHaveBeenCalled();
    expect(dialog.socket.send.mock.calls[0][0]).toEqual(
        JSON.stringify({
            "command": "get_new_message",
            "message": {
                "text": "message_text"
            }
        })
    );
    expect(dialog.textInput.value).toBe("");
});


describe("focus", () => {
    test("window.addEventListener", () => {
        const spy = jest.spyOn(window, "addEventListener");
        loadModule();
        expect(spy.mock.calls[0]).toEqual(
            ["focus", dialog.focusHandler]
        );
    });

    test("focusHandler", () => {
        dialog.m.sendMarkDialogAsRead = jest.fn();

        dialog.m.unreadMessagesExist = false;
        dialog.focusHandler();
        expect(dialog.m.sendMarkDialogAsRead).toHaveBeenCalledTimes(0);

        dialog.m.unreadMessagesExist = true;
        dialog.focusHandler();
        expect(dialog.m.sendMarkDialogAsRead).toHaveBeenCalledTimes(1);
    });
});

test("connect", () => {
    expect(dialog.socket.onmessage).toBe(dialog.socketOnMessageHandler);
});

describe("socketOnMessageHandler", () => {
    test("invalid", () => {
        let ev = {data: JSON.stringify({})};
        dialog.socketOnMessageHandler(ev);
        expect(console.warn.mock.calls[0][0]).toBe("invalid data");

        ev = {data: JSON.stringify({"command": "pampam"})};
        dialog.socketOnMessageHandler(ev);
        expect(console.warn.mock.calls[1][0]).toBe("Invalid command");
    });

    describe("get_new_message", () => {
        const message = {
            "text": "text1", "hash": 500,
            "user_owns_message": true, "time": "2021.07.01 05:27",
            "is_unread": true
        };
        const data = {
            "command": "get_new_message",
            "message": message
        };

        test("1 case", () => {
            jest.spyOn(dialog.m, "checkIntegrity");
            document.hasFocus = jest.fn(() => {return false;});

            dialog.socketOnMessageHandler({data: JSON.stringify(data)});
            expect(dialog.m.checkIntegrity).toHaveBeenCalledTimes(1);
            expect(dialog.m.unreadMessagesExist).toBe(true);
        });

        test("2 case", () => {
            document.hasFocus = jest.fn(() => {return true;});
            dialog.m.unreadMessagesExist = true;
            jest.spyOn(dialog.m, "sendMarkDialogAsRead");

            dialog.socketOnMessageHandler({data: JSON.stringify(data)});
            expect(dialog.m.sendMarkDialogAsRead).toHaveBeenCalledTimes(1);
        });
    });

    describe("get_messages", () => {
        const message1 = {
            "text": "text1", "hash": 500,
            "user_owns_message": true, "time": "2021.07.02 00:37",
            "is_unread": false
        };
        const message2 = {
            "text": "text2", "hash": 400,
            "user_owns_message": false, "time": "2021.02.02 00:27",
            "is_unread": false
        };
        const data = {
            "command": "get_messages",
        };

        test("replacement", () => {
            dialogHolder.appendChild(dialog.m.createMessageNode(message1));
            data["messages"] = [message2];

            dialog.socketOnMessageHandler({data: JSON.stringify(data)});
            expect(dialogHolder).toMatchSnapshot();
        });

        test("no send", () => {
            dialog.m.sendMarkDialogAsRead = jest.fn();
            message1["is_unread"] = false;
            message2["is_unread"] = false;
            data["messages"] = [message1, message2];

            dialog.socketOnMessageHandler({data: JSON.stringify(data)});
            expect(dialogHolder).toMatchSnapshot();
            expect(dialog.m.sendMarkDialogAsRead).toHaveBeenCalledTimes(0);
        });

        test("with send", () => {
            dialog.m.sendMarkDialogAsRead = jest.fn();
            document.hasFocus = jest.fn(() => {return true;});
            message1["is_unread"] = false;
            message2["is_unread"] = true;
            data["messages"] = [message1, message2];

            dialog.socketOnMessageHandler({data: JSON.stringify(data)});
            expect(dialog.m.sendMarkDialogAsRead).toHaveBeenCalledTimes(1);
        });
    });

    test("check_integrity", () => {
        dialog.m.checkIntegrity = jest.fn();
        const ev = {data: JSON.stringify({
            "command": "check_integrity",
            "integrity_hash": 100
        })};

        dialog.socketOnMessageHandler(ev);
        expect(dialog.m.checkIntegrity.mock.calls[0][0]).toBe(100);
    });

    test("go_home", () => {
        const oldValue = window.location;
        delete window.location;
        window.location = {href: ""};
        const ev = {data: JSON.stringify({"command": "go_home"})};

        dialog.socketOnMessageHandler(ev);
        expect(window.location.href).toBe("/account/");

        window.location = oldValue;
    });
});

test("createMessageNode", () => {
    const oldDate = Date;
    const date = new Date(Date.UTC(2020, 9, 20));
    jest.spyOn(global, "Date").mockImplementation(
        (args) => {
            if (args !== undefined) {
                return new oldDate(args);
            } else {
                return date;
            }
        }
    );
    let message = {
        "text": "text1", "hash": 200,
        "user_owns_message": true, "time": "2020.10.19 20:59"
    };
    let messageNode = dialog.m.createMessageNode(message);
    expect(messageNode).toMatchSnapshot();

    message = {
        "text": "text2", "hash": 400,
        "user_owns_message": false, "time": "2020.10.19 21:01"
    };
    messageNode = dialog.m.createMessageNode(message);
    expect(messageNode).toMatchSnapshot();
});

test("sendMarkDialogAsRead", () => {
    dialog.m.sendMarkDialogAsRead();
    expect(dialog.m.unreadMessagesExist).toBe(false);
    expect(dialog.socket.send.mock.calls[0][0]).toEqual(
        JSON.stringify({"command": "mark_dialog_as_read"})
    );
});

test("checkIntegrity", () => {
    const message = {
        "text": "text", "hash": 200,
        "user_owns_message": true, "time": "2021.01.01 00:37"
    };
    dialogHolder.appendChild(dialog.m.createMessageNode(message));
    message["hash"] = 300;
    dialogHolder.appendChild(dialog.m.createMessageNode(message));

    dialog.m.checkIntegrity(500);
    expect(dialog.socket.send).toHaveBeenCalledTimes(0);

    dialog.m.checkIntegrity(501);
    expect(dialog.socket.send.mock.calls[0][0]).toBe(
        JSON.stringify({"command": "give_messages"})
    );
});
