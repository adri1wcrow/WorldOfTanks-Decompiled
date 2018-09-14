# Embedded file name: scripts/common/ArenaType.py
import ResMgr
from constants import IS_BOT, IS_WEB, ARENA_TYPE_XML_PATH, ARENA_GAMEPLAY_NAMES, ARENA_GAMEPLAY_IDS, TEAMS_IN_ARENA
from items.vehicles import CAMOUFLAGE_KINDS
from debug_utils import *
if IS_CLIENT:
    from helpers import i18n
elif IS_WEB:
    from web_stubs import *
g_cache = {}
g_geometryNamesToIDs = {}
g_gameplayNames = set()
g_gameplaysMask = 0

def getVisibilityMask(gameplayID):
    return 1 << gameplayID


def getGameplaysMask(gameplayNames):
    return sum([ 1 << ARENA_GAMEPLAY_IDS[name] for name in set(gameplayNames) ])


def getGameplayIDsForMask(gameplaysMask):
    return [ gameplayID for gameplayID in xrange(len(ARENA_GAMEPLAY_NAMES)) if bool(gameplaysMask & 1 << gameplayID) ]


def getGameplayName(gameplayID):
    return ARENA_GAMEPLAY_NAMES[gameplayID]


def getGameplayIDForName(gameplayName):
    return ARENA_GAMEPLAY_IDS[gameplayName]


def parseTypeID(typeID):
    return (typeID >> 16, typeID & 65535)


_DEFAULT_XML = ARENA_TYPE_XML_PATH + '_default_.xml'

def init():
    global g_gameplayNames
    global g_cache
    global g_geometryNamesToIDs
    global g_gameplaysMask
    rootSection = ResMgr.openSection(ARENA_TYPE_XML_PATH + '_list_.xml')
    if rootSection is None:
        raise Exception, "Can't open '%s'" % (ARENA_TYPE_XML_PATH + '_list_.xml')
    defaultXml = ResMgr.openSection(_DEFAULT_XML)
    if defaultXml is None:
        raise Exception, "Can't open '%s'" % _DEFAULT_XML
    defaultGameplayTypesXml = defaultXml['gameplayTypes']
    if defaultGameplayTypesXml is None or not defaultGameplayTypesXml:
        raise Exception, "No defaults for 'gameplayTypes'"
    geometriesSet = set()
    for key, value in rootSection.items():
        geometryID = value.readInt('id')
        if geometryID in geometriesSet:
            raise Exception, 'Geometry ID=%d is not unique' % geometryID
        geometriesSet.add(geometryID)
        __buildCache(geometryID, value.readString('name'), defaultXml)

    g_gameplaysMask = getGameplaysMask(g_gameplayNames)
    g_geometryNamesToIDs = dict([ (arenaType.geometryName, arenaType.geometryID) for arenaType in g_cache.itervalues() ])
    return


class ArenaType(object):

    def __init__(self, geometryCfg, gameplayCfg):
        self.__geometryCfg = geometryCfg
        self.__gameplayCfg = gameplayCfg
        self.__gameplayCfg['id'] = gameplayCfg['gameplayID'] << 16 | geometryCfg['geometryID']
        if self.maxPlayersInTeam < self.minPlayersInTeam:
            raise Exception, "'maxPlayersInTeam' value < 'minPlayersInTeam' value"

    def __getattr__(self, name):
        if name in self.__gameplayCfg:
            return self.__gameplayCfg[name]
        return self.__geometryCfg[name]


def __buildCache(geometryID, geometryName, defaultXml):
    sectionName = ARENA_TYPE_XML_PATH + geometryName + '.xml'
    section = ResMgr.openSection(sectionName)
    if section is None:
        raise Exception, "Can't open '%s'" % sectionName
    geometryCfg = __readGeometryCfg(geometryID, geometryName, section, defaultXml)
    for gameplayCfg in __readGameplayCfgs(geometryName, section, defaultXml, geometryCfg):
        arenaType = ArenaType(geometryCfg, gameplayCfg)
        g_cache[arenaType.id] = arenaType
        g_gameplayNames.add(arenaType.gameplayName)

    return


