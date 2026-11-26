"""Blocking coordinates in game pixels. +Y faces the viewer; +Z is up."""

from dataclasses import dataclass
from math import cos, sin, radians
import numpy as np
from scipy.interpolate import PchipInterpolator


@dataclass(frozen=True)
class Key:
    time: int
    x: float
    z: float
    hip_yaw: int
    chest_yaw: int
    lean: int
    roll: int
    head_yaw: int
    arm: tuple
    free_arm: tuple
    near_leg: tuple
    far_leg: tuple
    grip: tuple
    blade: float


# Limb values are upper azimuth/elevation and lower azimuth/elevation.
# Palm values are independent, small yaw/elevation offsets from the forearm.
AIR = (
    Key(0,0,0,60,61,0,0,65,(-18,-66,42,-37),(-85,-63,-70,-35),(66,-65,75,-72),(-82,-68,53,-76),(0,0),0),
    Key(28,-1,0,52,43,-7,9,64,(-85,-49,-97,20),(77,-41,73,-21),(74,-58,76,-73),(-85,-56,57,-76),(-9,12),46),
    Key(60,-.5,0,55,45,-8,8,63,(-67,-51,-70,26),(61,-41,59,-16),(77,-55,67,-63),(-80,-54,56,-72),(-12,15),52),
    Key(82,0,1,62,53,-2,5,67,(-39,-37,-38,50),(22,-46,14,-30),(70,-50,66,-66),(-90,-57,56,-72),(3,12),52),
    Key(100,3,1,70,76,13,-7,72,(72,-26,80,27),(-62,-44,-90,-16),(80,-50,60,-70),(-87,-61,48,-71),(-1,6),52),
    Key(122,4,0,77,94,16,-12,77,(77,-31,89,2),(-101,-36,-112,4),(83,-49,54,-75),(-101,-54,47,-65),(5,-7),52),
    Key(144,4,-1,83,105,19,-10,80,(87,-51,97,-23),(-106,-49,-102,6),(72,-56,52,-64),(-111,-53,38,-64),(8,-9),52),
    Key(169,3,-1,82,98,12,-4,76,(60,-60,89,-41),(-101,-57,-91,-20),(69,-65,64,-68),(-100,-56,37,-65),(8,-8),49),
    Key(195,2,0,73,83,5,0,73,(26,-63,63,-47),(-97,-62,-77,-25),(70,-66,64,-70),(-93,-60,39,-73),(7,-6),23),
    Key(220,1,0,65,68,1,0,69,(-12,-66,45,-41),(-86,-63,-69,-35),(67,-65,69,-70),(-86,-65,47,-76),(0,0),0),
    Key(300,0,0,60,61,0,0,65,(-18,-66,42,-37),(-85,-63,-70,-35),(66,-65,75,-72),(-82,-68,53,-76),(0,0),0),
)

DOWN = (
    Key(0,0,0,59,60,0,0,65,(-18,-66,42,-37),(-85,-63,-70,-35),(65,-65,74,-73),(-82,-68,53,-76),(0,0),0),
    Key(8,0,0,48,45,1,7,53,(40,-46,75,-11),(25,-69,38,-50),(66,-60,71,-77),(-72,-61,59,-74),(4,11),48),
    Key(18,0,1,39,31,3,10,35,(52,-38,89,-24),(37,-56,58,-32),(55,-55,61,-79),(-63,-56,45,-80),(4,8),53),
    Key(28,1,1,30,20,5,5,20,(38,-48,61,-48),(65,-38,85,-18),(49,-45,62,-75),(-47,-58,38,-80),(4,-4),53),
    Key(36,1,0,23,9,4,-2,8,(18,-63,16,-66),(71,-38,91,-18),(-16,-53,-25,-73),(43,-54,72,-75),(0,-1),53),
    Key(47,0,0,13,-7,1,-11,-3,(-20,-59,-62,-50),(87,-34,104,0),(-30,-51,-37,-77),(63,-50,77,-70),(-7,-2),53),
    Key(66,-1,1,9,-15,-3,-15,-10,(-47,-54,-97,-3),(92,-41,104,-5),(-37,-57,-26,-74),(64,-48,71,-65),(-4,8),50),
    Key(85,-1,2,13,-8,-2,-10,0,(-35,-54,-82,19),(73,-52,84,-22),(-26,-58,-15,-78),(51,-52,62,-73),(-3,9),26),
    Key(108,0,1,24,23,0,-5,22,(-7,-67,-25,-41),(46,-49,67,-24),(52,-59,62,-76),(-77,-64,43,-79),(0,0),0),
    Key(146,0,0,46,50,0,0,54,(-14,-66,27,-37),(-40,-65,-60,-35),(65,-64,73,-73),(-81,-68,50,-76),(0,0),0),
    Key(210,0,0,59,60,0,0,65,(-18,-66,42,-37),(-85,-63,-70,-35),(65,-65,74,-73),(-82,-68,53,-76),(0,0),0),
)


def angles(azimuth, elevation):
    a, e = radians(azimuth), radians(elevation)
    return np.array((sin(a)*cos(e), cos(a)*cos(e), sin(e)))


def channels(key):
    return [key.x, key.z, key.hip_yaw, key.chest_yaw, key.lean, key.roll, key.head_yaw,
            *key.arm, *key.free_arm, *key.near_leg, *key.far_leg, *key.grip, key.blade]


def clip(keys):
    return PchipInterpolator([k.time for k in keys], [channels(k) for k in keys], axis=0)


def limb(origin, values, lengths):
    a, e, b, f = values
    joint = origin + angles(a,e)*lengths[0]
    return joint, joint + angles(b,f)*lengths[1]


def pose(spline, time):
    x,z,hy,cy,lean,roll,head_yaw,*v = spline(time)
    hip = np.array((x,0.,z))
    chest = hip + angles(cy,90-lean)*16
    torso = chest-hip
    down = -torso/16
    across = angles(cy-90,roll)
    near_shoulder,far_shoulder = chest+11*across,chest-11*across
    near_hip,far_hip = hip+6*angles(hy-90,0),hip-6*angles(hy-90,0)
    neck = chest-down*8
    elbow,hand = limb(near_shoulder,v[:4],(12,13))
    other_elbow,other_hand = limb(far_shoulder,v[4:8],(12,13))
    knee,foot = limb(near_hip,v[8:12],(10,10))
    other_knee,other_foot = limb(far_hip,v[12:16],(10,10))
    da,de,blade = v[16:]
    tip = hand + angles(v[2]+da,v[3]+de)*blade
    # The cloth carries the jump silhouette through the turn and follows it with a delay.
    lag = spline(max(0, time-18))
    tail = hip-angles(lag[2],9)*29 + np.array((-11,0,-2.))
    scarf = chest-angles(lag[3],7)*34 + np.array((-9,0,5.))
    return dict(hip=hip,chest=chest,neck=neck,
                shoulder=near_shoulder,elbow=elbow,hand=hand,tip=tip,length=blade,
                other_shoulder=far_shoulder,other_elbow=other_elbow,other_hand=other_hand,
                near_hip=near_hip,knee=knee,foot=foot,far_hip=far_hip,other_knee=other_knee,other_foot=other_foot,
                tail=tail,scarf=scarf,yaw=cy,hip_yaw=hy,head_yaw=head_yaw)


def project(p, origin, scale=1):
    return (origin[0]+p[0]*scale,origin[1]-(p[2]-.09*p[1])*scale)
