# Python bytecode 2.7 (decompiled from Python 2.7)
# Embedded file name: scripts/client/gui/shop.py
import logging
from collections import namedtuple
import BigWorld
from adisp import async, process
from constants import RentType, GameSeasonType
from gui.Scaleform.daapi.settings.views import VIEW_ALIAS
from gui.Scaleform.daapi.view.lobby.hangar.BrowserView import makeBrowserParams
from gui.Scaleform.daapi.view.lobby.store.browser import shop_helpers as helpers
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from gui.game_control.links import URLMacros
from gui.impl.gen import R
from gui.shared import events, g_eventBus
from gui.shared.economics import getGUIPrice
from gui.shared.event_bus import EVENT_BUS_SCOPE
from gui.shared.gui_items import GUI_ITEM_TYPE
from gui.shared.money import Currency
from helpers import dependency
from skeletons.gui.game_control import ITradeInController
from skeletons.gui.shared import IItemsCache
_logger = logging.getLogger(__name__)
_ProductInfo = namedtuple('_ProductInfo', ('price', 'href', 'method'))
SHOP_RENT_TYPE_MAP = {RentType.NO_RENT: 'none',
 RentType.TIME_RENT: 'time',
 RentType.BATTLES_RENT: 'battles',
 RentType.WINS_RENT: 'wins',
 RentType.SEASON_RENT: 'season',
 RentType.SEASON_CYCLE_RENT: 'cycle'}
SHOP_RENT_SEASON_TYPE_MAP = {GameSeasonType.NONE: 'none',
 GameSeasonType.RANKED: 'ranked',
 GameSeasonType.EPIC: 'frontline'}

class _GoldPurchaseReason(object):
    VEHICLE = 'vehicle'
    RENT = 'rent'
    XP = 'experience'
    SLOT = 'slot'
    BERTH = 'barracks'
    CREW = 'crew'
    EQUIPMENT = 'equipment'
    CUSTOMIZATION = 'customization'
    BUNDLE = 'bundle'
    BATTLE_PASS = 'battle_pass'
    BATTLE_PASS_LEVELS = 'battle_pass_levels'


class Source(object):
    EXTERNAL = 'external'


class Origin(object):
    SHOP = 'shop'
    STORAGE = 'storage'
    HERO_TANK = 'hero_tank'
    VEHICLE_PREVIEW = 'vehicle_preview'
    ADVENT_CALENDAR = 'advent_calendar'
    BATTLE_BOOSTERS = 'battle_boosters'
    CONSUMABLES = 'consumables'
    WITHOUT_NAME = 'without_name'


def _getParams(reason, price, itemId=None):
    params = {'reason': reason,
     'goldPrice': price,
     'source': Source.EXTERNAL}
    if itemId is not None:
        params['itemId'] = itemId
    return params


def _getTradeOffParams(targetVehicleLevel):
    return {'targetVehicleLevel': targetVehicleLevel}


def _makeBuyItemUrl(categoryUrl, itemId=None):
    return '{}/items/$PARAMS(web2client_{})'.format(categoryUrl, itemId) if itemId else categoryUrl


@dependency.replace_none_kwargs(itemsCache=IItemsCache)
def canBuyGoldForItemThroughWeb(itemID, itemsCache=None):
    item = itemsCache.items.getItemByCD(itemID)
    return canBuyGoldForVehicleThroughWeb(item) if item.itemTypeID == GUI_ITEM_TYPE.VEHICLE else False


@dependency.replace_none_kwargs(itemsCache=IItemsCache, tradeIn=ITradeInController)
def canBuyGoldForVehicleThroughWeb(vehicle, itemsCache=None, tradeIn=None):
    if vehicle.isUnlocked:
        money = itemsCache.items.stats.money
        money = tradeIn.addTradeInPriceIfNeeded(vehicle, money)
        exchangeRate = itemsCache.items.shop.exchangeRate
        price = getGUIPrice(vehicle, money, exchangeRate)
        currency = price.getCurrency(byWeight=True)
        mayObtainForMoney = vehicle.mayObtainWithMoneyExchange(money, exchangeRate)
        isBuyingAvailable = not vehicle.isHidden or vehicle.isRentable or vehicle.isRestorePossible()
        if currency == Currency.GOLD:
            if not mayObtainForMoney:
                if isBuyingAvailable:
                    return True
    return False


