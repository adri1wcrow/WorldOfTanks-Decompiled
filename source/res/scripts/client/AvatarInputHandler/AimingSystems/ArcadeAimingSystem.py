# Python bytecode 2.7 (decompiled from Python 2.7)
# Embedded file name: scripts/client/AvatarInputHandler/AimingSystems/ArcadeAimingSystem.py
import functools
import math
import BigWorld
import Math
from Math import Vector3, Matrix
import math_utils
from AvatarInputHandler import AimingSystems
from AvatarInputHandler.AimingSystems import IAimingSystem
from ProjectileMover import collideDynamic
from constants import CollisionFlags
from debug_utils import LOG_WARNING
import gun_rotation_shared

class ArcadeAimingSystem(IAimingSystem):

    def __setDistanceFromFocus(self, value):
        shotPoint = self.getThirdPersonShotPoint()
        self.__cursor.distanceFromFocus = value
        posOnVehicleProv = self.positionAboveVehicleProv.value
        posOnVehicle = Vector3(posOnVehicleProv.x, posOnVehicleProv.y, posOnVehicleProv.z)
        camPos = self.matrix.translation
        triBase = camPos - posOnVehicle
        pivotToTarget = shotPoint - posOnVehicle
        camPosToTarget = shotPoint - camPos
        if triBase.dot(camPosToTarget) * triBase.dot(pivotToTarget) > 0.0:
            if self.__shotPointCalculator is not None:
                self.__adjustFocus()
            else:
                self.focusOnPos(shotPoint)
        return

    def __setVehicleMProv(self, value):
        self.__vehicleMProv = value
        self.__cursor.base = value

    def __setYaw(self, value):
        self.__cursor.yaw = value
        if self.__cursor.yaw > 2.0 * math.pi:
            self.__cursor.yaw -= 2.0 * math.pi
        elif self.__cursor.yaw < -2.0 * math.pi:
            self.__cursor.yaw += 2.0 * math.pi

    def __setPitch(self, value):
        self.__cursor.pitch = math_utils.clamp(self.__anglesRange[0], self.__anglesRange[1], value)

    @property
    def aimMatrix(self):
        return self.__aimMatrix

    @aimMatrix.setter
    def aimMatrix(self, aimMatrix):
        self.__aimMatrix = aimMatrix
        self.__setDistanceFromFocus(self.distanceFromFocus)

    vehicleMProv = property(lambda self: self.__vehicleMProv, __setVehicleMProv)
    positionAboveVehicleProv = property(lambda self: self.__cursor.positionAboveBaseProvider)
    distanceFromFocus = property(lambda self: self.__cursor.distanceFromFocus, __setDistanceFromFocus)
    yaw = property(lambda self: self.__cursor.yaw, __setYaw)
    pitch = property(lambda self: self.__cursor.pitch, __setPitch)
    idealMatrix = property(lambda self: self.__idealMatrix)

    def __init__(self, vehicleMProv, heightAboveTarget, focusRadius, aimMatrix, anglesRange, enableSmartShotPointCalc=True):
        IAimingSystem.__init__(self)
        self.__aimMatrix = aimMatrix
        self.__vehicleMProv = vehicleMProv
        self.__anglesRange = anglesRange
        self.__cursor = BigWorld.ThirdPersonProvider()
        self.__cursor.base = vehicleMProv
        self.__cursor.heightAboveBase = heightAboveTarget
        self.__cursor.focusRadius = focusRadius
        self.__idealMatrix = Math.Matrix(self._matrix)
        self.__shotPointCalculator = ShotPointCalculatorPlanar() if enableSmartShotPointCalc else None
        self.__worldSpaceAimingWithLimits = _WorldSpaceAimingWithLimits(self.__vehicleMProv)
        self._vehicleTypeDescriptor = None
        self.__cachedScanDirection = Vector3(0.0, 0.0, 0.0)
        self.__cachedScanStart = Vector3(0.0, 0.0, 0.0)
        self.__cursorShouldCheckCollisions = True
        return

    def getPivotSettings(self):
        return (self.__cursor.heightAboveBase, self.__cursor.focusRadius)

    def setPivotSettings(self, heightAboveBase, focusRadius):
        self.__cursor.heightAboveBase = heightAboveBase
        self.__cursor.focusRadius = focusRadius

    def setAnglesRange(self, anglesRange):
        self.__anglesRange = anglesRange

    def cursorShouldCheckCollisions(self, shouldCheckCollisions=True):
        self.__cursorShouldCheckCollisions = shouldCheckCollisions

    def setMinDistanceForShotPointCalc(self, minDist=None):
        if self.__shotPointCalculator:
            self.__shotPointCalculator.setMinDistance(minDist=minDist)

    def destroy(self):
        IAimingSystem.destroy(self)

    def enable(self, targetPos, turretYaw=None, gunPitch=None):
        if targetPos is not None:
            self.focusOnPos(targetPos)
            if turretYaw is not None and gunPitch is not None:
                self.__adjustFocus((turretYaw, gunPitch))
        playerV = BigWorld.player().getVehicleAttached()
        if playerV is not None:
            self._vehicleTypeDescriptor = playerV.typeDescriptor
        if self.__shotPointCalculator is not None:
            self.__shotPointCalculator.updateVehicleDescr(self._vehicleTypeDescriptor)
        return

    def getShotPoint(self):
        return self.getThirdPersonShotPoint()

    def getZoom(self):
        return self.distanceFromFocus

    def __adjustFocus(self, yawPitch=None):
        if self.__shotPointCalculator is None:
            return
        else:
            scanStart, scanDir = self.__getScanRay()
            self.focusOnPos(self.__shotPointCalculator.focusAtPos(scanStart, scanDir, yawPitch))
            return

    def disable(self):
        pass

    def setDynamicCollisions(self, enable):
        self.__cursor.setDynamicCollisions(enable)

    def initAdvancedCollider(self, fovRatio, rollbackSpeed, minimalCameraDistance, speedThreshold, minVolume):
        self.__cursor.initAdvancedCollider(fovRatio, rollbackSpeed, minimalCameraDistance, speedThreshold, minVolume)

    def addVolumeGroup(self, group):
        self.__cursor.addVolumeGroup(group)

    def focusOnPos(self, preferredPos):
        if self.__worldSpaceAimingWithLimits.isEnabled:
            self.__worldSpaceAimingWithLimits.focusOnPos(preferredPos)
        vehPos = Matrix(self.__vehicleMProv).translation
        posOnVehicle = vehPos + Vector3(0.0, self.__cursor.heightAboveBase, 0.0)
        self.yaw = (preferredPos - vehPos).yaw
        xzDir = Vector3(self.__cursor.focusRadius * math.sin(self.__cursor.yaw), 0.0, self.__cursor.focusRadius * math.cos(self.__cursor.yaw))
        pivotPos = posOnVehicle + xzDir
        self.pitch = self.__calcPitchAngle(self.__cursor.distanceFromFocus, preferredPos - pivotPos)
        self.__updateInternal()

    def __updateInternal(self):
        self.__cursor.update(self.__cursorShouldCheckCollisions)
        aimMatrix = self.__getLookToAimMatrix()
        aimMatrix.postMultiply(self.__cursor.matrix)
        self._matrix.set(aimMatrix)
        self.__updateScanRay()
        aimWithIdealMatrix = self.__getLookToAimMatrix()
        aimWithIdealMatrix.postMultiply(self.__cursor.idealMatrix)
        self.__idealMatrix.set(aimWithIdealMatrix)
        if self.__shotPointCalculator is not None and not self.__worldSpaceAimingWithLimits.isEnabled:
            self.__shotPointCalculator.update(*self.__getScanRay())
        return 0.0

    def __calcPitchAngle(self, distanceFromFocus, direction):
        alpha = -self.__aimMatrix.pitch
        a = distanceFromFocus
        b = direction.length
        A = 2.0 * a * math.cos(alpha)
        B = a * a - b * b
        D = A * A - 4.0 * B
        if D > 0.0:
            c1 = (A + math.sqrt(D)) * 0.5
            c2 = (A - math.sqrt(D)) * 0.5
            c = c1 if c1 > c2 else c2
            cosValue = (a * a + b * b - c * c) / (2.0 * a * b) if a * b != 0.0 else 2.0
            if cosValue < -1.0 or cosValue > 1.0:
                LOG_WARNING('Invalid arg for acos: %f; distanceFromFocus: %f, dir: %s' % (cosValue, distanceFromFocus, direction))
                return -direction.pitch
            beta = math.acos(cosValue)
            eta = math.pi - beta
            return -direction.pitch - eta
        else:
            return -direction.pitch

    def getDesiredShotPoint(self):
        scanStart, scanDir = self.__getScanRay()
        if self.__worldSpaceAimingWithLimits.isEnabled:
            return self.__worldSpaceAimingWithLimits.getShotPoint()
        else:
            return self.getThirdPersonShotPoint() if self.__shotPointCalculator is None else self.__shotPointCalculator.getDesiredShotPoint(scanStart, scanDir)

    def getThirdPersonShotPoint(self):
        if self.__worldSpaceAimingWithLimits.isEnabled:
            return self.__worldSpaceAimingWithLimits.getAimPoint()
        elif self.__shotPointCalculator is not None:
            return self.__shotPointCalculator.aimPlane.intersectRay(*self.__getScanRay())
        else:
            shotDistance = self._vehicleTypeDescriptor.shot.maxDistance if self._vehicleTypeDescriptor else 10000.0
            return AimingSystems.getDesiredShotPoint(shotDistance=shotDistance, *self.__getScanRay())

    def handleMovement(self, dx, dy):
        if self.__worldSpaceAimingWithLimits.isEnabled:
            ddx, ddy = self.__calculateWorldAimMovement(dx, dy)
            self.__worldSpaceAimingWithLimits.move(ddx, ddy)
            self.__cursor.lookAt(self.__worldSpaceAimingWithLimits.getAimPoint())
        else:
            self.yaw += dx
            self.pitch += dy

    def update(self, deltaTime):
        return self.__updateInternal()

    def __getScanRay(self):
        return (self.__cachedScanStart, self.__cachedScanDirection)

    def __getLookToAimMatrix(self):
        return Matrix(self.__aimMatrix)

    def __updateScanRay(self):
        self.__cachedScanDirection = self._matrix.applyVector(Vector3(0.0, 0.0, 1.0))
        self.__cachedScanStart = self._matrix.translation + self.__cachedScanDirection * 0.3

    def setAimingLimits(self, limits):
        if limits is None:
            self.__worldSpaceAimingWithLimits.isEnabled = False
            return
        else:
            currentLookPoint = self.getThirdPersonShotPoint()
            self.__worldSpaceAimingWithLimits.init(limits, currentLookPoint)
            self.__worldSpaceAimingWithLimits.isEnabled = True
            self.__cursor.lookAt(currentLookPoint)
            return

    def __calculateWorldAimMovement(self, dx, dy):
        nextAimRadius = currentAimRadius = math.fabs(self.__cursor.heightAboveBase / math.tan(self.pitch))
        if dy != 0:
            newPitch = math_utils.clamp(self.__anglesRange[0], -0.001, self.pitch + dy)
            nextAimRadius = math.fabs(self.__cursor.heightAboveBase / math.tan(newPitch))
        ddx = math.tan(dx) * currentAimRadius
        ddy = nextAimRadius - currentAimRadius
        return (ddx, ddy)


