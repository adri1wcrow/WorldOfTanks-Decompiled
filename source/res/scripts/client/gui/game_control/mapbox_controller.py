# Python bytecode 2.7 (decompiled from Python 2.7)
# Embedded file name: scripts/client/gui/game_control/mapbox_controller.py
from collections import namedtuple
from functools import partial
import logging
import typing
from account_helpers.AccountSettings import AccountSettings, MAPBOX_PROGRESSION
from async import async, await, await_callback
import adisp
import BigWorld
from BWUtil import AsyncReturn
from constants import QUEUE_TYPE, PREBATTLE_TYPE, Configs
import Event
from gui import SystemMessages
from gui.prb_control import prb_getters
from gui.impl import backport
from gui.impl.gen import R
from gui.mapbox.mapbox_helpers import formatMapboxBonuses
from gui.prb_control.entities.base.ctx import PrbAction
from gui.prb_control.entities.listener import IGlobalListener
from gui.prb_control.settings import PREBATTLE_ACTION_NAME, SELECTOR_BATTLE_TYPES
from gui.Scaleform.daapi.settings.views import VIEW_ALIAS
from gui.Scaleform.daapi.view.lobby.store.browser.shop_helpers import getClientControlledCloseCtx
from gui.Scaleform.genConsts.QUESTS_ALIASES import QUESTS_ALIASES
from gui.server_events import caches
from gui.shared.event_dispatcher import showMapboxIntro, showBrowserOverlayView
from gui.shared.utils import SelectorBattleTypesUtils
from gui.shared.utils.SelectorBattleTypesUtils import setBattleTypeAsUnknown
from gui.shared.utils.scheduled_notifications import Notifiable, SimpleNotifier
from gui.wgcg.mapbox.contexts import MapboxProgressionCtx, MapboxRequestCrewbookCtx, MapboxCompleteSurveyCtx, MapboxRequestAuthorizedURLCtx
from helpers import dependency, server_settings, time_utils
from season_provider import SeasonProvider
from skeletons.gui.game_control import IMapboxController
from skeletons.gui.lobby_context import ILobbyContext
from skeletons.gui.web import IWebController
from skeletons.gui.server_events import IEventsCache
from skeletons.gui.system_messages import ISystemMessages
_logger = logging.getLogger(__name__)
ProgressionData = namedtuple('ProgressionData', ('surveys',
 'rewards',
 'minRank',
 'totalBattles'))
MapData = namedtuple('MapData', ('progress',
 'total',
 'passed',
 'available',
 'url'))
RewardData = namedtuple('RewardData', ('bonusList', 'status'))

