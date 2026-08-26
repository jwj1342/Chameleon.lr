local LrTasks = import "LrTasks"
local LrView = import "LrView"

local Config = require "modules/Config.lua"
local EngineClient = require "modules/EngineClient.lua"

local function testEngine(prefs)
	prefs.engineStatus = "Checking..."
	LrTasks.startAsyncTask(function()
		local ok, ready, message = LrTasks.pcall(EngineClient.health)
		if not ok then
			prefs.engineStatus = "Error: " .. tostring(ready)
		elseif ready then
			prefs.engineStatus = message
		else
			prefs.engineStatus = "Error: " .. tostring(message)
		end
	end, "Test Chameleon engine")
end

local function sectionsForTopOfDialog(factory, _)
	local prefs = Config.preferences()
	prefs.engineStatus = prefs.engineStatus or "Not checked"

	return {
		{
			title = "Chameleon.lr Engine",
			factory:column {
				bind_to_object = prefs,
				spacing = factory:control_spacing(),
				factory:row {
					factory:static_text { title = "Mode", width = 100 },
					factory:popup_menu {
						value = LrView.bind("engineMode"),
						items = {
							{ title = "Standalone executable", value = "executable" },
							{ title = "Python script (development)", value = "script" },
						},
						fill_horizontal = 1,
					},
				},
				factory:row {
					factory:static_text { title = "Executable", width = 100 },
					factory:edit_field {
						value = LrView.bind("engineExecutable"),
						fill_horizontal = 1,
					},
				},
				factory:row {
					factory:static_text { title = "Python", width = 100 },
					factory:edit_field {
						value = LrView.bind("pythonExecutable"),
						fill_horizontal = 1,
					},
				},
				factory:row {
					factory:static_text { title = "Engine script", width = 100 },
					factory:edit_field {
						value = LrView.bind("engineScript"),
						fill_horizontal = 1,
					},
				},
				factory:checkbox {
					title = "Keep temporary request, response, and previews",
					value = LrView.bind("keepArtifacts"),
				},
				factory:row {
					spacing = factory:control_spacing(),
					factory:push_button {
						title = "Test Engine",
						action = function() testEngine(prefs) end,
					},
					factory:push_button {
						title = "Reset Paths",
						action = function()
							Config.reset()
							prefs.engineStatus = "Not checked"
						end,
					},
					factory:static_text {
						title = LrView.bind("engineStatus"),
						fill_horizontal = 1,
					},
				},
			},
		},
	}
end

return {
	sectionsForTopOfDialog = sectionsForTopOfDialog,
}
