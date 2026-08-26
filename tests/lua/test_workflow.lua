local Mock = dofile("tests/lua/LrSDK_Mock.lua")
local Json = dofile("plugin/Chameleon.lrplugin/modules/Json.lua")

local reference = Mock.photo(1, "reference.jpg", { Exposure2012 = 0.5 })
local firstTarget = Mock.photo(2, "target-1.jpg", { Exposure2012 = -1 })
local secondTarget = Mock.photo(3, "target-2.jpg", { Exposure2012 = 1 })

local state = Mock.install {
	reference = reference,
	targets = { firstTarget, secondTarget },
	pluginModules = {
		["modules/PhotoService.lua"] = {
			capture = function(photo, previewPath)
				return {
					id = tostring(photo.localIdentifier),
					preview_path = previewPath,
					develop_settings = photo:getDevelopSettings(),
					metadata = { file_name = photo:getFormattedMetadata("fileName") },
				}
			end,
		},
		["modules/EngineClient.lua"] = {
			run = function(requestPath)
				local handle = assert(io.open(requestPath, "rb"))
				local request = Json.decode(handle:read("*a"))
				handle:close()
				local results = {}
				for _, target in ipairs(request.targets) do
					results[#results + 1] = {
						photo_id = target.id,
						develop_settings = { Exposure2012 = 0.25, Contrast2012 = 12 },
					}
				end
				return {
					schema_version = 1,
					request_id = request.request_id,
					status = "ok",
					results = results,
					errors = {},
				}
			end,
		},
	},
}

require("modules/Workflow.lua").run()

assert(reference.appliedSettings == nil)
assert(firstTarget.appliedSettings.Exposure2012 == 0.25)
assert(firstTarget.appliedSettings.Contrast2012 == 12)
assert(secondTarget.appliedSettings.Exposure2012 == 0.25)
assert(firstTarget.historyName == "Chameleon adaptive style")
assert(firstTarget.allowUndo == true)
assert(state.writeAccessCount == 1)
assert(state.progressDone == true)
assert(#state.messages == 1)
assert(state.messages[1].message == "Applied adaptive settings to 2 photo(s).")
