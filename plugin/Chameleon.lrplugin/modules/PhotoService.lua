local LrTasks = import "LrTasks"

local DevelopSettings = require "modules/DevelopSettings.lua"

local PhotoService = {}

local function writeBinary(path, contents)
	local handle, message = io.open(path, "wb")
	if not handle then
		return nil, message
	end
	local ok, writeMessage = handle:write(contents)
	handle:close()
	if not ok then
		return nil, writeMessage
	end
	return true
end

local function metadataFor(photo)
	return {
		file_name = photo:getFormattedMetadata("fileName"),
		file_format = photo:getRawMetadata("fileFormat"),
		width = photo:getRawMetadata("width"),
		height = photo:getRawMetadata("height"),
		iso = photo:getRawMetadata("isoSpeedRating"),
		shutter_speed = photo:getRawMetadata("shutterSpeed"),
		aperture = photo:getRawMetadata("aperture"),
		exposure_bias = photo:getRawMetadata("exposureBias"),
		capture_time = photo:getRawMetadata("dateTimeOriginalISO8601"),
	}
end

function PhotoService.capture(photo, previewPath, previewSize, progressScope)
	if photo:getRawMetadata("isVideo") then
		error("Video files are not supported: " .. tostring(photo:getFormattedMetadata("fileName")))
	end

	local finished = false
	local callbackError
	local request
	request = photo:requestJpegThumbnail(previewSize, previewSize, function(jpegData, message)
		if jpegData then
			local ok, writeMessage = writeBinary(previewPath, jpegData)
			if not ok then
				callbackError = "Cannot write preview: " .. tostring(writeMessage)
			end
		else
			callbackError = message or "Lightroom could not render the preview"
		end
		finished = true
	end)
	if request == nil then
		error("Lightroom did not create a preview request")
	end

	local startedAt = os.time()
	while not finished do
		if progressScope and progressScope:isCanceled() then
			error("Canceled by user")
		end
		if os.time() - startedAt > 90 then
			error("Timed out while waiting for Lightroom to render a preview")
		end
		LrTasks.sleep(0.05)
	end
	if callbackError then
		error(callbackError)
	end

	return {
		id = tostring(photo.localIdentifier),
		preview_path = previewPath,
		develop_settings = DevelopSettings.forEngine(photo:getDevelopSettings()),
		metadata = metadataFor(photo),
	}
end

return PhotoService
