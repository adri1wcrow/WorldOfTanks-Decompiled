# Python bytecode 2.7 (decompiled from Python 2.7)
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/barracks/__init__.py
from frameworks.wulf import WindowLayer
from gui.app_loader import settings as app_settings
from gui.impl.lobby.detachment.context_menu.detachment_card_context_menu import DetachmentCardContextMenu
from gui.impl.lobby.detachment.context_menu.instructor_card_context_menu import InstructorCardContextMenu
from gui.shared import EVENT_BUS_SCOPE
from gui.Scaleform.daapi.settings.views import VIEW_ALIAS
from gui.Scaleform.framework import ViewSettings, ScopeTemplates
from gui.Scaleform.framework.package_layout import PackageBusinessHandler
from gui.Scaleform.genConsts.CONTEXT_MENU_HANDLER_TYPE import CONTEXT_MENU_HANDLER_TYPE

def getContextMenuHandlers():
    return ((CONTEXT_MENU_HANDLER_TYPE.DETACHMENT_CARD_CONTEXT_MENU, DetachmentCardContextMenu), (CONTEXT_MENU_HANDLER_TYPE.INSTRUCTOR_CARD_CONTEXT_MENU, InstructorCardContextMenu))


def getViewSettings():
    from gui.Scaleform.daapi.view.lobby.barracks.Barracks import Barracks
    return (ViewSettings(VIEW_ALIAS.LOBBY_BARRACKS, Barracks, 'barracks.swf', WindowLayer.SUB_VIEW, VIEW_ALIAS.LOBBY_BARRACKS, ScopeTemplates.LOBBY_SUB_SCOPE),)


def getBusinessHandlers():
    return (BarracksPackageBusinessHandler(),)


class BarracksPackageBusinessHandler(PackageBusinessHandler):

    def __init__(self):
        listeners = ((VIEW_ALIAS.LOBBY_BARRACKS, self.loadViewByCtxEvent),)
        super(BarracksPackageBusinessHandler, self).__init__(listeners, app_settings.APP_NAME_SPACE.SF_LOBBY, EVENT_BUS_SCOPE.LOBBY)
