# Python bytecode 2.7 (decompiled from Python 2.7)
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/vehicle_preview/vehicle_preview.py
import itertools
from copy import deepcopy
import BigWorld
from CurrentVehicle import g_currentPreviewVehicle, g_currentVehicle
from HeroTank import HeroTank
from account_helpers import AccountSettings
from account_helpers.AccountSettings import PREVIEW_INFO_PANEL_IDX
from account_helpers.settings_core.ServerSettingsManager import UI_STORAGE_KEYS
from account_helpers.settings_core.settings_constants import OnceOnlyHints
from gui import makeHtmlString
from gui.ClientUpdateManager import g_clientUpdateManager
from gui.Scaleform.daapi.view.lobby.vehicle_preview.items_kit_helper import getActiveOffer, addBuiltInEquipment
from gui.Scaleform.daapi.settings.views import VIEW_ALIAS
from gui.Scaleform.daapi.view.lobby.LobbySelectableView import LobbySelectableView
from gui.Scaleform.daapi.view.lobby.vehicle_preview.sound_constants import RESEARCH_PREVIEW_SOUND_SPACE
from gui.Scaleform.daapi.view.lobby.vehicle_compare.formatters import resolveStateTooltip
from gui.Scaleform.daapi.view.lobby.vehicle_preview.info.crew_tab import getUniqueMembers
from gui.Scaleform.daapi.view.lobby.vehicle_preview.items_kit_helper import OFFER_CHANGED_EVENT
from gui.Scaleform.daapi.view.meta.VehiclePreviewMeta import VehiclePreviewMeta
from gui.Scaleform.framework import g_entitiesFactories
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from gui.Scaleform.genConsts.PERSONAL_MISSIONS_ALIASES import PERSONAL_MISSIONS_ALIASES
from gui.Scaleform.genConsts.TOOLTIPS_CONSTANTS import TOOLTIPS_CONSTANTS
from gui.Scaleform.genConsts.VEHPREVIEW_CONSTANTS import VEHPREVIEW_CONSTANTS
from gui.Scaleform.locale.RES_ICONS import RES_ICONS
from gui.Scaleform.locale.VEHICLE_PREVIEW import VEHICLE_PREVIEW
from gui.Scaleform.locale.VEH_COMPARE import VEH_COMPARE
from gui.hangar_cameras.hangar_camera_common import CameraRelatedEvents, CameraMovementStates
from gui.impl import backport
from gui.impl.gen import R
from gui.impl.lobby.buy_vehicle_view import BuyVehicleWindow
from gui.shared import event_dispatcher, events, event_bus_handlers, EVENT_BUS_SCOPE, g_eventBus
from gui.shared.event_dispatcher import showShop, showVehPostProgressionView
from gui.shared.formatters import text_styles, getRoleTextWithIcon
from gui.shared.gui_items import GUI_ITEM_TYPE
from gui.shared.money import MONEY_UNDEFINED
from gui.shared.tutorial_helper import getTutorialGlobalStorage
from helpers import dependency
from helpers.i18n import makeString as _ms
from skeletons.account_helpers.settings_core import ISettingsCore
from skeletons.gui.game_control import IHeroTankController, IVehicleComparisonBasket, IMapsTrainingController
from skeletons.gui.shared import IItemsCache
from skeletons.gui.shared.utils import IHangarSpace
from gui.Scaleform.daapi.view.lobby.store.browser.sound_constants import SHOP_PREVIEW_SOUND_SPACE
from gui.Scaleform.daapi.view.lobby.vehicle_preview.sound_constants import VEHICLE_PREVIEW_SOUND_SPACE
from gui.Scaleform.daapi.view.lobby.vehicle_preview.hero_tank_preview_constants import getHeroTankPreviewParams
from web.web_client_api.common import ItemPackTypeGroup, ItemPackEntry, ItemPackType
import SoundGroups
from tutorial.control.context import GLOBAL_FLAG
from gui.prb_control.dispatcher import g_prbLoader
from constants import QUEUE_TYPE
_BACK_BTN_LABELS = {VIEW_ALIAS.LOBBY_HANGAR: 'hangar',
 VIEW_ALIAS.LOBBY_STORE: 'shop',
 VIEW_ALIAS.LOBBY_STORAGE: 'storage',
 VIEW_ALIAS.LOBBY_RESEARCH: 'researchTree',
 VIEW_ALIAS.LOBBY_TECHTREE: 'researchTree',
 VIEW_ALIAS.VEHICLE_COMPARE: 'vehicleCompare',
 VIEW_ALIAS.REFERRAL_PROGRAM_WINDOW: 'referralProgram',
 VIEW_ALIAS.EPIC_BATTLE_PAGE: 'frontline',
 VIEW_ALIAS.RANKED_BATTLE_PAGE: 'ranked',
 VIEW_ALIAS.ADVENT_CALENDAR: 'adventCalendar',
 VIEW_ALIAS.VEH_POST_PROGRESSION: 'vehPostProgression',
 PERSONAL_MISSIONS_ALIASES.PERSONAL_MISSIONS_AWARDS_VIEW_ALIAS: 'personalAwards',
 VIEW_ALIAS.WOT_PLUS_VEHICLE_PREVIEW: None,
 VIEW_ALIAS.SHOP_SALES_MAIN_VIEW: 'event'}