class MapboxController(Notifiable, SeasonProvider, IMapboxController, IGlobalListener):
    __lobbyContext = dependency.descriptor(ILobbyContext)
    __systemMessages = dependency.descriptor(ISystemMessages)
    __webCtrl = dependency.descriptor(IWebController)

    def __init__(self):
        super(MapboxController, self).__init__()
        self.onPrimeTimeStatusUpdated = Event.Event()
        self.onUpdated = Event.Event()
        self.onMapboxSurveyShown = Event.Event()
        self.__callbackID = None
        self.__progressionDataProvider = MapboxProgressionDataProvider()
        self.__settingsManager = MapboxSettingsManager()
        self.__isSyncing = False
        return

    def addProgressionListener(self, listener):
        self.__progressionDataProvider.onProgressionDataUpdated += listener

    def removeProgressionListener(self, listener):
        self.__progressionDataProvider.onProgressionDataUpdated -= listener

    def init(self):
        super(MapboxController, self).init()
        self.addNotificator(SimpleNotifier(self.getTimer, self.__timerUpdate))
        self.__progressionDataProvider.init()

    def fini(self):
        self.__progressionDataProvider.fini()
        self.__progressionDataProvider = None
        self.__settingsManager.stop()
        self.__settingsManager = None
        self.clearNotification()
        self.onPrimeTimeStatusUpdated.clear()
        self.onUpdated.clear()
        self.onMapboxSurveyShown.clear()
        self.__lobbyContext.getServerSettings().onServerSettingsChange -= self.__onServerSettingsChanged
        if self.__callbackID is not None:
            BigWorld.cancelCallback(self.__callbackID)
            self.__callbackID = None
        super(MapboxController, self).fini()
        return

    def onLobbyStarted(self, ctx):
        super(MapboxController, self).onLobbyStarted(ctx)
        self.__settingsManager.start()
        self.storeCycle()

    def onLobbyInited(self, event):
        super(MapboxController, self).onLobbyInited(event)
        self.__lobbyContext.getServerSettings().onServerSettingsChange += self.__onServerSettingsChanged
        unitMgr = prb_getters.getClientUnitMgr()
        if unitMgr is not None:
            unitMgr.onUnitJoined += self.__onUnitJoined
        if self.isActive():
            self.__progressionDataProvider.start()
        self.startNotification()
        self.startGlobalListening()
        return

    def onAccountBecomeNonPlayer(self):
        super(MapboxController, self).onAccountBecomeNonPlayer()
        self.stopGlobalListening()
        self.stopNotification()
        unitMgr = prb_getters.getClientUnitMgr()
        if unitMgr is not None:
            unitMgr.onUnitJoined -= self.__onUnitJoined
        self.__lobbyContext.getServerSettings().onServerSettingsChange -= self.__onServerSettingsChanged
        if self.__progressionDataProvider is not None:
            self.__progressionDataProvider.stop()
        if self.__settingsManager is not None:
            self.__settingsManager.stop()
        return

    def isEnabled(self):
        return self.getModeSettings().isEnabled

    def getModeSettings(self):
        return dependency.instance(ILobbyContext).getServerSettings().mapbox

    def isActive(self):
        return self.isEnabled() and self.getCurrentSeason() is not None and self.getCurrentCycleInfo()[1]

    def isMapboxMode(self):
        dispatcher = self.prbDispatcher
        if dispatcher is not None:
            state = dispatcher.getFunctionalState()
            return state.isInPreQueue(queueType=QUEUE_TYPE.MAPBOX) or state.isInUnit(PREBATTLE_TYPE.MAPBOX)
        else:
            return False

    @adisp.process
    def selectMapboxBattle(self):
        dispatcher = self.prbDispatcher
        if dispatcher is None:
            _logger.error('Prebattle dispatcher is not defined')
            return
        else:
            yield dispatcher.doSelectAction(PrbAction(PREBATTLE_ACTION_NAME.MAPBOX))
            return

    def getProgressionData(self):
        return self.__progressionDataProvider.getProgressionData()

    @adisp.process
    def selectCrewbookNation(self, itemID):
        if self.__webCtrl.isAvailable():
            result = yield self.__webCtrl.sendRequest(MapboxRequestCrewbookCtx(itemID))
            if not result.isSuccess():
                SystemMessages.pushMessage(backport.text(R.strings.messenger.serviceChannelMessages.mapbox.crewbookRequestError()), SystemMessages.SM_TYPE.ErrorSimple)

    @adisp.process
    def handleSurveyCompleted(self, mapName):

        @adisp.async
        @async
        def proxy(callback):
            result = yield await(self.forceUpdateProgressData())
            callback(result)

        if self.__webCtrl.isAvailable():
            yield self.__webCtrl.sendRequest(MapboxCompleteSurveyCtx(mapName))
            yield proxy()
        else:
            _logger.error('Survey completed request not sent due to WGCG unavailability')

    def getUnseenItemsCount(self):
        progressionData = self.__progressionDataProvider.getProgressionData()
        if not self.isEnabled() or self.getCurrentCycleID() is None or progressionData is None:
            return 0
        else:
            return len([ mapName for mapName, mapData in progressionData.surveys.iteritems() if not self.__settingsManager.isMapVisited(mapName) and mapData.available and mapData.progress >= mapData.total ]) + len([ rewardItem for battles, reward in progressionData.rewards.iteritems() if battles <= progressionData.totalBattles for rewardItem in reward.bonusList if rewardItem.getName() == 'selectableCrewbook' ])

    @adisp.process
    def showSurvey(self, mapName):
        progressionData = self.getProgressionData()
        if progressionData is None:
            return
        else:
            if mapName in progressionData.surveys and not self.__isSyncing:
                self.__isSyncing = True
                result = yield self.__webCtrl.sendRequest(MapboxRequestAuthorizedURLCtx(progressionData.surveys[mapName].url))
                self.__isSyncing = False
                if result.isSuccess():
                    data = MapboxProgressionCtx.getDataObj(result.data)
                    if data is not None:
                        showBrowserOverlayView(data['url'], alias=VIEW_ALIAS.BROWSER_OVERLAY, **getClientControlledCloseCtx())
                        self.onMapboxSurveyShown(mapName)
                        self.addVisitedMap(mapName)
            return

    def addVisitedMap(self, mapName):
        self.__settingsManager.addVisitedMap(mapName)

    def storeReward(self, numBattles, rewardIdx, rewardIconName):
        self.__settingsManager.storeReward(numBattles, rewardIdx, rewardIconName)

    def getStoredReward(self, numBattles, rewardIdx):
        return self.__settingsManager.getStoredReward(numBattles, rewardIdx)

    def setPrevBattlesPlayed(self, numBattles):
        self.__settingsManager.setPrevBattlesPlayed(numBattles)

    def getPrevBattlesPlayed(self):
        return self.__settingsManager.getPrevBattlesPlayed()

    def isMapVisited(self, mapName):
        return self.__settingsManager.isMapVisited(mapName)

    def storeCycle(self):
        self.__settingsManager.storeCycle(self.isActive(), self.getCurrentCycleID())

    @async
    def forceUpdateProgressData(self):
        result = yield await(self.__progressionDataProvider.forceUpdateProgressData())
        raise AsyncReturn(result)

    def onPrbEntitySwitched(self):
        self.__modeEntered()

    def getEventEndTimestamp(self):
        if self.hasPrimeTimesLeftForCurrentCycle() or self.isInPrimeTime():
            currServerTime = time_utils.getCurrentLocalServerTimestamp()
            actualSeason = self.getCurrentSeason() or self.getNextSeason()
            actualCycle = actualSeason.getCycleInfo() or actualSeason.getNextCycleInfo(currServerTime)
            lastPrimeTimeEnd = max([ period[1] for primeTime in self.getPrimeTimes().values() for period in primeTime.getPeriodsBetween(int(currServerTime), actualCycle.endDate, True) ])
            return lastPrimeTimeEnd
        else:
            return None

    def __onUnitJoined(self, *args):
        self.__modeEntered()

    def __modeEntered(self):
        if self.isMapboxMode() and not SelectorBattleTypesUtils.isKnownBattleType(SELECTOR_BATTLE_TYPES.MAPBOX):
            SelectorBattleTypesUtils.setBattleTypeAsKnown(SELECTOR_BATTLE_TYPES.MAPBOX)
            showMapboxIntro()

    def __selectRandomBattle(self):
        dispatcher = self.prbDispatcher
        if dispatcher is None:
            _logger.error('Prebattle dispatcher is not defined')
            return
        else:
            self.__callbackID = BigWorld.callback(0, partial(self.__doSelectRandomPrb, dispatcher))
            return

    @adisp.process
    def __doSelectRandomPrb(self, dispatcher):
        self.__callbackID = None
        yield dispatcher.doSelectAction(PrbAction(PREBATTLE_ACTION_NAME.RANDOM))
        return

    def __timerUpdate(self):
        status, _, _ = self.getPrimeTimeStatus()
        isMapboxTabLast = caches.getNavInfo().getMissionsTab() == QUESTS_ALIASES.MAPBOX_VIEW_PY_ALIAS
        isMarathonsTabLast = caches.getNavInfo().getMissionsTab() == QUESTS_ALIASES.MISSIONS_GROUPED_VIEW_PY_ALIAS
        if not self.isActive() and isMapboxTabLast or self.isActive() and isMarathonsTabLast:
            caches.getNavInfo().setMissionsTab(None)
        self.onPrimeTimeStatusUpdated(status)
        if self.getCurrentSeason() is None:
            self.__settingsManager.clearSettings()
        self.__eventAvailabilityUpdate()
        return

    def __eventAvailabilityUpdate(self):
        if self.isActive():
            self.__progressionDataProvider.start()
        else:
            self.__progressionDataProvider.stop()
            if self.isMapboxMode():
                self.__selectRandomBattle()
        if not self.isActive() and self.isMapboxMode():
            self.__selectRandomBattle()

    @server_settings.serverSettingsChangeListener(Configs.MAPBOX_CONFIG.value)
    def __onServerSettingsChanged(self, diff):
        self.startNotification()
        self.onUpdated()
        self.__timerUpdate()
        self.storeCycle()


