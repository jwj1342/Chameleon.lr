local Json = dofile("plugin/Chameleon.lrplugin/modules/Json.lua")

local source = {
	request_id = "test-1",
	active = true,
	value = 1.25,
	label = "line\n\"quoted\"",
	items = { 1, 2, 3 },
	nested = { alpha = "beta" },
}

local encoded = Json.encode(source)
local decoded = Json.decode(encoded)

assert(decoded.request_id == source.request_id)
assert(decoded.active == true)
assert(decoded.value == 1.25)
assert(decoded.label == source.label)
assert(#decoded.items == 3 and decoded.items[3] == 3)
assert(decoded.nested.alpha == "beta")
assert(Json.decode('"\\u4f60\\u597d"') == "你好")

local ok = pcall(Json.decode, '{"broken":]')
assert(ok == false)