class _AimPlane(object):
    __EPS_COLLIDE_ARENA = 0.001

    def __init__(self):
        self.__plane = Math.Plane()
        self.init(Vector3(0.0, 0.0, 0.0), Vector3(0.0, 0.0, 0.0))

    def init(self, aimPos, targetPos):
        lookDir = targetPos - aimPos
        self.__lookLength = lookDir.length
        lookDir.normalise()
        self.__plane.init(targetPos, targetPos + Vector3(0.0, 0.0, 1.0), targetPos + Vector3(1.0, 0.0, 0.0))
        self.__initialProjection = Vector3(0.0, 1.0, 0.0).dot(lookDir)

    def intersectRay(self, startPos, direction, checkCloseness=True, checkSign=True):
        collisionPoint = self.__plane.intersectRay(startPos, direction)
        projection = Vector3(0.0, 1.0, 0.0).dot(direction)
        tooClose = collisionPoint.distTo(startPos) - self.__lookLength < -0.0001 and checkCloseness
        parallelToPlane = abs(projection) <= _AimPlane.__EPS_COLLIDE_ARENA
        projectionSignDiffers = projection * self.__initialProjection < 0.0 and checkSign
        backwardCollision = (collisionPoint - startPos).dot(direction) <= 0.0
        return startPos + direction * self.__lookLength if tooClose or parallelToPlane or projectionSignDiffers or backwardCollision else collisionPoint


