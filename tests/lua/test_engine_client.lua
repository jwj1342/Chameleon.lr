local Mock = dofile("tests/lua/LrSDK_Mock.lua")
local reference = Mock.photo(1, "reference.jpg", {})
local state = Mock.install {
	reference = reference,
	targets = { Mock.photo(2, "target.jpg", {}) },
	preferences = {
		engineMode = "executable",
		engineExecutable = "backend/chameleon_cli.py",
		engineScript = "backend/chameleon_cli.py",
		keepArtifacts = false,
		previewSize = 256,
		pythonExecutable = "python3",
	},
}

local EngineClient = require("modules/EngineClient.lua")
local ready = EngineClient.health()
assert(ready == true)
assert(state.lastCommand == "'backend/chameleon_cli.py' 'health' '--json'")

state.preferences.engineMode = "script"
ready = EngineClient.health()
assert(ready == true)
assert(state.lastCommand == "'python3' 'backend/chameleon_cli.py' 'health' '--json'")

local responsePath = os.tmpname()
local runState = Mock.install {
	reference = reference,
	targets = { Mock.photo(2, "target.jpg", {}) },
	preferences = state.preferences,
	execute = function(command)
		assert(command:find("'fit'", 1, true))
		local handle = assert(io.open(responsePath, "wb"))
		handle:write([[{
			"schema_version":1,
			"request_id":"lua-client",
			"status":"ok",
			"results":[],
			"errors":[]
		}]])
		handle:close()
		return 0
	end,
}
package.loaded["modules/EngineClient.lua"] = nil
runState.pluginModules["modules/EngineClient.lua"] = nil
EngineClient = require("modules/EngineClient.lua")
local response = EngineClient.run(os.tmpname(), responsePath)
assert(response.request_id == "lua-client")
assert(runState.lastCommand:find("'--output'", 1, true))
os.remove(responsePath)

local windowsPython = [[C:\Program Files\Python\python.exe]]
local windowsScript = [[C:\Users\Ada Lovelace\Chameleon.lr\backend\chameleon_cli.py]]
local windowsState = Mock.install {
	reference = reference,
	targets = { Mock.photo(2, "target.jpg", {}) },
	windows = true,
	existingPaths = {
		[windowsPython] = true,
		[windowsScript] = true,
	},
	preferences = {
		engineMode = "script",
		engineScript = windowsScript,
		pythonExecutable = windowsPython,
		keepArtifacts = false,
		previewSize = 256,
	},
}
package.loaded["modules/EngineClient.lua"] = nil
windowsState.pluginModules["modules/EngineClient.lua"] = nil
EngineClient = require("modules/EngineClient.lua")
ready = EngineClient.health()
assert(ready == true)
local expectedWindowsCommand = '"C:\\Program Files\\Python\\python.exe" '
	.. '"C:\\Users\\Ada Lovelace\\Chameleon.lr\\backend\\chameleon_cli.py" '
	.. '"health" "--json"'
assert(windowsState.lastCommand == expectedWindowsCommand)
