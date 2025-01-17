# Python bytecode 2.7 (decompiled from Python 2.7)
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/store/browser/shop_helpers.py
import typing
from gui import GUI_SETTINGS
from gui.Scaleform.daapi.view.lobby.hangar.BrowserView import makeBrowserParams
from helpers import dependency
from helpers.http.url_formatters import addParamsToUrlQuery
from skeletons.gui.lobby_context import ILobbyContext
from skeletons.gui.shared import IItemsCache

@dependency.replace_none_kwargs(lobbyContext=ILobbyContext)
def _getUrl(urlName=None, lobbyContext=None):
    hostUrl = lobbyContext.getServerSettings().shop.hostUrl
    return hostUrl + ('' if urlName is None else GUI_SETTINGS.shop.get(urlName))


@dependency.replace_none_kwargs(itemsCache=IItemsCache)
def isSubscriptionEnabled(itemsCache=None):
    return itemsCache.items.stats.isSubscriptionEnabled


def getShopURL():
    return _getUrl()


def getBuyMoreGoldUrl():
    return _getUrl('buyMoreGoldUrl')


def getBuyGoldUrl():
    return _getUrl('buyGoldUrl')


def getBuyPremiumUrl():
    return _getUrl('buyPremiumUrl')


def getBuyPersonalReservesUrl():
    return _getUrl('buyBoosters')


def getBuyCreditsBattleBoostersUrl():
    return _getUrl('buyCreditsBattleBoosters')


def getBuyBonBattleBoostersUrl():
    return _getUrl('buyBonBattleBoosters')


def getBuyEquipmentUrl():
    return _getUrl('buyEquipment')


def getBuyOptionalDevicesUrl():
    return _getUrl('buyOptionalDevices')


def getBuyVehiclesUrl():
    return _getUrl('buyVehiclesUrl')


def getVehicleUrl():
    return _getUrl('buyVehicle')


def getBonsUrl():
    return _getUrl('bonsUrl')


def getBonsDevicesUrl():
    return _getUrl('bonsDevicesUrl')


def getBonsVehiclesUrl():
    return _getUrl('bonsVehiclesUrl')


def getBonsInstructionsUrl():
    return _getUrl('bonsInstructionsUrl')


def getTradeInVehiclesUrl():
    return _getUrl('tradeIn')


def getPersonalTradeInVehiclesUrl():
    return _getUrl('trade_in_personal')


def getTradeOffOverlayUrl():
    return _getUrl('tradeOffOverlay')


def getPersonalTradeOffOverlayUrl():
    return _getUrl('personalTradeOffOverlay')


def getPremiumVehiclesUrl():
    return _getUrl('premiumVehicles')


def getBuyBattlePassUrl():
    return _getUrl('buyBattlePass')


def getBattlePassCoinProductsUrl():
    return _getUrl('bpcoinProducts')


def getBuyCollectibleVehiclesUrl():
    return _getUrl('buyCollectibleVehicle')


def getBlueprintsExchangeUrl():
    return _getUrl('blueprintsExchange')


def getPlayerSeniorityAwardsUrl():
    return _getUrl('psaProducts')


def getSplitPageUrl(params):
    url = _getUrl('splitUrl')
    return addParamsToUrlQuery(url, params, True)


def getRentVehicleUrl():
    return _getUrl('rentVehicle')


def getTelecomRentVehicleUrl():
    return _getUrl('telecomTankRental')


def getBuyRenewableSubscriptionUrl():
    return _getUrl('buyRenewableSubscription')


def getClientControlledCloseCtx():
    return {'browserParams': makeBrowserParams(isCloseBtnVisible=True),
     'forcedSkipEscape': True}


def getEnvelopesUrl():
    return _getUrl('envelopes')
