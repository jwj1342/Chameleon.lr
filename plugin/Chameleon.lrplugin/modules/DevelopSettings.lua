local DevelopSettings = {}

local allowed = {
	ProcessVersion = true,
	WhiteBalance = true,
	Temperature = true,
	Tint = true,
	Exposure2012 = true,
	Contrast2012 = true,
	Highlights2012 = true,
	Shadows2012 = true,
	Whites2012 = true,
	Blacks2012 = true,
	Texture = true,
	Clarity2012 = true,
	Dehaze = true,
	Vibrance = true,
	Saturation = true,
	ToneCurveName2012 = true,
	ToneCurvePV2012 = true,
	ToneCurvePV2012Red = true,
	ToneCurvePV2012Green = true,
	ToneCurvePV2012Blue = true,
	ParametricShadows = true,
	ParametricDarks = true,
	ParametricLights = true,
	ParametricHighlights = true,
	ParametricShadowSplit = true,
	ParametricMidtoneSplit = true,
	ParametricHighlightSplit = true,
	ColorGradeBlending = true,
	ColorGradeGlobalHue = true,
	ColorGradeGlobalLum = true,
	ColorGradeGlobalSat = true,
	ColorGradeHighlightLum = true,
	ColorGradeHighlightHue = true,
	ColorGradeHighlightSat = true,
	ColorGradeMidtoneHue = true,
	ColorGradeMidtoneLum = true,
	ColorGradeMidtoneSat = true,
	ColorGradeShadowLum = true,
	ColorGradeShadowHue = true,
	ColorGradeShadowSat = true,
}

for _, hue in ipairs({ "Red", "Orange", "Yellow", "Green", "Aqua", "Blue", "Purple", "Magenta" }) do
	allowed["HueAdjustment" .. hue] = true
	allowed["SaturationAdjustment" .. hue] = true
	allowed["LuminanceAdjustment" .. hue] = true
end

local ranges = {
	Exposure2012 = { -5, 5 },
	Temperature = { 2000, 50000 },
	Tint = { -150, 150 },
	Contrast2012 = { -100, 100 },
	Highlights2012 = { -100, 100 },
	Shadows2012 = { -100, 100 },
	Whites2012 = { -100, 100 },
	Blacks2012 = { -100, 100 },
	Texture = { -100, 100 },
	Clarity2012 = { -100, 100 },
	Dehaze = { -100, 100 },
	Vibrance = { -100, 100 },
	Saturation = { -100, 100 },
}

local arraySettings = {
	ToneCurvePV2012 = true,
	ToneCurvePV2012Red = true,
	ToneCurvePV2012Green = true,
	ToneCurvePV2012Blue = true,
}

local stringSettings = {
	ProcessVersion = true,
	WhiteBalance = true,
	ToneCurveName2012 = true,
}

local function rangeFor(key)
	if ranges[key] then
		return ranges[key]
	elseif key:match("^Parametric.*Split$") then
		return { 0, 100 }
	elseif key:find("Adjustment", 1, true) or key:match("^Parametric") then
		return { -100, 100 }
	elseif key:match("^ColorGrade.*Hue$") then
		return { 0, 360 }
	elseif key:match("^ColorGrade.*Sat$") or key == "ColorGradeBlending" then
		return { 0, 100 }
	elseif key:match("^ColorGrade.*Lum$") then
		return { -100, 100 }
	end
	return nil
end

local function copyArray(value)
	local result = {}
	local count = 0
	local maximum = 0
	for index, _ in pairs(value) do
		if type(index) ~= "number" or index < 1 or index % 1 ~= 0 then
			return nil, "curve arrays must use consecutive numeric indexes"
		end
		count = count + 1
		maximum = math.max(maximum, index)
		if count > 512 then
			return nil, "curve array is too large"
		end
	end
	if count < 4 or maximum ~= count or count % 2 ~= 0 then
		return nil, "curve arrays must contain at least two complete points"
	end
	for index = 1, count do
		local item = value[index]
		if type(item) ~= "number" or item ~= item or item == math.huge or item == -math.huge then
			return nil, "curve arrays must contain finite numbers"
		end
		if item < 0 or item > 255 then
			return nil, "curve values must be between 0 and 255"
		end
		result[index] = item
	end
	return result
end

function DevelopSettings.sanitize(settings)
	if type(settings) ~= "table" then
		return nil, "develop_settings must be an object"
	end

	local result = {}
	local count = 0
	for key, value in pairs(settings) do
		if allowed[key] then
			local valueType = type(value)
			if arraySettings[key] then
				if valueType ~= "table" then
					return nil, key .. " must be a curve array"
				end
				local copied, message = copyArray(value)
				if not copied then
					return nil, key .. ": " .. message
				end
				result[key] = copied
			elseif stringSettings[key] then
				if valueType ~= "string" then
					return nil, key .. " must be a string"
				end
				result[key] = value
			elseif valueType == "number" then
				if value ~= value or value == math.huge or value == -math.huge then
					return nil, key .. " must be finite"
				end
				local range = rangeFor(key)
				if range and (value < range[1] or value > range[2]) then
					return nil, key .. " is outside Lightroom's supported range"
				end
				result[key] = value
			else
				return nil, key .. " must be a number"
			end
			count = count + 1
		end
	end

	if count == 0 then
		return nil, "no supported develop settings were returned"
	end
	return result
end

function DevelopSettings.forEngine(settings)
	local filtered = {}
	for key, value in pairs(settings or {}) do
		if allowed[key] then
			filtered[key] = value
		end
	end
	return filtered
end

function DevelopSettings.isAllowed(key)
	return allowed[key] == true
end

return DevelopSettings