def __readGeometryCfg(geometryID, geometryName, section, defaultXml):
    try:
        cfg = {}
        cfg['geometryID'] = geometryID
        cfg['geometryName'] = geometryName
        cfg['geometry'] = __readString('geometry', section, defaultXml)
        cfg['boundingBox'] = __readBoundingBox(section)
        cfg['weatherPresets'] = __readWeatherPresets(section)
        cfg['vehicleCamouflageKind'] = __readVehicleCamouflageKind(section)
        cfg['explicitRequestOnly'] = __readBool('explicitRequestOnly', section, defaultXml)
        if IS_CLIENT or IS_WEB:
            cfg['name'] = i18n.makeString(__readString('name', section, defaultXml))
        if IS_CLIENT:
            cfg['umbraEnabled'] = __readInt('umbraEnabled', section, defaultXml)
            cfg['defaultReverbPreset'] = __readString('defaultReverbPreset', section, defaultXml).strip()
            cfg['batchingEnabled'] = __readInt('batchingEnabled', section, defaultXml)
            cfg['waterTexScale'] = section.readFloat('water/texScale', 0.5)
            cfg['waterFreqX'] = section.readFloat('water/freqX', 1.0)
            cfg['waterFreqZ'] = section.readFloat('water/freqZ', 1.0)
            cfg['defaultGroundEffect'] = __readDefaultGroundEffect(section, defaultXml)
        cfg.update(__readCommonCfg(section, defaultXml, True, {}))
        cfg.update(__readGameplayPoints(defaultXml))
    except Exception as e:
        LOG_CURRENT_EXCEPTION()
        raise Exception, "Wrong arena type XML '%s' : %s" % (geometryName, str(e))

    return cfg


def __readGameplayCfgs(geometryName, section, defaultXml, geometryCfg):
    try:
        if section['gameplayTypes'] is None:
            gameplayName = 'ctf'
            gameplayID = getGameplayIDForName(gameplayName)
            return [{'gameplayID': gameplayID,
              'gameplayName': gameplayName}]
        if not section['gameplayTypes']:
            raise Exception, "no 'gameplayTypes' section"
        cfgs = []
        defaultGameplayTypesXml = defaultXml['gameplayTypes']
        for name, subsection in section['gameplayTypes'].items():
            defaultSubsection = defaultGameplayTypesXml[name]
            if defaultSubsection is None:
                raise Exception, "no defaults for '%s'" % name
            cfgs.append(__readGameplayCfg(name, subsection, defaultSubsection, geometryCfg))

    except Exception as e:
        LOG_CURRENT_EXCEPTION()
        raise Exception, "Wrong arena type XML '%s' : %s" % (geometryName, e)

    return cfgs


def __readGameplayCfg(gameplayName, section, defaultXml, geometryCfg):
    try:
        cfg = {}
        cfg['gameplayID'] = getGameplayIDForName(gameplayName)
        cfg['gameplayName'] = gameplayName
        if gameplayName == 'nations':
            raise Exception, 'national battles are disabled'
        cfg.update(__readCommonCfg(section, defaultXml, False, geometryCfg))
    except Exception as e:
        LOG_CURRENT_EXCEPTION()
        raise Exception, "wrong gameplay section '%s' : %s" % (gameplayName, e)

    return cfg