class MapboxProgressionDataProvider(Notifiable):
    __webCtrl = dependency.descriptor(IWebController)
    __lobbyContext = dependency.descriptor(ILobbyContext)
    __mapboxCtrl = dependency.descriptor(IMapboxController)
    __eventsCache = dependency.descriptor(IEventsCache)
    __slots__ = ('onProgressionDataUpdated', '__progressionData', '__isSyncing', '__isShuttingDown', '__isStarted')

    def __init__(self):
        super(MapboxProgressionDataProvider, self).__init__()
        self.__progressionData = None
        self.__isSyncing = False
        self.__isShuttingDown = False
        self.__isStarted = False
        self.onProgressionDataUpdated = Event.Event()
        return

    def init(self):
        self.__progressionData = {}
        self.addNotificator(SimpleNotifier(self.getTimer, self.__timerUpdate))

    def fini(self):
        if self.__isSyncing:
            self.__isShuttingDown = True
            return
        else:
            if self.__isStarted:
                self.stop()
            self.onProgressionDataUpdated.clear()
            self.onProgressionDataUpdated = None
            self.__progressionData = None
            self.clearNotification()
            return

    def start(self):
        if self.__isStarted:
            return
        self.__lobbyContext.getServerSettings().onServerSettingsChange += self.__onServerSettingsChanged
        self.startNotification()
        self.__request(lambda *args: True)
        self.__isStarted = True

    def stop(self):
        self.__lobbyContext.getServerSettings().onServerSettingsChange -= self.__onServerSettingsChanged
        self.stopNotification()
        self.__progressionData.clear()
        self.__isStarted = False

    def getProgressionData(self):
        return None if not self.__progressionData else ProgressionData({key:MapData(value['progress'], value['total'], value['passed'], value['available'], value['url']) for key, value in self.__progressionData.get('surveys', {}).iteritems()}, {value['battles']:RewardData(formatMapboxBonuses(value['reward']), value['status']) for value in self.__progressionData.get('rewards', [])}, self.__progressionData.get('min_rank'), self.__progressionData.get('total_battles_amount'))

    def getTimer(self):
        return self.__mapboxCtrl.getModeSettings().progressionUpdateInterval

    @async
    def forceUpdateProgressData(self):
        result = yield await_callback(self.__request)()
        raise AsyncReturn(result)

    @server_settings.serverSettingsChangeListener(Configs.MAPBOX_CONFIG.value)
    def __onServerSettingsChanged(self, diff):
        if 'progressionUpdateInterval' in diff[Configs.MAPBOX_CONFIG.value]:
            self.startNotification()

    def __timerUpdate(self):
        if self.onProgressionDataUpdated:
            self.__request(lambda *args: True)

    def __onSyncCompleted(self):
        if self.__isShuttingDown:
            self.fini()

    @adisp.process
    def __request(self, callback):
        data = None
        result = None
        if self.__webCtrl.isAvailable() and not self.__isSyncing:
            self.__isSyncing = True
            result = yield self.__webCtrl.sendRequest(MapboxProgressionCtx())
            self.__isSyncing = False
            if result.isSuccess():
                data = MapboxProgressionCtx.getDataObj(result.data)
            self.__onSyncCompleted()
        elif self.__isSyncing:
            callback(False)
            return
        if data != self.__progressionData:
            self.__progressionData = data if data is not None else {}
            self.onProgressionDataUpdated()
            self.__eventsCache.onEventsVisited()
        if result is not None:
            callback(result.isSuccess())
        else:
            callback(False)
        return


