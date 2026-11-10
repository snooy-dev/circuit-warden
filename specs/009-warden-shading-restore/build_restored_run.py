"""Rebind the existing Run motion to the user-selected restored side master."""
from pathlib import Path
import importlib.util
import json
import math
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / 'art/warden'
SOURCE = ART / 'shading-restore/proportion-fix-v1/warden-proportion-restored.png'
RIG = ART / 'sprint-hibit/build_sprint_v3.py'
spec = importlib.util.spec_from_file_location('existing_run', RIG)
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
SCALE = 80 / 938
W, H, S, N = b.W, b.H, b.S, b.N
X, Y = b.X, b.Y


def point(x, y):
    return 64 + (x - 735)*SCALE, 92 + (y - 1126)*SCALE


def prepare():
    im = Image.open(SOURCE).convert('RGBA')
    im = im.resize((round(im.width*SCALE*S), round(im.height*SCALE*S)), Image.Resampling.LANCZOS)
    canvas = Image.new('RGBA', (W*S, H*S))
    canvas.alpha_composite(im, (round(64*S-735*SCALE*S), round(92*S-1126*SCALE*S)))
    return np.array(canvas)


b.SOURCE = SOURCE
b.point = point
b.prepare = prepare
b.PATHS = [
    ('near-ear', 'tip-to-base', [(591,226),(549,285),(661,289),(665,355)], .08),
    ('far-ear', 'tip-to-base', [(715,212),(692,283),(796,278),(788,337)], .5),
    ('forehead', 'back-to-front', [(658,483),(720,422),(816,476),(868,390)], .18),
    ('chin', 'front-to-back', [(772,614),(738,662),(704,646),(649,675)], .62),
    ('torso', 'upper-front-to-lower-back', [(821,888),(813,948),(755,938),(734,984)], .35),
    ('tail', 'root-to-tip', [(564,987),(528,1040),(446,1012),(351,1045)], .7),
]
b.CURVES = [(n,d,*b.samples(points),offset) for n,d,points,offset in b.PATHS]
b.BASE = prepare()
region = Image.new('L', (W*S,H*S))
draw = ImageDraw.Draw(region)
for _,_,xy,_,_ in b.CURVES:
    draw.line([tuple(p*S) for p in xy], fill=255, width=round(3.8*S))
remove = (np.array(region)>0) & (b.BASE[:,:,0]>70) & (b.BASE[:,:,1]>210) & (b.BASE[:,:,3]>128)
donor = (b.BASE[:,:,3]>200) & (b.BASE[:,:,0]<65) & (b.BASE[:,:,1]>65) & ~remove
_, ix = distance_transform_edt(~donor, return_indices=True)
b.BASE[remove,:3] = b.BASE[ix[0][remove],ix[1][remove],:3]

b.CLOTH = b.poly([(210,945),(210,780),(453,760),(520,723),(582,700),(593,735),(557,797),(536,851),(470,879),(350,875),(323,930)])
b.TAIL = b.poly([(240,930),(430,934),(550,941),(607,916),(612,990),(608,1058),(561,1094),(453,1125),(265,1142),(240,1100)])
b.NEAR_ARM = b.poly([(609,847),(682,850),(686,893),(663,937),(637,942),(609,916)])
b.FAR_ARM = b.poly([(819,856),(843,849),(853,899),(839,937),(822,938)])
b.LEG_ROOT = point(0,1044)[1]
SPLIT = point(713,0)[0]
b.NEAR_LEG = (Y>=b.LEG_ROOT-.5) & (X<SPLIT) & ~b.TAIL
b.FAR_LEG = (Y>=b.LEG_ROOT-.5) & (X>=SPLIT) & ~b.TAIL
b.BODY = ~(b.CLOTH|b.TAIL|b.NEAR_ARM|b.FAR_ARM) & (Y<b.LEG_ROOT+.25)

# A small hidden torso underlap prevents a moving arm revealing an artificial cut-out.
UNDERLAP = b.NEAR_ARM & (X>=point(632,0)[0]) & (Y>=point(0,860)[1])
BODY_BASE = b.BASE.copy()
donor = (b.BASE[:,:,3]>200) & ~b.NEAR_ARM & (X>point(684,0)[0]) & (Y>point(0,860)[1])
_, ix = distance_transform_edt(~donor, return_indices=True)
BODY_BASE[UNDERLAP] = b.BASE[ix[0][UNDERLAP],ix[1][UNDERLAP]]
b.BODY |= UNDERLAP
SOLES = {}
for near, mask in [(True,b.NEAR_LEG),(False,b.FAR_LEG)]:
    yy,_ = np.where(mask & (b.BASE[:,:,3]>128))
    SOLES[near] = (yy.max()+1)/S