def __readCommonCfg(section, defaultXml, raiseIfMissing, geometryCfg):
    cfg = {}
    if raiseIfMissing or __hasKey('minPlayersInTeam', section, defaultXml):
        cfg['minPlayersInTeam'] = __readMinPlayersInTeam(section, defaultXml)
    if raiseIfMissing or __hasKey('maxPlayersInTeam', section, defaultXml):
        cfg['maxPlayersInTeam'] = __readMaxPlayersInTeam(section, defaultXml)
    if raiseIfMissing or __hasKey('maxTeamsInArena', section, defaultXml):
        cfg['maxTeamsInArena'] = __readTeamsCount('maxTeamsInArena', section, defaultXml)
    if raiseIfMissing or __hasKey('minTeamsInArena', section, defaultXml):
        cfg['minTeamsInArena'] = __readTeamsCount('minTeamsInArena', section, defaultXml)
    if raiseIfMissing or __hasKey('maxSquadTeams', section, defaultXml):
        cfg['maxSquadTeams'] = __readSquadTeamsCount('maxSquadTeams', section, defaultXml)
    if raiseIfMissing or __hasKey('minSquadTeams', section, defaultXml):
        cfg['minSquadTeams'] = __readSquadTeamsCount('minSquadTeams', section, defaultXml)
    if raiseIfMissing or __hasKey('runDelay', section, defaultXml):
        cfg['runDelay'] = __readInt('runDelay', section, defaultXml)
    if raiseIfMissing or __hasKey('roundLength', section, defaultXml):
        cfg['roundLength'] = __readInt('roundLength', section, defaultXml)
    if raiseIfMissing or __hasKey('winnerIfTimeout', section, defaultXml):
        cfg['winnerIfTimeout'] = __readInt('winnerIfTimeout', section, defaultXml)
    if raiseIfMissing or __hasKey('winnerIfExtermination', section, defaultXml):
        cfg['winnerIfExtermination'] = __readInt('winnerIfExtermination', section, defaultXml)
    if raiseIfMissing or __hasKey('artilleryPreparationChance', section, defaultXml):
        cfg['artilleryPreparationChance'] = __readFloat('artilleryPreparationChance', section, defaultXml)
    if raiseIfMissing or section.has_key('mapActivities'):
        cfg['mapActivitiesTimeframes'] = __readMapActivitiesTimeframes(section)
    maxTeamsInArena = cfg.get('maxTeamsInArena', geometryCfg.get('maxTeamsInArena', None))
    if not maxTeamsInArena is not None:
        raise AssertionError
        cfg.update(__readWinPoints(section))
        cfg.update(__readGameplayPoints(section))
        cfg['teamBasePositions'] = __readTeamBasePositions(section, maxTeamsInArena)
        cfg['teamSpawnPoints'] = __readTeamSpawnPoints(section, maxTeamsInArena)
        if IS_CLIENT or IS_WEB:
            if raiseIfMissing or __hasKey('description', section, defaultXml):
                cfg['description'] = i18n.makeString(__readString('description', section, defaultXml))
            if raiseIfMissing or __hasKey('minimap', section, defaultXml):
                cfg['minimap'] = __readString('minimap', section, defaultXml)
            if raiseIfMissing or __hasKey('music', section, defaultXml):
                cfg['music'] = __readString('music', section, defaultXml)
            if raiseIfMissing or __hasKey('loadingMusic', section, defaultXml):
                cfg['loadingMusic'] = __readString('loadingMusic', section, defaultXml)
            if raiseIfMissing or __hasKey('ambientSound', section, defaultXml):
                cfg['ambientSound'] = __readString('ambientSound', section, defaultXml)
            if __hasKey('battleVictoryMusic', section, defaultXml):
                cfg['battleVictoryMusic'] = __readString('battleVictoryMusic', section, defaultXml)
            if __hasKey('battleLoseMusic', section, defaultXml):
                cfg['battleLoseMusic'] = __readString('battleLoseMusic', section, defaultXml)
            if __hasKey('battleDrawMusic', section, defaultXml):
                cfg['battleDrawMusic'] = __readString('battleDrawMusic', section, defaultXml)
            if raiseIfMissing or __hasKey('battleCountdownTimerSound', section, defaultXml):
                cfg['battleCountdownTimerSound'] = __readString('battleCountdownTimerSound', section, defaultXml)
            if raiseIfMissing or section.has_key('mapActivities'):
                cfg['mapActivitiesSection'] = section['mapActivities']
            if section.has_key('soundRemapping'):
                cfg['soundRemapping'] = section['soundRemapping']
        cfg['controlPoints'] = (IS_CLIENT or IS_BOT) and __readControlPoints(section)
        cfg['teamLowLevelSpawnPoints'] = __readTeamSpawnPoints(section, maxTeamsInArena, nodeNameTemplate='team%d_low', required=False)
    return cfg


