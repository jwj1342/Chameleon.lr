local LrFileUtils = import "LrFileUtils"
local LrTasks = import "LrTasks"

local Config = require "modules/Config.lua"
local Json = require "modules/Json.lua"
local logger = require "modules/Logger.lua"

local EngineClient = {}

local function quoteArgument(value)
	value = tostring(value)
	if value:find("[%z\r\n]") then
		error("engine command contains an invalid control character")
	end
	if WIN_ENV then
		if value:find('"', 1, true) then
			error("Windows command arguments cannot contain a quote")
		end
		return '"' .. value .. '"'
	end
	return "'" .. value:gsub("'", "'\\''") .. "'"
end

local function commandFor(arguments)
	local prefs = Config.preferences()
	local parts
	if prefs.engineMode == "executable" then
		if not LrFileUtils.exists(prefs.engineExecutable) then
			error("Engine executable not found: " .. tostring(prefs.engineExecutable))
		end
		parts = { quoteArgument(prefs.engineExecutable) }
	elseif prefs.engineMode == "script" then
		if not LrFileUtils.exists(prefs.engineScript) then
			error("Engine script not found: " .. tostring(prefs.engineScript))
		end
		parts = {
			quoteArgument(prefs.pythonExecutable),
			quoteArgument(prefs.engineScript),
		}
	else
		error("Unknown engine mode: " .. tostring(prefs.engineMode))
	end
	for _, argument in ipairs(arguments) do
		parts[#parts + 1] = quoteArgument(argument)
	end
	return table.concat(parts, " ")
end

local function firstError(response)
	if type(response.errors) == "table" and type(response.errors[1]) == "table" then
		return response.errors[1].message
	end
	return nil
end

function EngineClient.run(requestPath, responsePath)
	local command = commandFor({
		"fit",
		"--request", requestPath,
		"--output", responsePath,
	})
	logger:trace("Starting engine request")
	local status = LrTasks.execute(command)
	if not LrFileUtils.exists(responsePath) then
		error("Engine exited with status " .. tostring(status) .. " without a response")
	end

	local encoded = LrFileUtils.readFile(responsePath)
	local ok, response = pcall(Json.decode, encoded)
	if not ok then
		error("Engine returned invalid JSON: " .. tostring(response))
	end
	if status ~= 0 then
		error(firstError(response) or ("Engine exited with status " .. tostring(status)))
	end
	if response.status ~= "ok" and response.status ~= "partial" then
		error(firstError(response) or "Engine rejected the request")
	end
	return response
end

function EngineClient.health()
	local status = LrTasks.execute(commandFor({ "health", "--json" }))
	if status == 0 then
		return true, "Engine is ready"
	end
	return false, "Engine exited with status " .. tostring(status)
end

return EngineClient