def showBuyPersonalReservesOverlay(itemId, source=None, origin=None):
    showBuyItemWebView(helpers.getBuyPersonalReservesUrl(), itemId, source, origin)


def showBuyCreditsBattleBoosterOverlay(itemId, source=None, origin=None, alias=VIEW_ALIAS.OVERLAY_WEB_STORE):
    showBuyItemWebView(helpers.getBuyCreditsBattleBoostersUrl(), itemId, source, origin, alias)


def showBuyBonBattleBoosterOverlay(itemId, source=None, origin=None, alias=VIEW_ALIAS.OVERLAY_WEB_STORE):
    showBuyItemWebView(helpers.getBuyBonBattleBoostersUrl(), itemId, source, origin, alias)


@dependency.replace_none_kwargs(itemsCache=IItemsCache)
def showBattleBoosterOverlay(itemId, source=None, origin=None, alias=VIEW_ALIAS.OVERLAY_WEB_STORE, itemsCache=None):
    item = itemsCache.items.getItemByCD(itemId)
    if item.getBuyPrice().price.isCurrencyDefined(Currency.CRYSTAL):
        showBuyMethod = showBuyBonBattleBoosterOverlay
    else:
        showBuyMethod = showBuyCreditsBattleBoosterOverlay
    showBuyMethod(itemId, source, origin, alias)


def showBuyEquipmentOverlay(itemId, source=None, origin=None, alias=VIEW_ALIAS.OVERLAY_WEB_STORE):
    showBuyItemWebView(helpers.getBuyEquipmentUrl(), itemId, source, origin, alias)


@dependency.replace_none_kwargs(itemsCache=IItemsCache)
def showBuyOptionalDeviceOverlay(itemId, source=None, origin=None, alias=VIEW_ALIAS.OVERLAY_WEB_STORE, itemsCache=None):
    item = itemsCache.items.getItemByCD(itemId)
    if item.getBuyPrice().price.isCurrencyDefined(Currency.CRYSTAL):
        showBuyItemWebView(helpers.getBonsDevicesUrl(), itemId, source, origin, alias)
    else:
        showBuyItemWebView(helpers.getBuyOptionalDevicesUrl(), itemId, source, origin, alias)


def showTradeOffOverlay(targetLevel, parent=None):
    _showBlurredWebOverlay(helpers.getTradeOffOverlayUrl(), _getTradeOffParams(targetLevel), parent, isClientCloseControl=True)


def showPersonalTradeOffOverlay(parent=None):
    _showBlurredWebOverlay(helpers.getPersonalTradeOffOverlayUrl(), parent=parent, isClientCloseControl=True)


def showBuyGoldForVehicleWebOverlay(fullPrice, intCD, parent=None):
    showBuyGoldWebOverlay(_getParams(_GoldPurchaseReason.VEHICLE, fullPrice, intCD), parent)


def showBuyGoldForRentWebOverlay(fullPrice, intCD):
    showBuyGoldWebOverlay(_getParams(_GoldPurchaseReason.RENT, fullPrice, intCD))


def showBuyGoldForXpWebOverlay(fullPrice):
    showBuyGoldWebOverlay(_getParams(_GoldPurchaseReason.XP, fullPrice))


def showBuyGoldForSlot(fullPrice):
    showBuyGoldWebOverlay(_getParams(_GoldPurchaseReason.SLOT, fullPrice))


def showBuyGoldForBerth(fullPrice):
    showBuyGoldWebOverlay(_getParams(_GoldPurchaseReason.BERTH, fullPrice))