class ShotPointCalculatorPlanar(object):

    class CachedResult(object):

        def __init__(self):
            self.frameStamp = BigWorld.wg_getFrameTimestamp()
            self.scanStart = Vector3(0.0, 0.0, 0.0)
            self.scanDir = Vector3(0.0, 0.0, 0.0)
            self.result = Vector3(0.0, 0.0, 0.0)
            self.isConvenient = False

        def update(self, frameStamp, scanStart, scanDir, result, isConvenient):
            self.frameStamp = frameStamp
            self.scanStart = scanStart
            self.scanDir = scanDir
            self.result = result
            self.isConvenient = isConvenient

    MIN_DIST = 50
    TERRAIN_MIN_ANGLE = math.pi / 6
    aimPlane = property(lambda self: self.__aimPlane)

    def __init__(self):
        player = BigWorld.player()
        self.__vehicleMat = player.inputHandler.steadyVehicleMatrixCalculator.outputMProv
        self.__vehicleDesc = player.vehicleTypeDescriptor
        self.__aimPlane = _AimPlane()
        self.__getTurretMat = functools.partial(AimingSystems.getTurretJointMat, self.__vehicleDesc, self.__vehicleMat)
        self.__cachedResult = ShotPointCalculatorPlanar.CachedResult()
        self.__minDist = ShotPointCalculatorPlanar.MIN_DIST

    def setMinDistance(self, minDist=None):
        if minDist is None:
            self.__minDist = ShotPointCalculatorPlanar.MIN_DIST
        else:
            self.__minDist = minDist
        return

    def updateVehicleDescr(self, vehicleDesr):
        if vehicleDesr is not None:
            self.__vehicleDesc = vehicleDesr
        return

    def update(self, scanStart, scanDir):
        point, isPointConvenient = self.__testMouseTargetPoint(scanStart, scanDir)
        if isPointConvenient:
            self.__aimPlane.init(scanStart, point)

    def focusAtPos(self, scanStart, scanDir, yawPitch=None):
        scanPos, isPointConvenient = self.__testMouseTargetPoint(scanStart, scanDir)
        if not isPointConvenient:
            if yawPitch is not None:
                turretYaw, gunPitch = yawPitch
                gunMat = AimingSystems.getGunJointMat(self.__vehicleDesc, self.__getTurretMat(turretYaw), gunPitch)
                planePos = self.__aimPlane.intersectRay(gunMat.translation, gunMat.applyVector(Vector3(0, 0, 1)), False, False)
            else:
                planePos = self.__aimPlane.intersectRay(scanStart, scanDir)
            if scanStart.distSqrTo(planePos) < scanStart.distSqrTo(scanPos):
                return scanPos
            return planePos
        else:
            self.__aimPlane.init(scanStart, scanPos)
            return scanPos

    def getDesiredShotPoint(self, scanStart, scanDir):
        scanPos, isPointConvenient = self.__testMouseTargetPoint(scanStart, scanDir)
        if isPointConvenient:
            return scanPos
        planePos = self.__aimPlane.intersectRay(scanStart, scanDir)
        if scanStart.distSqrTo(planePos) < scanStart.distSqrTo(scanPos):
            return scanPos
        turretYaw, gunPitch = AimingSystems.getTurretYawGunPitch(self.__vehicleDesc, self.__vehicleMat, planePos, True)
        gunMat = AimingSystems.getGunJointMat(self.__vehicleDesc, self.__getTurretMat(turretYaw), gunPitch)
        aimDir = gunMat.applyVector(Vector3(0.0, 0.0, 1.0))
        shotDistance = self.__vehicleDesc.shot.maxDistance
        return AimingSystems.getDesiredShotPoint(gunMat.translation, aimDir, shotDistance=shotDistance)

    def __calculateClosestPoint(self, start, direction):
        direction.normalise()
        distance = self.__vehicleDesc.shot.maxDistance if self.__vehicleDesc is not None else 10000.0
        end = start + direction.scale(distance)
        testResStatic = BigWorld.wg_collideSegment(BigWorld.player().spaceID, start, end, 128)
        testResDynamic = collideDynamic(start, end, (BigWorld.player().playerVehicleID,), False)
        closestPoint = None
        closestDist = 1000000
        isPointConvenient = True
        if testResStatic:
            closestPoint = testResStatic.closestPoint
            closestDist = (closestPoint - start).length
            shouldCheck = True
            if testResStatic.isTerrain():
                shouldCheck = testResStatic.normal.dot(Math.Vector3(0.0, 1.0, 0.0)) <= math.cos(ShotPointCalculatorPlanar.TERRAIN_MIN_ANGLE)
            if shouldCheck:
                isPointConvenient = closestDist >= self.__minDist
        if closestPoint is None and testResDynamic is None:
            return (AimingSystems.shootInSkyPoint(start, direction), True)
        else:
            if testResDynamic is not None:
                dynDist = testResDynamic[0]
                if dynDist <= closestDist:
                    direction = end - start
                    direction.normalise()
                    closestPoint = start + direction * dynDist
                    isPointConvenient = True
            return (closestPoint, isPointConvenient)

    def __testMouseTargetPoint(self, start, direction):
        currentFrameStamp = BigWorld.wg_getFrameTimestamp()
        if self.__cachedResult.frameStamp == currentFrameStamp and self.__cachedResult.scanStart == start and self.__cachedResult.scanDir == direction:
            return (self.__cachedResult.result, self.__cachedResult.isConvenient)
        descr = self.__vehicleDesc
        closestPoint, isPointConvenient = self.__calculateClosestPoint(start, direction)
        turretYaw, gunPitch = AimingSystems.getTurretYawGunPitch(descr, self.__vehicleMat, closestPoint, True)
        if not isPointConvenient:
            _, maxPitch = gun_rotation_shared.calcPitchLimitsFromDesc(turretYaw, descr.gun.pitchLimits, descr.hull.turretPitches[0], descr.turret.gunJointPitch)
            pitchInBorders = gunPitch <= maxPitch + 0.001
            isPointConvenient = not pitchInBorders
        if isPointConvenient:
            isPointConvenient = not self.__isTurretTurnRequired(direction, turretYaw, closestPoint)
        self.__cachedResult.update(currentFrameStamp, start, direction, closestPoint, isPointConvenient)
        return (closestPoint, isPointConvenient)

    def __isTurretTurnRequired(self, viewDir, turretYawOnPoint, targetPoint):
        turretMat = self.__getTurretMat(turretYawOnPoint)
        turretPos = turretMat.translation
        gunPos = AimingSystems.getGunJointMat(self.__vehicleDesc, turretMat, 0.0).translation
        dirFromTurretPos = targetPoint - turretPos
        dirFromSniperPos = targetPoint - gunPos
        viewDir = Math.Vector3(viewDir)
        viewDir.y = 0.0
        viewDir.normalise()
        dirFromSniperPos.y = 0.0
        dirFromTurretPos.y = 0.0
        return viewDir.dot(dirFromSniperPos) < 0.0 or viewDir.dot(dirFromTurretPos) < 0.0