_TABS_DATA = ({'id': VEHPREVIEW_CONSTANTS.BROWSE_LINKAGE,
  'label': VEHICLE_PREVIEW.INFOPANEL_TAB_BROWSE_NAME,
  'linkage': VEHPREVIEW_CONSTANTS.BROWSE_LINKAGE}, {'id': VEHPREVIEW_CONSTANTS.MODULES_LINKAGE,
  'label': VEHICLE_PREVIEW.INFOPANEL_TAB_MODULES_NAME,
  'linkage': VEHPREVIEW_CONSTANTS.MODULES_LINKAGE}, {'id': VEHPREVIEW_CONSTANTS.CREW_LINKAGE,
  'label': VEHICLE_PREVIEW.INFOPANEL_TAB_CREWINFO_NAME,
  'linkage': VEHPREVIEW_CONSTANTS.CREW_LINKAGE})
_SHOW_BACK_BTN = True
_SHOW_CLOSE_BTN = True

def _isCollectibleVehicleWithModules():
    return g_currentPreviewVehicle.isCollectible() and g_currentPreviewVehicle.hasModulesToSelect()


def _updateCollectorHintParameters():
    tutorialStorage = getTutorialGlobalStorage()
    if tutorialStorage is None:
        return
    else:
        isActiveModulesTab = AccountSettings.getSettings(PREVIEW_INFO_PANEL_IDX) == _getModulesTabIdx()
        hintValue = False if isActiveModulesTab else _isCollectibleVehicleWithModules()
        tutorialStorage.setValue(GLOBAL_FLAG.COLLECTIBLE_VEHICLE_PREVIEW_ENABLED, hintValue)
        return


def _updatePostProgressionParameters():
    tutorialStorage = getTutorialGlobalStorage()
    if tutorialStorage is None:
        return
    else:
        isModulesTab = AccountSettings.getSettings(PREVIEW_INFO_PANEL_IDX) == _getModulesTabIdx()
        tutorialStorage.setValue(GLOBAL_FLAG.VEH_POST_PROGRESSION_ENABLED, isModulesTab and g_currentPreviewVehicle.isPostProgressionExists())
        return


def _isModuleBulletVisible():
    return _isCollectorModuleBulletVisible() or _isPostProgressionBulletVisible()


@dependency.replace_none_kwargs(settingsCore=ISettingsCore)
def _isCollectorModuleBulletVisible(settingsCore=None):
    return _isCollectibleVehicleWithModules() and settingsCore.serverSettings.getOnceOnlyHintsSetting(OnceOnlyHints.VEHICLE_PREVIEW_MODULES_BUTTON_HINT)