def __hasKey(key, xml, defaultXml):
    return xml.has_key(key) or defaultXml.has_key(key)


def __readString(key, xml, defaultXml, defaultValue = None):
    if xml.has_key(key):
        return xml.readString(key)
    elif defaultXml.has_key(key):
        return defaultXml.readString(key)
    elif defaultValue is not None:
        return defaultValue
    else:
        raise Exception, "missing key '%s'" % key
        return


def __readInt(key, xml, defaultXml, defaultValue = None):
    if xml.has_key(key):
        return xml.readInt(key)
    elif defaultXml.has_key(key):
        return defaultXml.readInt(key)
    elif defaultValue is not None:
        return defaultValue
    else:
        raise Exception, "missing key '%s'" % key
        return


def __readFloat(key, xml, defaultXml, defaultValue = None):
    if xml.has_key(key):
        return xml.readFloat(key)
    elif defaultXml.has_key(key):
        return defaultXml.readFloat(key)
    elif defaultValue is not None:
        return defaultValue
    else:
        raise Exception, "missing key '%s'" % key
        return


def __readBool(key, xml, defaultXml, defaultValue = None):
    if xml.has_key(key):
        return xml.readBool(key)
    elif defaultXml.has_key(key):
        return defaultXml.readBool(key)
    elif defaultValue is not None:
        return defaultValue
    else:
        raise Exception, "missing key '%s'" % key
        return


def __readBoundingBox(section):
    bottomLeft = section.readVector2('boundingBox/bottomLeft')
    upperRight = section.readVector2('boundingBox/upperRight')
    if bottomLeft[0] >= upperRight[0] or bottomLeft[1] >= upperRight[1]:
        raise Exception, "wrong 'boundingBox' values"
    return (bottomLeft, upperRight)


def __readWeatherPresets(section):
    weatherXML = section['weather']
    if weatherXML is None or not weatherXML:
        return [{'rnd_range': (0, 1)}]
    else:
        presets = []
        possibilitySum = 0
        for presetXML in weatherXML.values():
            preset = {}
            for key, valueXML in presetXML.items():
                preset[key] = valueXML.asString

            presets.append(preset)
            possibilitySum += presetXML.readFloat('possibility', 1.0)

        factor = 1 / possibilitySum
        prev_upper_limit = 0
        for preset in presets:
            possibility = float(preset.pop('possibility', 1.0))
            rnd_range = (prev_upper_limit, prev_upper_limit + possibility * factor)
            preset['rnd_range'] = rnd_range
            prev_upper_limit = rnd_range[1]

        return presets


def __readVehicleCamouflageKind(section):
    kindName = section.readString('vehicleCamouflageKind')
    kind = CAMOUFLAGE_KINDS.get(kindName)
    if kind is None:
        raise Exception, "missing or wrong section 'vehicleCamouflageKind'"
    return kind


def __readMinPlayersInTeam(section, defaultXml):
    minPlayersInTeam = __readInt('minPlayersInTeam', section, defaultXml)
    if minPlayersInTeam < 0:
        raise Exception, "wrong 'minPlayersInTeam' value"
    return minPlayersInTeam


def __readMaxPlayersInTeam(section, defaultXml):
    maxPlayersInTeam = __readInt('maxPlayersInTeam', section, defaultXml)
    if maxPlayersInTeam < 0:
        raise Exception, "wrong 'maxPlayersInTeam' value"
    return maxPlayersInTeam


def __readTeamsCount(key, section, defaultXml):
    value = __readInt(key, section, defaultXml)
    if not TEAMS_IN_ARENA.MIN_TEAMS <= value <= TEAMS_IN_ARENA.MAX_TEAMS:
        raise Exception, 'Invalid teams in arena'
    return value


def __readSquadTeamsCount(key, section, defaultXml):
    value = __readInt(key, section, defaultXml, 0)
    if not 0 <= value <= TEAMS_IN_ARENA.MAX_TEAMS:
        raise Exception, 'Invalid squad teams count'
    return value


