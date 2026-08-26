local pluginRoot = "plugin/Chameleon.lrplugin"
local nativeRequire = require
local pluginModules = {}

function require(name)
	if name:match("%.lua$") then
		if pluginModules[name] == nil then
			local value = dofile(pluginRoot .. "/" .. name)
			pluginModules[name] = value == nil and true or value
		end
		return pluginModules[name]
	end
	return nativeRequire(name)
end

function import(name)
	if name == "LrLogger" then
		return function()
			return {
				enable = function() end,
				trace = function() end,
				error = function() end,
			}
		end
	end
	return {}
end

_PLUGIN = { path = pluginRoot }
WIN_ENV = false
MAC_ENV = true

local info = dofile(pluginRoot .. "/Info.lua")
assert(info.LrSdkVersion == 6.0)
assert(info.LrSdkMinimumVersion == 6.0)
assert(info.LrToolkitIdentifier == "io.github.chameleon-lr")
assert(info.LrLibraryMenuItems[1].file == "ApplyAdaptiveStyle.lua")

assert(type(require("modules/Workflow.lua").run) == "function")
assert(type(require("modules/EngineClient.lua").run) == "function")

local provider = dofile(pluginRoot .. "/PluginInfoProvider.lua")
assert(type(provider.sectionsForTopOfDialog) == "function")