@dependency.replace_none_kwargs(settingsCore=ISettingsCore)
def _isPostProgressionBulletVisible(settingsCore=None):
    return g_currentPreviewVehicle.isPostProgressionExists() and not settingsCore.serverSettings.getUIStorage().get(UI_STORAGE_KEYS.VEH_PREVIEW_POST_PROGRESSION_BULLET_SHOWN)


def _getModulesTabIdx():
    return [ tab['id'] for tab in _TABS_DATA ].index(VEHPREVIEW_CONSTANTS.MODULES_LINKAGE)


class VehiclePreview(LobbySelectableView, VehiclePreviewMeta):
    __background_alpha__ = 0.0
    __metaclass__ = event_bus_handlers.EventBusListener
    __itemsCache = dependency.descriptor(IItemsCache)
    __comparisonBasket = dependency.descriptor(IVehicleComparisonBasket)
    __heroTanksControl = dependency.descriptor(IHeroTankController)
    __hangarSpace = dependency.descriptor(IHangarSpace)
    __settingsCore = dependency.descriptor(ISettingsCore)
    __mapsTrainingController = dependency.descriptor(IMapsTrainingController)

    def __init__(self, ctx=None):
        self._backAlias = ctx.get('previewAlias', VIEW_ALIAS.LOBBY_HANGAR)
        self._itemsPack = ctx.get('itemsPack')
        if self._backAlias == VIEW_ALIAS.LOBBY_STORE or self._itemsPack is not None:
            self._COMMON_SOUND_SPACE = SHOP_PREVIEW_SOUND_SPACE
        elif self._backAlias in (VIEW_ALIAS.LOBBY_TECHTREE, VIEW_ALIAS.LOBBY_RESEARCH):
            self._COMMON_SOUND_SPACE = RESEARCH_PREVIEW_SOUND_SPACE
        elif self._backAlias in (VIEW_ALIAS.RANKED_BATTLE_PAGE, VIEW_ALIAS.VEH_POST_PROGRESSION):
            self._COMMON_SOUND_SPACE = VEHICLE_PREVIEW_SOUND_SPACE
        super(VehiclePreview, self).__init__(ctx)
        self.__currentOffer = None
        self._vehicleCD = ctx['itemCD']
        self.__vehicleStrCD = ctx.get('vehicleStrCD')
        self._previousBackAlias = ctx.get('previousBackAlias')
        self._previewBackCb = ctx.get('previewBackCb')
        self.__isHeroTank = ctx.get('isHeroTank', False)
        vehParams = ctx.get('vehParams') or {}
        self.__customizationCD = vehParams.get('styleCD')
        self.__offers = ctx.get('offers')
        self._price = ctx.get('price', MONEY_UNDEFINED)
        self._oldPrice = ctx.get('oldPrice', MONEY_UNDEFINED)
        self._title = ctx.get('title')
        self.__description = ctx.get('description')
        self.__endTime = ctx.get('endTime')
        self.__buyParams = ctx.get('buyParams')
        self.__unmodifiedItemsPack = deepcopy(self._itemsPack)
        addBuiltInEquipment(self._itemsPack, self.__itemsCache, self._vehicleCD)
        notInteractive = (VIEW_ALIAS.LOBBY_STORE, VIEW_ALIAS.RANKED_BATTLE_PAGE, VIEW_ALIAS.VEH_POST_PROGRESSION)
        self._heroInteractive = not (self._itemsPack or self.__offers or self._backAlias in notInteractive)
        self.__haveCustomCrew = any((item.type == ItemPackType.CREW_CUSTOM for item in self._itemsPack)) if self._itemsPack else False
        self.__hangarVehicleCD = ctx.get('hangarVehicleCD')
        self.__previewAppearance = ctx.get('previewAppearance')
        if self.__previewAppearance:
            self.__vehAppearanceChanged = True
            g_currentPreviewVehicle.resetAppearance(self.__previewAppearance)
        else:
            self.__vehAppearanceChanged = False
        self.__keepVehicleSelectionEnabled = False
        self._needToResetAppearance = True
        if not self.__isHeroTank:
            self.__hangarSpace.removeVehicle()
        g_currentPreviewVehicle.selectHeroTank(self.__isHeroTank)
        return

    def setBottomPanel(self):
        self.as_setBottomPanelS(VEHPREVIEW_CONSTANTS.BUYING_PANEL_LINKAGE)

    def _populate(self):
        self.addListener(CameraRelatedEvents.VEHICLE_LOADING, self.__onVehicleLoading, EVENT_BUS_SCOPE.DEFAULT)
        self.setBottomPanel()
        if g_currentPreviewVehicle.intCD == self._vehicleCD:
            self.__fullUpdate()
        if self.__hangarVehicleCD and self.__isHeroTank and self.__vehAppearanceChanged:
            g_currentPreviewVehicle.resetAppearance()
            g_currentPreviewVehicle.selectVehicle(self.__hangarVehicleCD, None)
            g_currentPreviewVehicle.resetAppearance(self.__previewAppearance)
        g_currentPreviewVehicle.selectVehicle(self._vehicleCD, self.__vehicleStrCD)
        super(VehiclePreview, self)._populate()
        g_currentPreviewVehicle.onChanged += self.__onVehicleChanged
        g_currentPreviewVehicle.onVehicleInventoryChanged += self.__onInventoryChanged
        self.__comparisonBasket.onChange += self.__onCompareBasketChanged
        self.__comparisonBasket.onSwitchChange += self.__updateHeaderData
        self.__hangarSpace.onSpaceCreate += self.__onHangarCreateOrRefresh
        self.__hangarSpace.setVehicleSelectable(True)
        if not g_currentPreviewVehicle.isPresent():
            event_dispatcher.showHangar()
        if not self._heroInteractive:
            self.__heroTanksControl.setInteractive(False)
        self.addListener(CameraRelatedEvents.CAMERA_ENTITY_UPDATED, self.handleSelectedEntityUpdated)
        specialData = getHeroTankPreviewParams() if self.__isHeroTank else None
        if specialData is not None and specialData.enterEvent:
            SoundGroups.g_instance.playSound2D(specialData.enterEvent)
        g_eventBus.addListener(OFFER_CHANGED_EVENT, self.__onOfferChanged)
        _updateCollectorHintParameters()
        _updatePostProgressionParameters()
        return

    def _dispose(self):
        specialData = getHeroTankPreviewParams() if self.__isHeroTank else None
        if specialData is not None and specialData.exitEvent:
            SoundGroups.g_instance.playSound2D(specialData.exitEvent)
        self.removeListener(CameraRelatedEvents.VEHICLE_LOADING, self.__onVehicleLoading, EVENT_BUS_SCOPE.DEFAULT)
        g_clientUpdateManager.removeObjectCallbacks(self)
        g_currentPreviewVehicle.onChanged -= self.__onVehicleChanged
        g_currentPreviewVehicle.onVehicleInventoryChanged -= self.__onInventoryChanged
        self.__comparisonBasket.onChange -= self.__onCompareBasketChanged
        self.__comparisonBasket.onSwitchChange -= self.__updateHeaderData
        self.__hangarSpace.onSpaceCreate -= self.__onHangarCreateOrRefresh
        self.__hangarSpace.setVehicleSelectable(self.__keepVehicleSelectionEnabled)
        self.removeListener(CameraRelatedEvents.CAMERA_ENTITY_UPDATED, self.handleSelectedEntityUpdated)
        if self.__mapsTrainingController.isMapsTrainingPrbActive:
            self._needToResetAppearance = self._needToResetAppearance and self.__mapsTrainingController.getSelectedVehicle() <= 0
        if self._needToResetAppearance:
            g_currentPreviewVehicle.selectNoVehicle()
            g_currentPreviewVehicle.resetAppearance()
        g_eventBus.handleEvent(events.LobbySimpleEvent(events.LobbySimpleEvent.VEHICLE_PREVIEW_HIDDEN), scope=EVENT_BUS_SCOPE.LOBBY)
        if self._backAlias == VIEW_ALIAS.VEHICLE_PREVIEW:
            g_currentVehicle.refreshModel()
        self._previewBackCb = None
        self.__unmodifiedItemsPack = None
        super(VehiclePreview, self)._dispose()
        if not self._heroInteractive:
            self.__heroTanksControl.setInteractive(True)
        if self.__vehAppearanceChanged:
            g_currentPreviewVehicle.resetAppearance()
        g_eventBus.removeListener(OFFER_CHANGED_EVENT, self.__onOfferChanged)
        return

    def closeView(self):
        event_dispatcher.showHangar()

    def onBackClick(self):
        self._processBackClick()

    def onOpenInfoTab(self, index):
        AccountSettings.setSettings(PREVIEW_INFO_PANEL_IDX, index)
        _updatePostProgressionParameters()
        if index == _getModulesTabIdx():
            self.__resetPostProgressionBullet()

    def onGoToPostProgressionClick(self):
        if self._backAlias == VIEW_ALIAS.VEH_POST_PROGRESSION and callable(self._previewBackCb):
            self._previewBackCb()
        else:
            showVehPostProgressionView(self._vehicleCD, exitEvent=self._getExitEvent())

    def onCompareClick(self):
        self.__comparisonBasket.addVehicle(self._vehicleCD, initParameters={'strCD': g_currentPreviewVehicle.item.descriptor.makeCompactDescr()})

    def handleSelectedEntityUpdated(self, event):
        ctx = event.ctx
        entity = BigWorld.entities.get(ctx['entityId'], None)
        if ctx['state'] == CameraMovementStates.MOVING_TO_OBJECT:
            if isinstance(entity, HeroTank):
                descriptor = entity.typeDescriptor
                if descriptor:
                    self._needToResetAppearance = False
                    event_dispatcher.showHeroTankPreview(descriptor.type.compactDescr, previewAlias=VIEW_ALIAS.VEHICLE_PREVIEW, previousBackAlias=self._backAlias)
            elif entity.id == self.__hangarSpace.space.vehicleEntityId:
                self._processBackClick({'entity': entity})
        return

    def _highlight3DEntityAndShowTT(self, entity):
        itemId = entity.selectionId
        if itemId:
            self.as_show3DSceneTooltipS(TOOLTIPS_CONSTANTS.ENVIRONMENT, [itemId])

    def _fade3DEntityAndHideTT(self, entity):
        self.as_hide3DSceneTooltipS()

    def _createSelectableLogic(self):
        if self.__isHeroTank:
            return super(VehiclePreview, self)._createSelectableLogic()
        from new_year.custom_selectable_logic import WithoutNewYearObjectsSelectableLogic
        return WithoutNewYearObjectsSelectableLogic()

    def _onRegisterFlashComponent(self, viewPy, alias):
        super(VehiclePreview, self)._onRegisterFlashComponent(viewPy, alias)
        if alias == VEHPREVIEW_CONSTANTS.BUYING_PANEL_PY_ALIAS:
            viewPy.setIsHeroTank(self.__isHeroTank)
            viewPy.setBackAlias(self._backAlias)
            viewPy.setBackCallback(self._previewBackCb)
            if self._itemsPack:
                viewPy.setPackItems(self._itemsPack, self._price, self._oldPrice, self._title)
                viewPy.setTimerData(self.__endTime)
                viewPy.setBuyParams(self.__buyParams)
            elif self.__offers:
                viewPy.setOffers(self.__offers, self._title, self.__description)
        elif alias == VEHPREVIEW_CONSTANTS.CREW_LINKAGE:
            if self._itemsPack:
                crewItems = tuple((item for item in self._itemsPack if item.type in ItemPackTypeGroup.CREW))
                vehicleItems = tuple((item for item in self._itemsPack if item.type in ItemPackTypeGroup.VEHICLE))
                if not vehicleItems and crewItems:
                    groupID = crewItems[0].groupID
                    vehicleItems = (ItemPackEntry(id=g_currentPreviewVehicle.item.intCD, groupID=groupID),)
                viewPy.setVehicleCrews(vehicleItems, crewItems)
            elif self.__offers:
                offer = getActiveOffer(self.__offers)
                viewPy.setVehicleCrews((ItemPackEntry(id=g_currentPreviewVehicle.item.intCD, groupID=offer.crew.groupID),), (offer.crew,))
            elif self.__isHeroTank:
                crewData = self.__heroTanksControl.getCurrentTankCrew()
                if crewData and crewData.get('tankmen'):
                    viewPy.setVehicleCrews((ItemPackEntry(id=g_currentPreviewVehicle.item.intCD, groupID=1),), (ItemPackEntry(type=ItemPackType.CREW_CUSTOM, groupID=1, extra=crewData),))
                else:
                    viewPy.setVehicleCrews((ItemPackEntry(id=g_currentPreviewVehicle.item.intCD, groupID=1),), ())
            else:
                viewPy.setVehicleCrews((ItemPackEntry(id=g_currentPreviewVehicle.item.intCD, groupID=1),), ())
        elif alias == VEHPREVIEW_CONSTANTS.BROWSE_LINKAGE:
            viewPy.setHeroTank(self.__isHeroTank)
            if self.__offers:
                offer = self.__currentOffer if self.__currentOffer is not None else getActiveOffer(self.__offers)
                viewPy.setActiveOffer(offer)
        elif alias == VEHPREVIEW_CONSTANTS.WOT_PLUS_PANEL_LINKAGE:
            viewPy.setOffers(self.__offers)
        return

    def _getData(self):
        vehicle = g_currentPreviewVehicle.item
        vehicleLevel = makeHtmlString('html_templates:lobby/vehicle_preview', 'vehicleNameRegular', {'name': backport.text(R.strings.menu.header.level.num(vehicle.level)())})
        vehicleNameStyle = 'vehicleNamePremium' if vehicle.isPremium else 'vehicleNameRegular'
        vehicleName = makeHtmlString('html_templates:lobby/vehicle_preview', vehicleNameStyle, {'name': vehicle.descriptor.type.shortUserString})
        compareBtnEnabled, compareBtnTooltip = resolveStateTooltip(self.__comparisonBasket, vehicle, VEH_COMPARE.STORE_COMPAREVEHICLEBTN_TOOLTIPS_ADDTOCOMPARE, VEH_COMPARE.STORE_COMPAREVEHICLEBTN_TOOLTIPS_DISABLED)
        result = {'closeBtnLabel': VEHICLE_PREVIEW.HEADER_CLOSEBTN_LABEL,
         'backBtnLabel': VEHICLE_PREVIEW.HEADER_BACKBTN_LABEL,
         'backBtnDescrLabel': self._getBackBtnLabel(),
         'showCloseBtn': _SHOW_CLOSE_BTN,
         'showBackButton': _SHOW_BACK_BTN,
         'showPostProgressionBtn': vehicle.isPostProgressionExists,
         'vehicleName': vehicleName,
         'vehicleLevel': vehicleLevel,
         'vehicleType': vehicle.type,
         'isVehicleElite': vehicle.isElite,
         'nationFlagIcon': RES_ICONS.getNationFlag(vehicle.nationName),
         'compareBtnTooltip': compareBtnTooltip,
         'showCompareBtn': compareBtnEnabled,
         'listDesc': self.__getInfoPanelListDescription(vehicle),
         'isMultinational': vehicle.hasNationGroup,
         'roleText': getRoleTextWithIcon(vehicle.role, vehicle.roleLabel),
         'roleId': vehicle.role,
         'vehicleCD': vehicle.intCD}
        return result

    def _getExitEvent(self):
        hangarVehicleCD = None
        hangarVehicle = self.__hangarSpace.getVehicleEntity()
        currentVehicle = g_currentVehicle.item
        if self.__isHeroTank and currentVehicle is not None and hangarVehicle.typeDescriptor.type.compactDescr != currentVehicle.compactDescr:
            hangarVehicleCD = hangarVehicle.typeDescriptor.type.compactDescr
        return events.LoadViewEvent(SFViewLoadParams(self.alias), ctx={'itemCD': self._vehicleCD,
         'previewAlias': self._backAlias,
         'previousBackAlias': self._previousBackAlias,
         'vehicleStrCD': self.__vehicleStrCD,
         'previewBackCb': self._previewBackCb,
         'itemsPack': self.__unmodifiedItemsPack,
         'offers': self.__offers,
         'price': self._price,
         'oldPrice': self._oldPrice,
         'title': self._title,
         'description': self.__description,
         'endTime': self.__endTime,
         'buyParams': self.__buyParams,
         'vehParams': {'styleCD': self.__customizationCD} if self.__customizationCD is not None else {},
         'isHeroTank': self.__isHeroTank,
         'hangarVehicleCD': hangarVehicleCD})

    def __onVehicleLoading(self, ctxEvent):
        if self.__customizationCD is not None and not ctxEvent.ctx.get('started'):
            customizationItem = self.__itemsCache.items.getItemByCD(self.__customizationCD)
            if customizationItem is None:
                return
            if customizationItem.itemTypeID == GUI_ITEM_TYPE.STYLE:
                g_currentPreviewVehicle.previewStyle(customizationItem)
            elif customizationItem.itemTypeID == GUI_ITEM_TYPE.CAMOUFLAGE:
                g_currentPreviewVehicle.previewCamouflage(customizationItem)
        return

    def __fullUpdate(self):
        self.__updateHeaderData()
        self.__updateTabsData()
        self.__updateModuleBullet()

    def __updateTabsData(self):
        selectedTabInd = AccountSettings.getSettings(PREVIEW_INFO_PANEL_IDX)
        if self.__haveCustomCrew or self.__offers:
            tab_ids = [ tab['id'] for tab in _TABS_DATA ]
            if VEHPREVIEW_CONSTANTS.CREW_LINKAGE in tab_ids:
                selectedTabInd = tab_ids.index(VEHPREVIEW_CONSTANTS.CREW_LINKAGE)
        for idx, tab in enumerate(_TABS_DATA):
            tab['selected'] = selectedTabInd == idx

        self.as_setTabsDataS(_TABS_DATA)

    def __onVehicleChanged(self, *args):
        if g_currentPreviewVehicle.isPresent():
            self._vehicleCD = g_currentPreviewVehicle.item.intCD
            self.__updateCrewTabLabel()
            self.__fullUpdate()

    def __updateCrewTabLabel(self):
        crewCount = len(g_currentPreviewVehicle.item.crew)
        crewCount += len(getUniqueMembers(g_currentPreviewVehicle.item))
        for tab in _TABS_DATA:
            if tab['linkage'] == VEHPREVIEW_CONSTANTS.CREW_LINKAGE:
                tab['label'] = _ms(VEHICLE_PREVIEW.INFOPANEL_TAB_CREWINFO_NAME, crewCount=crewCount)

    def __onCompareBasketChanged(self, changedData):
        if changedData.isFullChanged:
            self.__updateHeaderData()

    def __updateHeaderData(self):
        self.as_setDataS(self._getData())

    @staticmethod
    def __getInfoPanelListDescription(vehicle):
        descriptions = (text_styles.main(VEHICLE_PREVIEW.INFOPANEL_TAB_LISTDESC_CREW),
         text_styles.main(VEHICLE_PREVIEW.INFOPANEL_TAB_LISTDESC_CREWSKILLS),
         text_styles.main(VEHICLE_PREVIEW.INFOPANEL_TAB_LISTDESC_CREWEQUIPS),
         text_styles.main(VEHICLE_PREVIEW.INFOPANEL_TAB_LISTDESC_CREWSKILLSEQUIPS))
        hasSkillBonuses = any((tMan.skills for _, tMan in vehicle.crew))
        hasEquipBonuses = any(itertools.chain(vehicle.optDevices.installed, vehicle.battleAbilities.installed, vehicle.battleBoosters.installed, (rCons and rCons.getKpi() for rCons in vehicle.consumables.installed), (vehicle.hasOutfit(vehicle.getAnyOutfitSeason()),)))
        return descriptions[hasEquipBonuses << 1 | hasSkillBonuses]

    def _getBackBtnLabel(self):
        if self._backAlias and self._backAlias in _BACK_BTN_LABELS:
            backBtnLabel = _BACK_BTN_LABELS[self._backAlias]
            if not backBtnLabel:
                return None
            return VEHICLE_PREVIEW.getBackBtnLabel(_BACK_BTN_LABELS[self._backAlias])
        else:
            return VEHICLE_PREVIEW.HEADER_BACKBTN_DESCRLABEL_HANGAR

    def _getPrbEntityType(self):
        prbDispatcher = g_prbLoader.getDispatcher()
        if not prbDispatcher:
            return QUEUE_TYPE.UNKNOWN
        else:
            entity = prbDispatcher.getEntity()
            return entity.getQueueType() if entity is not None else QUEUE_TYPE.UNKNOWN

    def __onHangarCreateOrRefresh(self):
        self.closeView()

    @event_bus_handlers.eventBusHandler(events.HideWindowEvent.HIDE_VEHICLE_PREVIEW, EVENT_BUS_SCOPE.LOBBY)
    def __handleWindowClose(self, event=None):
        if event is not None:
            if event.ctx.get('back', True):
                self.onBackClick()
            elif event.ctx.get('close', False):
                self.closeView()
        self.destroy()
        return

    def _processBackClick(self, ctx=None):
        if self._previewBackCb:
            self._previewBackCb()
        elif self._backAlias == VIEW_ALIAS.LOBBY_RESEARCH and g_currentPreviewVehicle.isPresent():
            event_dispatcher.showResearchView(self._vehicleCD, exitEvent=events.LoadViewEvent(SFViewLoadParams(VIEW_ALIAS.LOBBY_TECHTREE), ctx={'nation': g_currentPreviewVehicle.item.nationName}))
        elif self._backAlias == VIEW_ALIAS.VEHICLE_PREVIEW:
            entity = ctx.get('entity', None) if ctx else None
            if entity:
                descriptor = entity.typeDescriptor
                event_dispatcher.showVehiclePreview(descriptor.type.compactDescr, previewAlias=self._previousBackAlias)
            else:
                event_dispatcher.showHangar()
        elif self._backAlias == VIEW_ALIAS.LOBBY_STORE:
            showShop()
        else:
            event = g_entitiesFactories.makeLoadEvent(SFViewLoadParams(self._backAlias), {'isBackEvent': True})
            self.fireEvent(event, scope=EVENT_BUS_SCOPE.LOBBY)
        return

    def __onInventoryChanged(self, *_):
        if not BuyVehicleWindow.getInstances():
            g_currentPreviewVehicle.selectNoVehicle()

    def __onOfferChanged(self, event):
        self.__currentOffer = event.ctx.get('offer')

    def __updateModuleBullet(self):
        self.as_setBulletVisibilityS(_getModulesTabIdx(), _isModuleBulletVisible())

    def __resetPostProgressionBullet(self):
        if _isPostProgressionBulletVisible(settingsCore=self.__settingsCore):
            self.__settingsCore.serverSettings.saveInUIStorage({UI_STORAGE_KEYS.VEH_PREVIEW_POST_PROGRESSION_BULLET_SHOWN: True})
