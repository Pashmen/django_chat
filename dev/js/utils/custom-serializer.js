const prettier = require("prettier");

module.exports = {
    test(value) {
        return value instanceof Element;
    },
    print(value) {
        const s = prettier.format(
            value.outerHTML, {parser: "html"}
        );
        if (s.split("\n").length === 2) {
            return s;
        } else {
            return s.trimEnd();
        }
    }
};