class MapboxSettingsManager(object):
    __slots__ = ('__settings',)

    def __init__(self):
        self.__settings = None
        return

    def start(self):
        self.__settings = AccountSettings.getSettings(MAPBOX_PROGRESSION)

    def stop(self):
        if self.__settings is not None:
            AccountSettings.setSettings(MAPBOX_PROGRESSION, self.__settings)
            self.__settings = None
        return

    def clearSettings(self):
        self.__settings['visited_maps'] *= 0
        self.__settings['stored_rewards'].clear()
        self.__settings['previous_battles_played'] = 0

    def isMapVisited(self, mapName):
        return mapName in self.__settings['visited_maps']

    def addVisitedMap(self, mapName):
        if mapName not in self.__settings['visited_maps']:
            self.__settings['visited_maps'].append(mapName)

    def storeReward(self, numBattles, rewardIdx, rewardIconName):
        self.__settings['stored_rewards'].setdefault(numBattles, {})
        self.__settings['stored_rewards'][numBattles].update({rewardIdx: rewardIconName})

    def getStoredReward(self, numBattles, rewardIdx):
        return self.__settings['stored_rewards'].get(numBattles, {}).pop(rewardIdx, '')

    def setPrevBattlesPlayed(self, numBattles):
        self.__settings['previous_battles_played'] = numBattles

    def getPrevBattlesPlayed(self):
        return self.__settings.get('previous_battles_played', 0)

    def storeCycle(self, isActive, cycleId):
        if not isActive or cycleId is None:
            self.__settings['lastCycleId'] = None
        elif self.__settings['lastCycleId'] != cycleId:
            self.__settings['lastCycleId'] = cycleId
            setBattleTypeAsUnknown(SELECTOR_BATTLE_TYPES.MAPBOX)
        return
