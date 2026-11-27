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
    Key(0,0,0,60,61,0,0,65,(-18,-66,42,-37),(-154,-72,-145,-22),(36,-65,23,-73),(-27,-57,-20,-68),(0,0),0),
    Key(28,-1,0,52,43,-7,9,64,(-85,-49,-97,20),(-150,-71,-132,12),(30,-61,19,-77),(-20,-52,-16,-73),(-9,12),46),
    Key(60,-0.5,0,55,45,-8,8,63,(-67,-51,-70,26),(-143,-70,-131,19),(25,-54,19,-78),(-16,-47,-10,-72),(-12,15),52),
    Key(82,0,1,62,53,-2,5,67,(-39,-37,-38,50),(-138,-72,-130,26),(21,-51,17,-80),(-15,-43,-8,-70),(3,12),52),
    Key(100,3,1,70,76,13,-7,72,(72,-26,80,27),(-147,-75,-134,28),(18,-48,11,-78),(-19,-43,-14,-67),(-1,6),52),
    Key(122,4,0,77,94,16,-12,77,(77,-31,89,2),(-157,-75,-141,25),(17,-52,15,-76),(-25,-46,-16,-67),(5,-7),52),
    Key(144,4,-1,83,105,19,-10,80,(87,-51,97,-23),(-149,-70,-138,13),(25,-56,17,-74),(-29,-49,-18,-72),(8,-9),52),
    Key(169,3,-1,82,98,12,-4,76,(60,-60,89,-41),(-148,-72,-137,0),(28,-61,18,-74),(-29,-53,-20,-70),(8,-8),49),
    Key(195,2,0,73,83,5,0,73,(26,-63,63,-47),(-151,-74,-140,-18),(33,-64,20,-73),(-31,-55,-18,-69),(7,-6),23),
    Key(220,1,0,65,68,1,0,69,(-12,-66,45,-41),(-153,-74,-144,-21),(36,-65,23,-73),(-29,-57,-19,-68),(0,0),0),
    Key(300,0,0,60,61,0,0,65,(-18,-66,42,-37),(-154,-72,-145,-22),(36,-65,23,-73),(-27,-57,-20,-68),(0,0),0),
)

DOWN = (
    Key(0,0,0,59,60,0,0,65,(-18,-66,42,-37),(-154,-72,-145,-22),(36,-65,23,-73),(-27,-57,-20,-68),(0,0),0),
    Key(8,0,0,48,45,1,7,53,(40,-46,75,-11),(-151,-70,-138,-11),(35,-64,24,-75),(-31,-55,-20,-70),(4,11),48),
    Key(18,0,1,39,31,3,10,35,(52,-38,89,-24),(-146,-68,-126,5),(34,-57,23,-78),(-34,-51,-25,-70),(4,8),53),
    Key(28,1,1,30,20,5,5,20,(38,-48,61,-48),(-141,-68,-120,23),(33,-51,24,-78),(-35,-46,-25,-70),(4,-4),53),
    Key(36,1,0,23,9,4,-2,8,(18,-63,16,-66),(-144,-65,-121,29),(31,-46,22,-78),(-33,-46,-26,-71),(0,-1),53),
    Key(47,0,0,13,-7,1,-11,-3,(-20,-59,-62,-50),(-147,-65,-121,32),(33,-44,26,-78),(-34,-44,-26,-73),(-7,-2),53),
    Key(66,-1,1,9,-15,-3,-15,-10,(-15,-66,-97,-3),(-143,-65,-124,24),(34,-49,27,-73),(-36,-48,-28,-68),(-4,8),50),
    Key(85,-1,2,13,-8,-2,-10,0,(-18,-66,-82,19),(-149,-69,-128,16),(37,-56,22,-74),(-36,-54,-25,-70),(-3,9),26),
    Key(108,0,1,24,23,0,-5,22,(-7,-67,-25,-41),(-150,-73,-135,7),(37,-60,23,-74),(-33,-55,-22,-72),(0,0),0),
    Key(146,0,0,46,50,0,0,54,(-14,-66,27,-37),(-152,-74,-141,-15),(35,-63,22,-73),(-29,-57,-21,-69),(0,0),0),
    Key(210,0,0,59,60,0,0,65,(-18,-66,42,-37),(-154,-72,-145,-22),(36,-65,23,-73),(-27,-57,-20,-68),(0,0),0),
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
