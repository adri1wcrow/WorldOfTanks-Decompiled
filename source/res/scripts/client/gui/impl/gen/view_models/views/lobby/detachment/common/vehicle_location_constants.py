# Python bytecode 2.7 (decompiled from Python 2.7)
# Embedded file name: scripts/client/gui/impl/gen/view_models/views/lobby/detachment/common/vehicle_location_constants.py
from frameworks.wulf import ViewModel

class VehicleLocationConstants(ViewModel):
    __slots__ = ()
    IN_STORAGE = 'inStorage'
    NOT_IN_STORAGE = 'notInStorage'

    def __init__(self, properties=0, commands=0):
        super(VehicleLocationConstants, self).__init__(properties=properties, commands=commands)

    def _initialize(self):
        super(VehicleLocationConstants, self)._initialize()
