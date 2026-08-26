local LrPathUtils = import "LrPathUtils"
local LrPrefs = import "LrPrefs"
local LrFileUtils = import "LrFileUtils"

local Config = {}

local function repositoryRoot()
	return LrPathUtils.parent(LrPathUtils.parent(_PLUGIN.path))
end

function Config.defaults()
	local root = repositoryRoot()
	local executable = WIN_ENV and "python" or "python3"
	local packagedEngineName = WIN_ENV and "chameleon-engine.exe" or "chameleon-engine"
	local packagedEngine = LrPathUtils.child(
		LrPathUtils.child(_PLUGIN.path, "bin"),
		packagedEngineName
	)
	local virtualEnvironmentPython
	if WIN_ENV then
		virtualEnvironmentPython = LrPathUtils.child(
			LrPathUtils.child(LrPathUtils.child(root, ".venv"), "Scripts"),
			"python.exe"
		)
	else
		virtualEnvironmentPython = LrPathUtils.child(
			LrPathUtils.child(LrPathUtils.child(root, ".venv"), "bin"),
			"python"
		)
	end
	if LrFileUtils.exists(virtualEnvironmentPython) then
		executable = virtualEnvironmentPython
	end
	return {
		engineMode = LrFileUtils.exists(packagedEngine) and "executable" or "script",
		engineExecutable = packagedEngine,
		pythonExecutable = executable,
		engineScript = LrPathUtils.child(
			LrPathUtils.child(root, "backend"),
			"chameleon_cli.py"
		),
		previewSize = 1024,
		keepArtifacts = false,
	}
end

function Config.preferences()
	local prefs = LrPrefs.prefsForPlugin()
	local defaults = Config.defaults()
	for key, value in pairs(defaults) do
		if prefs[key] == nil or prefs[key] == "" then
			prefs[key] = value
		end
	end
	return prefs
end

function Config.reset()
	local prefs = LrPrefs.prefsForPlugin()
	for key, value in pairs(Config.defaults()) do
		prefs[key] = value
	end
end

return Config