class _WorldSpaceAimingWithLimits(object):

    def __init__(self, basis):
        self.__aimingLimit = (0, 0)
        self.__basis = basis
        self.__aimingPoint = Vector3(0, 0, 0)
        self.__enabled = False
        self.__lastCachedFrame = None
        self.__cachedShotPoint = Vector3(0, 0, 0)
        return

    @property
    def isEnabled(self):
        return self.__enabled

    @isEnabled.setter
    def isEnabled(self, enabled):
        if self.__enabled != enabled:
            self.__enabled = enabled
            if enabled:
                self.move(0, 0)

    def init(self, aimingLimits, initialAimingPoint):
        near = max(min(aimingLimits[0], aimingLimits[1]), 1)
        far = max(aimingLimits[0], aimingLimits[1], near)
        self.__aimingLimit = (near, far)
        origin = Matrix(self.__basis).translation
        self.__aimingPoint = initialAimingPoint - origin
        self.__aimingPoint.y = 0
        if self.__aimingPoint.lengthSquared == 0:
            self.__aimingPoint = Vector3(0, 0, near)
        self.__lastCachedFrame = None
        return

    def getAimPoint(self):
        return Matrix(self.__basis).translation + self.__aimingPoint

    def getShotPoint(self):
        currentFrameStamp = BigWorld.wg_getFrameTimestamp()
        if self.__lastCachedFrame != currentFrameStamp:
            wsAimPoint = self.getAimPoint()
            self.__cachedShotPoint = wsAimPoint
            if not (BigWorld.player().isObserver() and BigWorld.player().isObserverFPV):
                groundIntersection = BigWorld.wg_collideSegment(BigWorld.player().spaceID, wsAimPoint + Vector3(0, 200, 0), wsAimPoint - Vector3(0, 200, 0), CollisionFlags.TRIANGLE_PROJECTILENOCOLLIDE)
                if groundIntersection is None:
                    LOG_WARNING('Cannot determine on-ground target, point: ', wsAimPoint, ' not over or under ground')
                else:
                    self.__cachedShotPoint = groundIntersection.closestPoint
            self.__lastCachedFrame = currentFrameStamp
        return self.__cachedShotPoint

    def focusOnPos(self, pos):
        self.__aimingPoint = pos - Matrix(self.__basis).translation

    def move(self, dx, dy):
        forward = Vector3(self.__aimingPoint)
        if forward.x == forward.z == 0:
            forward.z = 1
        forward.normalise()
        right = forward * Vector3(0, -1, 0)
        aimPoint = self.__aimingPoint + forward * dy + right * dx
        self.__aimingPoint = self.__clampToAimLimits(aimPoint)
        self.__lastCachedFrame = None
        return

    def __clampToAimLimits(self, position):
        if not self.isEnabled:
            return position
        if position.x == position.z == 0:
            position.z = 1
        planarAimingVector = Vector3(position.x, 0, position.z)
        length = planarAimingVector.length
        planarAimingVector = planarAimingVector.scale(1.0 / length)
        minLimit = self.__aimingLimit[0]
        maxLimit = self.__aimingLimit[1]
        if minLimit > 0 and length < minLimit:
            position = planarAimingVector * minLimit
        elif maxLimit > 0 and length > maxLimit:
            position = planarAimingVector * maxLimit
        return position
