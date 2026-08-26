local Mock = {}

local function pathChild(parent, child)
	return parent .. "/" .. child
end

local function makeFactory()
	local factory = {}
	for _, method in ipairs({
		"checkbox",
		"column",
		"edit_field",
		"popup_menu",
		"push_button",
		"row",
		"slider",
		"static_text",
	}) do
		factory[method] = function(_, specification)
			return specification
		end
	end
	function factory:control_spacing()
		return 8
	end
	return factory
end

function Mock.photo(identifier, fileName, developSettings)
	local photo = {
		localIdentifier = identifier,
		appliedSettings = nil,
	}

	function photo:getFormattedMetadata(name)
		if name == "fileName" then
			return fileName
		end
		return nil
	end

	function photo:getRawMetadata(name)
		local values = {
			aperture = 2.8,
			dateTimeOriginalISO8601 = "2026-08-23T12:00:00",
			exposureBias = 0,
			fileFormat = "JPEG",
			height = 3000,
			isVideo = false,
			isoSpeedRating = 100,
			shutterSpeed = 0.01,
			width = 4000,
		}
		return values[name]
	end

	function photo:getDevelopSettings()
		return developSettings or {}
	end

	function photo:applyDevelopSettings(settings, historyName, allowUndo)
		self.appliedSettings = settings
		self.historyName = historyName
		self.allowUndo = allowUndo
	end

	return photo
end

function Mock.install(options)
	options = options or {}
	local pluginRoot = options.pluginRoot or "plugin/Chameleon.lrplugin"
	local state = {
		messages = {},
		preferences = options.preferences or {
			engineMode = "script",
			keepArtifacts = false,
			previewSize = 256,
		},
		workspaces = {},
	}
	local nativeRequire = require
	local pluginModules = options.pluginModules or {}
	local reference = assert(options.reference, "reference photo is required")
	local targets = assert(options.targets, "target photos are required")

	local catalog = {}
	function catalog:getTargetPhoto()
		return reference
	end
	function catalog:getTargetPhotos()
		local photos = { reference }
		for _, photo in ipairs(targets) do
			photos[#photos + 1] = photo
		end
		return photos
	end
	function catalog:withWriteAccessDo(_, callback)
		state.writeAccessCount = (state.writeAccessCount or 0) + 1
		callback()
		return "executed"
	end

	local progress = {}
	function progress:setCaption(caption)
		state.lastCaption = caption
	end
	function progress:setPortionComplete(completed, total)
		state.progress = { completed, total }
	end
	function progress:isCanceled()
		return false
	end
	function progress:done()
		state.progressDone = true
	end

	local sdkModules = {
		LrApplication = { activeCatalog = function() return catalog end },
		LrBinding = { makePropertyTable = function() return {} end },
		LrDialogs = {
			message = function(title, message, level)
				state.messages[#state.messages + 1] = { title = title, message = message, level = level }
			end,
			presentModalDialog = function() return "ok" end,
			showModalProgressDialog = function() return progress end,
		},
		LrFileUtils = {
			chooseUniqueFileName = function(path) return path end,
			createAllDirectories = function(path)
				state.workspaces[#state.workspaces + 1] = path
				local command
				if options.windows then
					command = 'mkdir "' .. path .. '" >NUL 2>NUL'
				else
					command = 'mkdir -p "' .. path .. '"'
				end
				local result = os.execute(command)
				return result == 0, result == 0 and nil or "mkdir failed"
			end,
			delete = function(path)
				os.remove(pathChild(path, "request.json"))
				os.remove(pathChild(path, "response.json"))
				os.remove(path)
				return true
			end,
			exists = function(path)
				if options.existingPaths and options.existingPaths[path] then
					return true
				end
				local handle = io.open(path, "rb")
				if handle then
					handle:close()
					return true
				end
				return false
			end,
			readFile = function(path)
				local handle = assert(io.open(path, "rb"))
				local contents = handle:read("*a")
				handle:close()
				return contents
			end,
		},
		LrFunctionContext = {
			callWithContext = function(_, callback) return callback({}) end,
		},
		LrLogger = function()
			return {
				enable = function() end,
				error = function(_, message) state.lastLogError = message end,
				trace = function() end,
			}
		end,
		LrPathUtils = {
			child = pathChild,
			getStandardFilePath = function()
				return options.tempDirectory
					or os.getenv("TMPDIR")
					or os.getenv("TEMP")
					or os.getenv("TMP")
					or "."
			end,
			leafName = function(path) return path:match("([^/]+)$") end,
			parent = function(path) return path:match("^(.*)/[^/]+$") or "." end,
		},
		LrPrefs = { prefsForPlugin = function() return state.preferences end },
		LrTasks = {
			execute = function(command)
				state.lastCommand = command
				if options.execute then
					return options.execute(command, state)
				end
				return 0
			end,
			pcall = pcall,
			sleep = function() end,
			startAsyncTask = function(callback) callback() end,
		},
		LrView = {
			bind = function(name) return name end,
			osFactory = makeFactory,
		},
	}

	function import(name)
		return assert(sdkModules[name], "unmocked Lightroom SDK module: " .. tostring(name))
	end

	function require(name)
		if name:match("%.lua$") then
			if pluginModules[name] == nil then
				local value = dofile(pathChild(pluginRoot, name))
				pluginModules[name] = value == nil and true or value
			end
			return pluginModules[name]
		end
		return nativeRequire(name)
	end

	_PLUGIN = { path = pluginRoot }
	WIN_ENV = options.windows == true
	MAC_ENV = not WIN_ENV
	state.catalog = catalog
	state.pluginModules = pluginModules
	return state
end

return Mock
