# Python bytecode 2.7 (decompiled from Python 2.7)
# Embedded file name: scripts/client/gui/impl/wrappers/user_drop_down_menu_model.py
import logging
from gui.impl.gen.view_models.ui_kit.drop_down_menu_item_model import DropDownMenuItemModel
from gui.impl.gen.view_models.views.lobby.lootboxes.components.loot_box_drop_down_menu_item_model import LootBoxDropDownMenuItemModel
from gui.impl.wrappers.user_list_model import UserListModel
_logger = logging.getLogger(__name__)

class UserDropDownMenuModel(UserListModel):
    __slots__ = ()

    def addItem(self, actionID, label, icon=None, isEnabled=True):
        item = DropDownMenuItemModel()
        item.setId(actionID)
        item.setLabel(label)
        item.setIsEnabled(isEnabled)
        if icon is not None:
            item.setIcon(icon)
        self.getItems().addViewModel(item)
        return

    def getItemByID(self, actionID):
        try:
            return next((item for item in self.getItems() if item.getId() == actionID))
        except StopIteration:
            _logger.error("Item with actionID '%d' is not found in drop down list", actionID)
            return None

        return None


class NyDropDownMenuModel(UserListModel):
    __slots__ = ()

    def addItem(self, actionID, label=None, labelStr=None, icon=None, isEnabled=True):
        item = LootBoxDropDownMenuItemModel()
        item.setId(actionID)
        if labelStr is not None:
            item.setLabelStr(labelStr)
        elif label is not None:
            item.setLabel(label)
        item.setIsEnabled(isEnabled)
        if icon is not None:
            item.setIcon(icon)
        self.getItems().addViewModel(item)
        return

    def getItemByID(self, actionID):
        for item in self.getItems():
            if item.getId() == actionID:
                return item

        _logger.error("Item with actionID '%d' is not found in drop down list", actionID)
        return None
