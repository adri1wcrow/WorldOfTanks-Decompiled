# Python bytecode 2.7 (decompiled from Python 2.7)
# Embedded file name: scripts/client/gui/shared/utils/requesters/IntSettingsRequester.py
import logging
from functools import wraps
import BigWorld
import constants
from adisp import async, process
from debug_utils import LOG_ERROR
from gui.shared.utils import code2str
_logger = logging.getLogger(__name__)

def requireSync(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        instance = args[0]
        if not instance.isSynced():
            LOG_ERROR('Calling %s require for IntSettingsRequester to be synced.' % func.__name__, stack=True)
        return func(*args, **kwargs)

    return wrapper


class IntSettingsRequester(object):
    __SETTINGS = {'VERSION': 0,
     'GAME': 1,
     'GRAPHICS': 2,
     'SOUND': 3,
     'CONTROLS': 4,
     'AIM_ARCADE_1': 43,
     'AIM_ARCADE_2': 44,
     'AIM_ARCADE_3': 45,
     'AIM_SNIPER_1': 46,
     'AIM_SNIPER_2': 47,
     'AIM_SNIPER_3': 48,
     'MARKERS_ENEMY': 49,
     'MARKERS_DEAD': 50,
     'MARKERS_ALLY': 51,
     'GUI_START_BEHAVIOR': 52,
     'FEEDBACK': 53,
     'EULA_VERSION': constants.USER_SERVER_SETTINGS.EULA_VERSION,
     'GAMEPLAY': 55,
     'FORT': 56,
     'USERS_STORAGE_REV': 57,
     'CONTACTS': 58,
     'GAME_EXTENDED': constants.USER_SERVER_SETTINGS.GAME_EXTENDED,
     'FALLOUT': 60,
     'TUTORIAL': 61,
     'AIM_ARCADE_4': 63,
     'AIM_SNIPER_4': 64,
     'MARKS_ON_GUN': constants.USER_SERVER_SETTINGS.HIDE_MARKS_ON_GUN,
     'BATTLE_COMM': constants.USER_SERVER_SETTINGS.BATTLE_COMM,
     'DOG_TAGS': constants.USER_SERVER_SETTINGS.DOG_TAGS,
     'ONCE_ONLY_HINTS': 70,
     'CAROUSEL_FILTER_1': 73,
     'CAROUSEL_FILTER_2': 74,
     'UNIT_FILTER': 77,
     'RANKED_CAROUSEL_FILTER_1': 80,
     'RANKED_CAROUSEL_FILTER_2': 81,
     'FEEDBACK_DAMAGE_INDICATOR': 82,
     'FEEDBACK_DAMAGE_LOG': 83,
     'FEEDBACK_BATTLE_EVENTS': 84,
     'FEEDBACK_BORDER_MAP': 85,
     'UI_STORAGE': 86,
     'EPICBATTLE_CAROUSEL_FILTER_1': 87,
     'EPICBATTLE_CAROUSEL_FILTER_2': 88,
     'LINKEDSET_QUESTS': constants.USER_SERVER_SETTINGS.LINKEDSET_QUESTS,
     'QUESTS_PROGRESS': constants.USER_SERVER_SETTINGS.QUESTS_PROGRESS,
     'SESSION_STATS': constants.USER_SERVER_SETTINGS.SESSION_STATS,
     'BATTLEPASS_CAROUSEL_FILTER_1': 97,
     'BATTLE_PASS_STORAGE': 98,
     'ONCE_ONLY_HINTS_2': 99,
     'ROYALE_CAROUSEL_FILTER_1': 100,
     'ROYALE_CAROUSEL_FILTER_2': 101}

    def __init__(self):
        self.__isSynced = False
        self.__cache = dict()

    def isSynced(self):
        return self.__isSynced

    def clear(self):
        self.__isSynced = False
        self.__cache = dict()

    @async
    @process
    def request(self, callback=None):
        self.__cache = yield self._requestCache()
        callback(self)

    def getCacheValue(self, key, defaultValue=None):
        return self.__cache.get(key, defaultValue)

    @requireSync
    @process
    def setSetting(self, key, value):
        yield self._addIntSettings({self.__SETTINGS[key]: int(value)})

    @requireSync
    @process
    def setSettings(self, settings):
        intSettings = {self.__SETTINGS[k]:int(v) for k, v in settings.iteritems()}
        yield self._addIntSettings(intSettings)

    @requireSync
    def getSetting(self, key, defaultValue=None):
        return self.getCacheValue(self.__SETTINGS[key], defaultValue)

    @requireSync
    @process
    def delSettings(self, settings):
        yield self._delIntSettings(settings)

    def _response(self, resID, value, callback):
        if resID < 0:
            _logger.error('[class %s] There is error while getting data from cache: %s[%d]', self.__class__.__name__, code2str(resID), resID)
            return callback(dict())
        self.__isSynced = True
        callback(value)

    @async
    def _requestCache(self, callback=None):
        player = BigWorld.player()
        if player is not None and player.intUserSettings is not None:
            self.__isSynced = False
            player.intUserSettings.getCache(lambda resID, value: self._response(resID, value, callback))
        else:
            _logger.warning('Player or intUserSettings is not defined: %r, %r', player, player.intUserSettings if player is not None else None)
        return

    @async
    def _addIntSettings(self, settings, callback=None):
        import BattleReplay
        if not BattleReplay.g_replayCtrl.isPlaying:
            player = BigWorld.player()
            if player is not None:
                self.__cache.update(settings)
                player.intUserSettings.addIntSettings(settings, callback)
            else:
                _logger.warning('Player is not defined, int setting can not be added: %r', settings)
        return

    @async
    def _delIntSettings(self, settings, callback=None):
        import BattleReplay
        if not BattleReplay.g_replayCtrl.isPlaying:
            player = BigWorld.player()
            if player is not None:
                player.intUserSettings.delIntSettings(settings, callback)
            else:
                _logger.warning('Player is not defined, int setting can not be removed: %r', settings)
        return