def current_layer(p):
    im = Image.new('RGBA', (W*S,H*S)); d = ImageDraw.Draw(im)
    for _,_,xy,arc,offset in b.CURVES:
        trail=arc[-1]*.42; head=((p+offset)%1)*(arc[-1]+trail)
        for j in range(1,len(xy)):
            behind=head-arc[j]
            if 0<=behind<=trail:
                value=(1-behind/trail)**.7
                d.line([tuple(xy[j-1]*S),tuple(xy[j]*S)],fill=(int(70+170*value),250,255,255),width=max(1,round(S*(.25+1.05*value))))
        if 0<head<arc[-1]:
            x=np.interp(head,arc,xy[:,0])*S; y=np.interp(head,arc,xy[:,1])*S; radius=.55*S
            d.ellipse((x-radius,y-radius,x+radius,y+radius),fill=(255,255,255,255))
    a=np.array(im)
    a[(b.BASE[:,:,3]<200)|(b.BASE[:,:,:3].max(2)<45)]=0
    return a


def leg(a,p,near,by,bx):
    dx,fy,_=b.foot(p+(0 if near else .5))
    sole=SOLES[near]; cut=sole-2.6; target_cut=fy-2.6
    # Keep the rounded foot rigid; only the short upper connector stretches.
    upper=b.LEG_ROOT+(Y-b.LEG_ROOT-by)*(cut-b.LEG_ROOT)/(target_cut-b.LEG_ROOT-by)
    srcy=np.where(Y>=target_cut,Y-fy+sole,upper)
    weight=np.clip((srcy-b.LEG_ROOT)/(cut-b.LEG_ROOT),0,1)
    srcx=X-(bx*(1-weight)+dx*weight)
    return b.warp(b.layer(a,b.NEAR_LEG if near else b.FAR_LEG),srcx,srcy)


def arm(a,p,near,by,bx):
    phase=p+(0 if near else .5); angle=math.radians(38)*math.sin(2*math.pi*phase)
    cx,cy=point(*( (645,855) if near else (830,862)))
    x=X-bx-cx; y=Y-by-cy
    xx=cx+math.cos(angle)*x+math.sin(angle)*y
    yy=cy-math.sin(angle)*x+math.cos(angle)*y
    return b.warp(b.layer(a,b.NEAR_ARM if near else b.FAR_ARM),xx,yy)


def render(p, current=True, physics=True):
    p%=1; by=b.bob(p); bx=b.sway(p)
    flow=current_layer(p) if current else np.zeros_like(b.BASE)
    im=Image.fromarray(b.BASE); im.alpha_composite(Image.fromarray(flow)); a=np.array(im)
    body=Image.fromarray(BODY_BASE); body.alpha_composite(Image.fromarray(flow))
    out=Image.new('RGBA',(W*S,H*S))
    cloth=b.qfield('cloth',p,(point(582,0)[0]-(X-bx))/(point(582,0)[0]-point(235,0)[0])) if physics else 0
    tail=b.qfield('tail',p,(point(607,0)[0]-(X-bx))/(point(607,0)[0]-point(286,0)[0])) if physics else 0
    out.alpha_composite(b.warp(b.layer(a,b.TAIL),X-bx,Y-by-tail))
    out.alpha_composite(b.warp(b.layer(a,b.CLOTH),X-bx,Y-by-cloth))
    out.alpha_composite(leg(a,p,False,by,bx)); out.alpha_composite(arm(a,p,False,by,bx))
    out.alpha_composite(leg(a,p,True,by,bx))
    earweight=(point(0,420)[1]-(Y-by))/(point(0,420)[1]-point(0,188)[1])
    ear=np.where(X-bx<point(688,0)[0],b.qfield('near-ear',p,earweight),b.qfield('far-ear',p,earweight)) if physics else 0
    out.alpha_composite(b.warp(b.layer(np.array(body),b.BODY),X-bx-ear,Y-by))
    out.alpha_composite(arm(a,p,True,by,bx))
    return b.finish(out)


b.render=render
b.leg=leg
b.arm=arm
b.current_layer=current_layer

if __name__=='__main__':
    out=ART/'shading-restore'/(sys.argv[1] if len(sys.argv)>1 else 'run-review-v1')
    b.publish(out)
    (out/'palette.hex').write_text('\n'.join('#%02x%02x%02x'%tuple(c) for c in b.PAL)+'\n',encoding='utf-8')
    source={'art_source':'existing','source':str(SOURCE.relative_to(ROOT)),'sourceSha256':b.sha(SOURCE),'sourceImageRoute':'host-image_gen','motionSource':'code','newImageOrVideoModelUsed':False,'rig':str(RIG.relative_to(ROOT)),'rigSha256':b.sha(RIG),'builder':str(Path(__file__).relative_to(ROOT)),'builderSha256':b.sha(Path(__file__)),'status':'review-only','registration':{'sourceHeight':938,'bodyHeight':80,'sourceRoot':[735,1126],'anchor':[64,92]},'limitations':['2D spring-mass transverse inertia; no cloth self-collision or physical folds','left direction mirrors lighting','updated foot lower shape moves rigidly; upper attachment is a short deformation']}
    (out/'provenance.json').write_text(json.dumps(source,indent=2),encoding='utf-8')
    (out/'codeart-meta.json').write_text(json.dumps({'art_source':'code','source_art':'user-selected existing restored image','placeholder':False,'disclosure':'existing raster art, code animation; no new image or video generation','specSha256':b.sha(Path(__file__).with_name('spec.md'))},indent=2),encoding='utf-8')
