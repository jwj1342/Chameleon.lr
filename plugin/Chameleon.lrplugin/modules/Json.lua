-- Small dependency-free JSON codec compatible with Lightroom's Lua 5.1 runtime.
local Json = { null = {} }

local escapes = {
	['"'] = '\\"',
	['\\'] = '\\\\',
	['\b'] = '\\b',
	['\f'] = '\\f',
	['\n'] = '\\n',
	['\r'] = '\\r',
	['\t'] = '\\t',
}

local function encodeString(value)
	return '"' .. value:gsub('[%z\1-\31\\"]', function(character)
		return escapes[character] or string.format("\\u%04x", string.byte(character))
	end) .. '"'
end

local function isArray(value)
	local count = 0
	local maximum = 0
	for key, _ in pairs(value) do
		if type(key) ~= "number" or key < 1 or key % 1 ~= 0 then
			return false
		end
		count = count + 1
		maximum = math.max(maximum, key)
	end
	return count > 0 and maximum == count
end

local function encodeValue(value, stack)
	local valueType = type(value)
	if value == Json.null or valueType == "nil" then
		return "null"
	elseif valueType == "boolean" then
		return value and "true" or "false"
	elseif valueType == "number" then
		if value ~= value or value == math.huge or value == -math.huge then
			error("cannot encode a non-finite JSON number")
		end
		return string.format("%.17g", value)
	elseif valueType == "string" then
		return encodeString(value)
	elseif valueType ~= "table" then
		error("cannot encode JSON value of type " .. valueType)
	end

	if stack[value] then
		error("cannot encode a cyclic table")
	end
	stack[value] = true

	local result = {}
	if isArray(value) then
		for index = 1, #value do
			result[index] = encodeValue(value[index], stack)
		end
		stack[value] = nil
		return "[" .. table.concat(result, ",") .. "]"
	end

	local keys = {}
	for key, _ in pairs(value) do
		if type(key) ~= "string" then
			error("JSON object keys must be strings")
		end
		keys[#keys + 1] = key
	end
	table.sort(keys)
	for index, key in ipairs(keys) do
		result[index] = encodeString(key) .. ":" .. encodeValue(value[key], stack)
	end
	stack[value] = nil
	return "{" .. table.concat(result, ",") .. "}"
end

function Json.encode(value)
	return encodeValue(value, {})
end

local function decodeError(position, message)
	error(string.format("invalid JSON at byte %d: %s", position, message), 0)
end

local function utf8(character)
	if character <= 0x7f then
		return string.char(character)
	elseif character <= 0x7ff then
		return string.char(
			0xc0 + math.floor(character / 0x40),
			0x80 + (character % 0x40)
		)
	elseif character <= 0xffff then
		return string.char(
			0xe0 + math.floor(character / 0x1000),
			0x80 + (math.floor(character / 0x40) % 0x40),
			0x80 + (character % 0x40)
		)
	end
	return string.char(
		0xf0 + math.floor(character / 0x40000),
		0x80 + (math.floor(character / 0x1000) % 0x40),
		0x80 + (math.floor(character / 0x40) % 0x40),
		0x80 + (character % 0x40)
	)
end

local function skipWhitespace(text, position)
	local _, last = text:find("^[ \n\r\t]*", position)
	return (last or position - 1) + 1
end

local parseValue

local function parseString(text, position)
	local result = {}
	position = position + 1
	while position <= #text do
		local character = text:sub(position, position)
		if character == '"' then
			return table.concat(result), position + 1
		elseif character == "\\" then
			local escaped = text:sub(position + 1, position + 1)
			local simple = {
				['"'] = '"', ['\\'] = '\\', ['/'] = '/',
				b = '\b', f = '\f', n = '\n', r = '\r', t = '\t',
			}
			if simple[escaped] then
				result[#result + 1] = simple[escaped]
				position = position + 2
			elseif escaped == "u" then
				local hex = text:sub(position + 2, position + 5)
				if not hex:match("^%x%x%x%x$") then
					decodeError(position, "invalid unicode escape")
				end
				local codepoint = tonumber(hex, 16)
				position = position + 6
				if codepoint >= 0xd800 and codepoint <= 0xdbff then
					local lowHex = text:match("^\\u(%x%x%x%x)", position)
					local low = lowHex and tonumber(lowHex, 16) or nil
					if not low or low < 0xdc00 or low > 0xdfff then
						decodeError(position, "missing low unicode surrogate")
					end
					codepoint = 0x10000 + (codepoint - 0xd800) * 0x400 + (low - 0xdc00)
					position = position + 6
				elseif codepoint >= 0xdc00 and codepoint <= 0xdfff then
					decodeError(position, "unexpected low unicode surrogate")
				end
				result[#result + 1] = utf8(codepoint)
			else
				decodeError(position, "invalid escape")
			end
		else
			if string.byte(character) < 32 then
				decodeError(position, "control character in string")
			end
			result[#result + 1] = character
			position = position + 1
		end
	end
	decodeError(position, "unterminated string")
end

local function parseArray(text, position)
	local result = {}
	position = skipWhitespace(text, position + 1)
	if text:sub(position, position) == "]" then
		return result, position + 1
	end
	while true do
		local value
		value, position = parseValue(text, position)
		result[#result + 1] = value
		position = skipWhitespace(text, position)
		local character = text:sub(position, position)
		if character == "]" then
			return result, position + 1
		elseif character ~= "," then
			decodeError(position, "expected ',' or ']'")
		end
		position = skipWhitespace(text, position + 1)
	end
end

local function parseObject(text, position)
	local result = {}
	position = skipWhitespace(text, position + 1)
	if text:sub(position, position) == "}" then
		return result, position + 1
	end
	while true do
		if text:sub(position, position) ~= '"' then
			decodeError(position, "expected string key")
		end
		local key
		key, position = parseString(text, position)
		position = skipWhitespace(text, position)
		if text:sub(position, position) ~= ":" then
			decodeError(position, "expected ':'")
		end
		local value
		value, position = parseValue(text, skipWhitespace(text, position + 1))
		result[key] = value
		position = skipWhitespace(text, position)
		local character = text:sub(position, position)
		if character == "}" then
			return result, position + 1
		elseif character ~= "," then
			decodeError(position, "expected ',' or '}'")
		end
		position = skipWhitespace(text, position + 1)
	end
end

parseValue = function(text, position)
	position = skipWhitespace(text, position)
	local character = text:sub(position, position)
	if character == '"' then
		return parseString(text, position)
	elseif character == "[" then
		return parseArray(text, position)
	elseif character == "{" then
		return parseObject(text, position)
	end

	local literals = { ["true"] = true, ["false"] = false, ["null"] = Json.null }
	for literal, value in pairs(literals) do
		if text:sub(position, position + #literal - 1) == literal then
			return value, position + #literal
		end
	end

	local token = text:match("^-?%d+%.?%d*[eE]?[+-]?%d*", position)
	if token and token ~= "" then
		local value = tonumber(token)
		if value then
			return value, position + #token
		end
	end
	decodeError(position, "unexpected token")
end

function Json.decode(text)
	if type(text) ~= "string" then
		error("JSON input must be a string")
	end
	local value, position = parseValue(text, 1)
	position = skipWhitespace(text, position)
	if position <= #text then
		decodeError(position, "trailing data")
	end
	return value
end

return Json
