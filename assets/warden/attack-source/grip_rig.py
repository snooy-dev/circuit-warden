"""Pose the original Warden parts around a single weapon hand and grip socket."""

from dataclasses import dataclass
from math import atan2, cos, hypot, radians, sin
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt, map_coordinates

ART = Path(__file__).resolve().parents[3] / 'art/warden'
SS = 3
Y, X = np.mgrid[:480, :480]
COLORS = '020816 00193E 002B64 003E8B 0050B1 0064CA 007BDB 0091E5 00ABEA 00C3ED 00DAF2 19EFF6 5BF7F9 A3FDFD DCFFFF FFFFFF'.split()
PALETTE = Image.new('P', (1, 1))
PALETTE.putpalette(list(bytes.fromhex(''.join(COLORS + [COLORS[-1]] * (256 - len(COLORS))))))


@dataclass(frozen=True)
class Key:
    view: str
    pelvis: tuple[int, int]
    pitch: int
    head: int
    shoulder: int
    upper_arm: int
    forearm: int
    blade: int
    length: int
    cloth: int
    legs: int


# Shoulder and elbow angles drive one hand. Blade angles follow that grip.
AIR = (
    Key('side',(126,154),-3,-1,0,160,40,0,0,3,-18),
    Key('side',(126,155),-8,3,-2,69,-158,-161,49,-9,-25),
    Key('side',(128,154),0,-1,2,20,-153,-120,51,-14,-28),
    Key('side',(129,153),8,-4,3,35,-75,-56,53,-21,-22),
    Key('side',(131,154),12,-5,4,40,-51,-42,58,-24,-19),
    Key('side',(132,154),16,-5,4,50,-24,2,54,-35,-15),
    Key('side',(132,156),17,-5,3,74,-7,28,54,-39,-15),
    Key('side',(131,156),11,-3,2,92,7,49,52,-27,-16),
    Key('side',(129,155),6,-2,1,115,10,62,29,-12,-11),
    Key('side',(127,154),1,0,0,140,27,0,0,-7,-15),
    Key('side',(126,154),-2,0,0,155,35,0,0,0,-18),
)
DOWN = (
    Key('side',(103,96),-2,0,0,155,35,0,0,4,-14),
    Key('side',(103,96),-4,1,1,69,-50,-17,50,-6,-21),
    Key('front',(104,96),4,-2,3,35,-25,24,53,-13,-26),
    Key('front',(104,97),0,1,3,24,70,73,54,-17,-28),
    Key('front',(103,97),-7,3,0,42,132,151,54,-29,-25),
    Key('front',(103,97),-5,3,-1,45,156,163,45,-35,-21),
    Key('front',(103,96),-2,1,0,25,155,166,25,-20,-17),
    Key('side',(104,96),3,-1,0,120,53,0,0,-10,-18),
    Key('side',(104,96),0,0,0,140,43,0,0,-3,-14),
    Key('side',(103,96),-2,0,0,155,35,0,0,3,-14),
)

def ellipse_mask(size, box):
    alpha = Image.new('L', size)
    ImageDraw.Draw(alpha).ellipse(box, fill=255)
    return alpha


def prepare_master(relative, near_arm, head_cut):
    src = Image.open(ART / relative).convert('RGBA').resize((480,480),Image.Resampling.LANCZOS)
    pixels = np.array(src)
    red,green,blue = pixels[:,:,:3].transpose(2,0,1)
    pixels[(red>166)&(blue>155)&(green<127)] = 0
    art = Image.fromarray(pixels.copy())
    mask = Image.new('1',art.size)
    ImageDraw.Draw(mask).polygon(near_arm,fill=1)
    covered = np.asarray(mask)
    _,nearest=distance_transform_edt(covered,return_indices=True)
    pixels[covered]=pixels[tuple(nearest[:,covered])]
    head = art.copy()
    head.putalpha(Image.fromarray(np.where(Y <= head_cut, np.asarray(art.getchannel('A')), 0).astype('uint8')))
    pixels[Y < head_cut - 7] = 0
    return pixels,head,art


SIDE, SIDE_HEAD, SIDE_ART = prepare_master(
    'shading-restore/proportion-fix-v1/warden-proportion-restored.png',
    [(232,322),(258,322),(264,337),(259,350),(247,359),(232,355),(227,337)],266)
FRONT, FRONT_HEAD, _ = prepare_master(
    'reference/master-source.png',
    [(163,317),(192,321),(188,345),(179,361),(166,366),(158,355),(158,334)],258)

