window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: {
        inject_xterm_js: (timeoutCount, mount_id) => {
            var term = new Terminal();
            term.open(document.getElementById(mount_id));
        }
    }
});