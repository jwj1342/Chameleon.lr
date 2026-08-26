local LrApplication = import "LrApplication"
local LrBinding = import "LrBinding"
local LrDialogs = import "LrDialogs"
local LrFileUtils = import "LrFileUtils"
local LrFunctionContext = import "LrFunctionContext"
local LrPathUtils = import "LrPathUtils"
local LrView = import "LrView"

local Config = require "modules/Config.lua"
local DevelopSettings = require "modules/DevelopSettings.lua"
local EngineClient = require "modules/EngineClient.lua"
local Json = require "modules/Json.lua"
local PhotoService = require "modules/PhotoService.lua"
local logger = require "modules/Logger.lua"

local Workflow = {}

local function writeText(path, contents)
	local handle, message = io.open(path, "wb")
	if not handle then
		error("Cannot write request: " .. tostring(message))
	end
	local ok, writeMessage = handle:write(contents)
	handle:close()
	if not ok then
		error("Cannot write request: " .. tostring(writeMessage))
	end
end

local function selectedPhotos()
	local catalog = LrApplication.activeCatalog()
	local reference = catalog:getTargetPhoto()
	if not reference then
		error("Select an edited reference photo and at least one target photo")
	end

	local targets = {}
	for _, photo in ipairs(catalog:getTargetPhotos()) do
		if photo.localIdentifier ~= reference.localIdentifier then
			targets[#targets + 1] = photo
		end
	end
	if #targets == 0 then
		error("The active photo is the reference. Select at least one additional target photo")
	end
	return catalog, reference, targets
end

local function confirm(reference, targetCount)
	return LrFunctionContext.callWithContext("Chameleon options", function(context)
		local factory = LrView.osFactory()
		local properties = LrBinding.makePropertyTable(context)
		properties.strength = 1.0
		properties.adaptExposure = true
		properties.adaptWhiteBalance = true

		local contents = factory:column {
			bind_to_object = properties,
			spacing = factory:control_spacing(),
			factory:static_text {
				title = "Reference: " .. tostring(reference:getFormattedMetadata("fileName")),
				fill_horizontal = 1,
			},
			factory:static_text {
				title = "Targets: " .. tostring(targetCount),
			},
			factory:row {
				factory:static_text { title = "Strength" },
				factory:slider {
					value = LrView.bind("strength"),
					min = 0,
					max = 1,
					width = 240,
				},
				factory:edit_field {
					value = LrView.bind("strength"),
					min = 0,
					max = 1,
					precision = 2,
					width_in_digits = 4,
				},
			},
			factory:checkbox {
				title = "Adapt exposure to each target",
				value = LrView.bind("adaptExposure"),
			},
			factory:checkbox {
				title = "Adapt white balance to each target",
				value = LrView.bind("adaptWhiteBalance"),
			},
		}

		local result = LrDialogs.presentModalDialog {
			title = "Chameleon.lr",
			contents = contents,
			actionVerb = "Apply",
		}
		if result ~= "ok" then
			return nil
		end
		return {
			strength = properties.strength,
			adapt_exposure = properties.adaptExposure,
			adapt_white_balance = properties.adaptWhiteBalance,
		}
	end)
end

local function newWorkspace()
	local base = LrPathUtils.child(
		LrPathUtils.getStandardFilePath("temp"),
		"chameleon-" .. tostring(os.time()) .. "-" .. tostring(math.random(100000, 999999))
	)
	local path = LrFileUtils.chooseUniqueFileName(base)
	local created, message = LrFileUtils.createAllDirectories(path)
	if not created then
		error("Cannot create temporary workspace: " .. tostring(message))
	end
	return path, LrPathUtils.leafName(path)
end

local function captureRequest(reference, targets, options, workspace, requestId, progress)
	progress:setCaption("Rendering reference preview")
	local referenceInput = PhotoService.capture(
		reference,
		LrPathUtils.child(workspace, "reference.jpg"),
		Config.preferences().previewSize,
		progress
	)

	local targetInputs = {}
	for index, photo in ipairs(targets) do
		progress:setCaption("Rendering target " .. tostring(index) .. " of " .. tostring(#targets))
		progress:setPortionComplete(index - 1, #targets + 2)
		targetInputs[index] = PhotoService.capture(
			photo,
			LrPathUtils.child(workspace, "target-" .. tostring(photo.localIdentifier) .. ".jpg"),
			Config.preferences().previewSize,
			progress
		)
	end

	return {
		schema_version = 1,
		request_id = requestId,
		reference = referenceInput,
		targets = targetInputs,
		options = options,
	}
end

local function validatedResults(response, requestId, photosById)
	if type(response) ~= "table" or response.schema_version ~= 1 then
		error("Engine response uses an unsupported schema version")
	end
	if response.request_id ~= requestId then
		error("Engine response request_id does not match")
	end
	if type(response.results) ~= "table" then
		error("Engine response has no results array")
	end
	if type(response.errors) ~= "table" then
		error("Engine response has no errors array")
	end
	if response.status == "ok" and #response.errors > 0 then
		error("Engine response status conflicts with its errors")
	end

	local results = {}
	local handledIds = {}
	for _, item in ipairs(response.results) do
		if type(item) ~= "table" then
			error("Engine returned a malformed result")
		end
		local photoId = tostring(item.photo_id)
		local photo = photosById[photoId]
		if not photo then
			error("Engine returned an unknown photo id: " .. tostring(item.photo_id))
		end
		if handledIds[photoId] then
			error("Engine returned a duplicate photo id: " .. photoId)
		end
		local settings, message = DevelopSettings.sanitize(item.develop_settings)
		if not settings then
			error("Invalid settings for " .. tostring(item.photo_id) .. ": " .. tostring(message))
		end
		results[#results + 1] = { photo = photo, settings = settings }
		handledIds[photoId] = true
	end

	for _, item in ipairs(response.errors) do
		if type(item) ~= "table" or type(item.message) ~= "string" then
			error("Engine returned a malformed error")
		end
		local photoId = tostring(item.photo_id)
		if not photosById[photoId] then
			error("Engine returned an error for an unknown photo id: " .. photoId)
		end
		if handledIds[photoId] then
			error("Engine returned more than one outcome for photo id: " .. photoId)
		end
		handledIds[photoId] = true
	end

	for photoId, _ in pairs(photosById) do
		if not handledIds[photoId] then
			error("Engine omitted target photo id: " .. photoId)
		end
	end
	if #results == 0 then
		error("Engine did not produce any applicable results")
	end
	return results
end

local function perform(catalog, reference, targets, options, workspace, requestId, progress)
	local request = captureRequest(reference, targets, options, workspace, requestId, progress)
	local requestPath = LrPathUtils.child(workspace, "request.json")
	local responsePath = LrPathUtils.child(workspace, "response.json")
	writeText(requestPath, Json.encode(request))

	progress:setCaption("Computing adaptive settings")
	progress:setPortionComplete(#targets, #targets + 2)
	local response = EngineClient.run(requestPath, responsePath)

	local photosById = {}
	for _, photo in ipairs(targets) do
		photosById[tostring(photo.localIdentifier)] = photo
	end
	local results = validatedResults(response, requestId, photosById)

	progress:setCaption("Applying Lightroom develop settings")
	local gateResult = catalog:withWriteAccessDo("Apply Chameleon adaptive style", function()
		for _, result in ipairs(results) do
			result.photo:applyDevelopSettings(result.settings, "Chameleon adaptive style", true)
		end
	end, { timeout = 15 })
	if gateResult ~= "executed" then
		error("Could not obtain catalog write access: " .. tostring(gateResult))
	end
	progress:setPortionComplete(#targets + 2, #targets + 2)

	local failureCount = type(response.errors) == "table" and #response.errors or 0
	return #results, failureCount
end

function Workflow.run()
	local catalog, reference, targets = selectedPhotos()
	local options = confirm(reference, #targets)
	if not options then
		return
	end

	LrFunctionContext.callWithContext("Chameleon workflow", function(context)
		local progress = LrDialogs.showModalProgressDialog {
			title = "Chameleon.lr",
			caption = "Preparing photos",
			cannotCancel = false,
			functionContext = context,
		}
		local workspace, requestId = newWorkspace()
		local ok, applied, failed = import("LrTasks").pcall(
			perform,
			catalog,
			reference,
			targets,
			options,
			workspace,
			requestId,
			progress
		)
		progress:done()

		if not Config.preferences().keepArtifacts then
			LrFileUtils.delete(workspace)
		end
		if not ok then
			logger:error(tostring(applied))
			error(applied)
		end

		local message = "Applied adaptive settings to " .. tostring(applied) .. " photo(s)."
		if failed > 0 then
			message = message .. " " .. tostring(failed) .. " target(s) failed."
		end
		LrDialogs.message("Chameleon.lr", message, failed > 0 and "warning" or "info")
	end)
end

return Workflow