def showBuyGoldForCrew(fullPrice):
    showBuyGoldWebOverlay(_getParams(_GoldPurchaseReason.CREW, fullPrice))


def showBuyGoldForEquipment(fullPrice):
    showBuyGoldWebOverlay(_getParams(_GoldPurchaseReason.EQUIPMENT, fullPrice))


def showBuyGoldForCustomization(fullPrice):
    showBuyGoldWebOverlay(_getParams(_GoldPurchaseReason.CUSTOMIZATION, fullPrice))


def showBuyGoldForBattlePass(fullPrice):
    showBuyGoldWebOverlay(_getParams(_GoldPurchaseReason.BATTLE_PASS, fullPrice))


def showBuyGoldForBattlePassLevels(fullPrice):
    showBuyGoldWebOverlay(_getParams(_GoldPurchaseReason.BATTLE_PASS_LEVELS, fullPrice))


def showBuyGoldForBundle(fullPrice, params=None):
    params = dict(params) or {}
    params.update(_getParams(_GoldPurchaseReason.BUNDLE, fullPrice))
    showBuyGoldWebOverlay(params)


def showBluprintsExchangeOverlay(url=None, parent=None):
    _url = url or helpers.getBlueprintsExchangeUrl()
    _showBlurredWebOverlay(_url, parent=parent)


@process
def _showBlurredWebOverlay(url, params=None, parent=None, isClientCloseControl=False):
    url = yield URLMacros().parse(url, params)
    ctx = {'url': url,
     'allowRightClick': False}
    if isClientCloseControl:
        ctx.update(helpers.getClientControlledCloseCtx())
    g_eventBus.handleEvent(events.LoadViewEvent(SFViewLoadParams(VIEW_ALIAS.WEB_VIEW_TRANSPARENT, parent=parent), ctx=ctx), EVENT_BUS_SCOPE.LOBBY)


@process
def showBuyItemWebView(url, itemId, source=None, origin=None, alias=VIEW_ALIAS.OVERLAY_WEB_STORE):
    url = yield URLMacros().parse(url)
    params = {}
    if source:
        params['source'] = source
    if origin:
        params['origin'] = origin
    url = yield URLMacros().parse(url=_makeBuyItemUrl(url, itemId), params=params)
    g_eventBus.handleEvent(events.LoadViewEvent(SFViewLoadParams(alias), ctx={'url': url}), EVENT_BUS_SCOPE.LOBBY)


@process
def showBuyGoldWebOverlay(params=None, parent=None):
    url = helpers.getBuyMoreGoldUrl()
    if url:
        url = yield URLMacros().parse(url, params=params)
        g_eventBus.handleEvent(events.LoadViewEvent(SFViewLoadParams(VIEW_ALIAS.OVERLAY_WEB_STORE, parent=parent), ctx={'url': url}), EVENT_BUS_SCOPE.LOBBY)


@process
def showBuyVehicleOverlay(params=None):
    url = helpers.getVehicleUrl()
    if url:
        url = yield URLMacros().parse(url, params=params)
        g_eventBus.handleEvent(events.LoadViewEvent(SFViewLoadParams(VIEW_ALIAS.OVERLAY_WEB_STORE), ctx={'url': url,
         'browserParams': makeBrowserParams(R.strings.waiting.buyItem(), True, True, 0.5)}), EVENT_BUS_SCOPE.LOBBY)


@process
def showRentVehicleOverlay(params=None):
    url = helpers.getVehicleUrl()
    if url:
        url = yield URLMacros().parse(url, params=params)
        g_eventBus.handleEvent(events.LoadViewEvent(SFViewLoadParams(VIEW_ALIAS.OVERLAY_WEB_STORE), ctx={'url': url,
         'browserParams': makeBrowserParams(R.strings.waiting.updating(), True, True, 0.5)}), EVENT_BUS_SCOPE.LOBBY)


@async
def _fetchUrl(url, headers, timeout, method, callback):
    BigWorld.fetchURL(url, callback, headers, timeout, method)