# All limb pieces use the original arm shading, with one continuous glove over the grip.
ARM = SIDE_ART.crop((233,323,262,359))
ARM.putalpha(ellipse_mask(ARM.size,(1,0,26,35)))
HAND = SIDE_ART.crop((239,332,259,352))
HAND.putalpha(ellipse_mask(HAND.size,(1,2,18,18)))
SWORD = Image.open(ART/'reference/energy-sword-master-v2.png').convert('RGBA')
SWORD.putalpha(SWORD.getchannel('A').point(lambda a:255 if a>=194 else 0))
GRIP = (419,887)
TIP = (1386,79)


def place(image, origin, position, angle, scale, size):
    ox,oy=origin
    x,y=(k*SS for k in position)
    c,s=cos(angle)/(scale*SS),sin(angle)/(scale*SS)
    return image.transform((size[0]*SS,size[1]*SS),Image.Transform.AFFINE,
                           (c,s,ox-c*x-s*y,-s,c,oy+s*x-c*y),Image.Resampling.BICUBIC)


def point(p, origin, target, angle, scale):
    x,y=((a-b)*scale for a,b in zip(p,origin,strict=True))
    c,s=cos(angle),sin(angle)
    return target[0]+c*x-s*y,target[1]+s*x+c*y


def end_point(start, length, angle):
    theta = radians(angle)
    return start[0] + cos(theta) * length, start[1] + sin(theta) * length


def arm_piece(start,end,width,size):
    dx,dy=end[0]-start[0],end[1]-start[1]
    length=hypot(dx,dy)+3.4
    # Raster tube adapted from the original arm, with overlap at elbow and wrist.
    part=ARM.resize((round(width*SS),round(length*SS)),Image.Resampling.LANCZOS)
    return place(part,(part.width/2,1.7*SS),start,atan2(dy,dx)-radians(90),1/SS,size)


def render(key,size):
    side=key.view=='side'
    pixels,head,hip,neck,shoulder,scale=(
        (SIDE,SIDE_HEAD,(276,369),(272,267),(249,316),.22) if side else
        (FRONT,FRONT_HEAD,(245,375),(237,255),(175,313),.197)
    )
    pitch=radians(key.pitch)
    rear=np.clip((228-X)/115,0,1)*np.clip((Y-285)/35,0,1)
    foot=np.clip((Y-350)/80,0,1)*(1-rear)
    sy=Y+rear*key.cloth-foot*key.legs
    sx=X+foot*key.legs*.30
    part=Image.fromarray(np.stack([map_coordinates(pixels[:,:,c],(sy,sx),order=1) for c in range(4)],axis=-1))
    frame=place(part,hip,key.pelvis,pitch,scale,size)
    head_center=point(neck,hip,key.pelvis,pitch,scale)
    frame.alpha_composite(place(head,neck,head_center,pitch+radians(key.head),scale,size))
    mount=point(shoulder,hip,key.pelvis,pitch,scale)
    mount=(mount[0]+key.shoulder,mount[1])
    elbow=end_point(mount,12,key.upper_arm)
    hand=end_point(elbow,13,key.forearm)
    # Both the wrist and the weapon use this one socket. It never changes arms.
    frame.alpha_composite(arm_piece(mount,elbow,7.5,size))
    frame.alpha_composite(arm_piece(elbow,hand,6.9,size))
    theta=radians(key.blade)
    tip=None
    if key.length:
        wrist_turn = (key.blade - key.forearm + 180) % 360 - 180
        assert abs(wrist_turn) <= 60, (key, wrist_turn)
        vx,vy=TIP[0]-GRIP[0],TIP[1]-GRIP[1]
        scale_weapon=key.length/hypot(vx,vy)
        frame.alpha_composite(place(SWORD,GRIP,hand,theta-atan2(vy,vx),scale_weapon,size))
        tip=(hand[0]+cos(theta)*key.length,hand[1]+sin(theta)*key.length)
    frame.alpha_composite(place(HAND,(10,10),hand,theta,.34,size))
    reduced=frame.resize(size,Image.Resampling.LANCZOS)
    alpha=reduced.getchannel('A').point(lambda a:255 if a>145 else 0)
    reduced=reduced.convert('RGB').quantize(palette=PALETTE,dither=Image.Dither.NONE).convert('RGBA')
    reduced.putalpha(alpha)
    far_mount=point((309,317),hip,key.pelvis,pitch,scale)
    return reduced, (key.pelvis,head_center,far_mount,mount,elbow,hand,tip)


if __name__ == '__main__':
    from build import WARDEN, sheet

    for keys, size, columns, path in (
        (AIR, (256, 224), 6, WARDEN / 'attack-source/air-poses.png'),
        (DOWN, (208, 208), 5, WARDEN / 'downstrike-source/poses.png'),
    ):
        frames = [render(key, size)[0] for key in keys]
        sheet(frames, size, columns).save(path)
