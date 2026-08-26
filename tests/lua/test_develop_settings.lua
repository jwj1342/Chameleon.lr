local DevelopSettings = dofile("plugin/Chameleon.lrplugin/modules/DevelopSettings.lua")

local settings, message = DevelopSettings.sanitize {
	Exposure2012 = 1.25,
	Contrast2012 = 15,
	ToneCurvePV2012 = { 0, 0, 128, 140, 255, 255 },
	CropAngle = 45,
}

assert(settings, message)
assert(settings.Exposure2012 == 1.25)
assert(settings.Contrast2012 == 15)
assert(#settings.ToneCurvePV2012 == 6)
assert(settings.CropAngle == nil)

local invalid, invalidMessage = DevelopSettings.sanitize { Exposure2012 = 99 }
assert(invalid == nil)
assert(invalidMessage:find("outside", 1, true))

local empty, emptyMessage = DevelopSettings.sanitize { CropAngle = 12 }
assert(empty == nil)
assert(emptyMessage:find("no supported", 1, true))

local wrongType, wrongTypeMessage = DevelopSettings.sanitize { Contrast2012 = "high" }
assert(wrongType == nil)
assert(wrongTypeMessage:find("must be a number", 1, true))

local malformedCurve, curveMessage = DevelopSettings.sanitize { ToneCurvePV2012 = { 0, 0, 255 } }
assert(malformedCurve == nil)
assert(curveMessage:find("complete points", 1, true))
