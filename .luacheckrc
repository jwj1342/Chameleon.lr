std = "lua51"
max_line_length = 120

read_globals = {
    "import",
    "_PLUGIN",
    "WIN_ENV",
    "MAC_ENV",
}

files["tests/lua/**"] = {
    unused_args = false,
    globals = {
        "import",
        "require",
        "_PLUGIN",
        "WIN_ENV",
        "MAC_ENV",
    },
}