def __readMapActivitiesTimeframes(section):
    mapActivitiesXML = section['mapActivities']
    if not mapActivitiesXML:
        return []
    timeframes = []
    for activityXML in mapActivitiesXML.values():
        startTimes = activityXML.readVector2('startTime')
        possibility = activityXML.readFloat('possibility', 1.0)
        timeframes.append((startTimes[0], startTimes[1], possibility))

    return timeframes


def __readDefaultGroundEffect(section, defaultXml):
    defaultGroundEff = __readString('defaultGroundEffect', section, defaultXml).strip()
    if defaultGroundEff == '':
        return None
    else:
        if defaultGroundEff.find('|') != -1:
            defaultGroundEff = defaultGroundEff.split('|')
            for i in xrange(0, len(defaultGroundEff)):
                defaultGroundEff[i] = defaultGroundEff[i].strip()

        return defaultGroundEff


def __readControlPoints(section):
    res = []
    for name, value in section.items():
        if name == 'controlPoint':
            res.append(value.readVector2(''))

    if res:
        return res
    else:
        return None


def __readTeamBasePositions(section, maxTeamsInArena):
    section = section['teamBasePositions']
    teamBases = tuple([ {} for _ in xrange(maxTeamsInArena) ])
    if section is None:
        return teamBases
    else:
        for idx, teamBase in enumerate(teamBases):
            teamIdx = idx + 1
            s = section['team%s' % teamIdx]
            if s is None:
                raise Exception, "missing 'teamBasePositions/team%s'" % teamIdx
            for name, value in s.items():
                try:
                    id = int(name[8:])
                except:
                    raise Exception, "wrong subsection 'teamBasePositions/team%s/%s'" % (teamIdx, s.name)

                teamBase[id] = value.readVector2('')

        return teamBases


def __readTeamSpawnPoints(section, maxTeamsInArena, nodeNameTemplate = 'team%d', required = True):
    section = section['teamSpawnPoints']
    allTeamSpawnPoints = tuple([ [] for _ in xrange(maxTeamsInArena) ])
    if section is None:
        return allTeamSpawnPoints
    else:
        for idx, teamSpawnPoint in enumerate(allTeamSpawnPoints):
            teamIdx = idx + 1
            s = section[nodeNameTemplate % teamIdx]
            if s is None:
                if required:
                    raise Exception, "missing 'teamSpawnPoints/%s'" % (nodeNameTemplate % teamIdx)
            else:
                for value in s.values():
                    teamSpawnPoint.append(value.readVector2(''))

        return allTeamSpawnPoints


def __readGameplayPoints(section):
    sps = []
    aps = []
    rps = []
    rsps = []
    for name, value in section.items():
        if name == 'flagSpawnPoint':
            sps.append({'position': value.readVector3('position'),
             'team': value.readInt('team'),
             'winPoints': value.readFloat('winPoints')})
        elif name == 'flagAbsorptionPoint':
            aps.append({'position': value.readVector3('position'),
             'team': value.readInt('team'),
             'guid': value.readString('guid')})
        elif name == 'repairPoint':
            rps.append({'position': value.readVector3('position'),
             'radius': value.readFloat('radius'),
             'cooldown': value.readFloat('cooldown'),
             'repairTime': value.readFloat('repairTime'),
             'repairFlags': value.readInt('repairFlags'),
             'guid': value.readString('guid')})
        elif name == 'resourcePoint':
            rsps.append({'position': value.readVector3('position'),
             'radius': value.readFloat('radius'),
             'startDelay': value.readFloat('startDelay'),
             'cooldown': value.readFloat('cooldown'),
             'damageLockTime': value.readFloat('damageLockTime'),
             'amount': value.readInt('amount'),
             'absorptionSpeed': value.readFloat('absorptionSpeed'),
             'reuseCount': value.readInt('reuseCount'),
             'team': value.readInt('team'),
             'guid': value.readString('guid')})

    cfg = {'flagSpawnPoints': sps,
     'flagAbsorptionPoints': aps,
     'repairPoints': rps,
     'resourcePoints': rsps}
    return cfg


def __readWinPoints(section):
    return {'winPoints': section.readString('winPoints', 'DEFAULT')}
