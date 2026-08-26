local LrDialogs = import "LrDialogs"
local LrTasks = import "LrTasks"

local Workflow = require "modules/Workflow.lua"

LrTasks.startAsyncTask(function()
	local success, message = LrTasks.pcall(Workflow.run)
	if not success then
		LrDialogs.message("Chameleon.lr", tostring(message), "critical")
	end
end, "Chameleon adaptive style")
