from pathlib import Path
import importlib.util
import json
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import binary_fill_holes, label

sys.dont_write_bytecode = True
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('new_run',Path(__file__).with_name('build_restored_run.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
b=m.b
OUT=m.ART/'shading-restore/run-review-v1'
OLD=m.ART/'provisional-approved/run-v3'
report={}

protected=0
for ap in (m.ART/'provisional-approved').glob('*/approval.json'):
    a=json.loads(ap.read_text(encoding='utf-8'))
    for rel,digest in a['frameSha256'].items():
        assert b.sha(ap.parent/rel)==digest
        protected+=1
assert protected==128
assert b.sha(m.SOURCE)=='2654e9adab12347a5a554518b9d0aead29e73cb7b963e3468065d5e78c87e4d2'
for name in ('gait.json','physics.json'):
    assert json.loads((OUT/name).read_text())==json.loads((OLD/name).read_text()),name
assert np.array_equal(m.render(0),m.render(1))
palette=set(map(tuple,b.PAL.tolist()))
connection=[];holes=[];feet=[];flow_pixels=[];inertia_pixels=[]
for i in range(b.N):
    p=i/b.N+b.PHASE_OFFSET
    right=np.array(Image.open(OUT/f'run_right/frame_{i:02d}.png').convert('RGBA'))
    left=np.array(Image.open(OUT/f'run_left/frame_{i:02d}.png').convert('RGBA'))
    assert np.array_equal(right[:,::-1],left)
    mask=right[:,:,3]>0
    assert set(np.unique(right[:,:,3]))<={0,255}
    assert set(map(tuple,right[mask,:3]))<=palette
    assert not(mask[:4].any() or mask[-4:].any() or mask[:,:4].any() or mask[:,-4:].any())
    labels,_=label(mask,np.ones((3,3)));sizes=np.bincount(labels.ravel())[1:]
    connection.append(float(sizes.max()/mask.sum()))
    enclosed=binary_fill_holes(mask)&~mask
    holes.append(int(enclosed.sum()))
    assert connection[-1]==1 and holes[-1]==0,(i,connection[-1],holes[-1])
    flow_pixels.append(int(np.any(right!=m.render(p,current=False),axis=2).sum()))
    inertia_pixels.append(int(np.any(right!=m.render(p,physics=False),axis=2).sum()))
    for near in (True,False):
        raw=np.array(m.leg(b.BASE,p,near,b.bob(p),b.sway(p)))[:,:,3]>127
        yy,xx=np.where(raw);dx,fy,stance=b.foot(p+(0 if near else .5))
        bottom=(yy.max()+1)/b.S
        lower=raw & (b.Y>=fy-2.6)
        ly,lx=np.where(lower)
        width=(lx.max()+1-lx.min())/b.S
        feet.append({'frame':i,'near':near,'stance':stance,'targetY':fy,'actualBottom':bottom,'lowerWidth':width})
        assert abs(bottom-fy)<=.5,(i,near,bottom,fy)
assert min(flow_pixels)>0 and min(inertia_pixels)>0
for near in (True,False):
    widths=[f['lowerWidth'] for f in feet if f['near']==near]
    assert max(widths)-min(widths)<=1.0,(near,widths)

directions=[]
for name,direction,xy,arc,offset in b.CURVES:
    positions=[]
    for fraction in (.2,.8):
        phase=(fraction/1.42-offset)%1
        a=m.current_layer(phase)
        yy,xx=np.where((a[:,:,0]>=245)&(a[:,:,3]>0))
        points=np.column_stack((xx,yy))/b.S
        distances=((points[:,None,:]-xy[None,:,:])**2).sum(2)
        nearest=distances.argmin(1);inside=distances.min(1)<1.5**2
        assert inside.any(),name
        positions.append(float(np.median(arc[nearest[inside]])/arc[-1]))
    assert positions[1]-positions[0]>.35,(name,positions)
    directions.append({'path':name,'direction':direction,'observedBrightHeadArcFractions':positions})

physics={}
for name,a in b.PHYS.items():
    physics[name]={'rootMaxAbs':float(abs(a[:,0]).max()),'tipPeakToPeak':float(np.ptp(a[:,-1])),'seamMaxError':float(abs(a[-1]-a[0]).max()),'middleTipMaxDifference':float(abs(a[:,len(a[0])//2]-a[:,-1]).max())}
    assert physics[name]['rootMaxAbs']==0 and physics[name]['tipPeakToPeak']>.05
    assert physics[name]['seamMaxError']<.001
assert physics['cloth']['tipPeakToPeak']>5
for direction in ('right','left'):
    folder=OUT/f'run_{direction}'
    manifest=json.loads((folder/'animation.json').read_text())
    assert sum(manifest['durationsMs'])==480 and len(manifest['frames'])==16
    gif=Image.open(folder/'preview.gif');dur=0
    assert gif.n_frames==16
    for i in range(16):gif.seek(i);dur+=gif.info['duration']
    assert dur==480
    sheet=np.array(Image.open(folder/'sheet.png').convert('RGBA'))
    for i in range(16):
        frame=np.array(Image.open(folder/f'frame_{i:02d}.png').convert('RGBA'))
        assert np.array_equal(frame,sheet[(i//8)*b.H:(i//8+1)*b.H,(i%8)*b.W:(i%8+1)*b.W])
report={'protectedPngs':protected,'selectedSourceUnchanged':True,'gaitAndPhysicsEqualToApprovedRun':True,'exactPeriodic':True,'allFramesConnected':min(connection),'enclosedHolesPerFrame':holes,'footSamples':feet,'currentChangedPixelsPerFrame':flow_pixels,'physicsChangedPixelsPerFrame':inertia_pixels,'currentDirections':directions,'physics':physics,'gifFrames':16,'gifMs':480,'sheetsEqualFrames':True}
(OUT/'revision-qa.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ('footSamples','enclosedHolesPerFrame')},indent=2))
