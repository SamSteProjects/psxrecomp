import assert from 'node:assert/strict';
import {nativeChannelSeries,channelGraphWindow,channelGraphFrame} from '../editor/animation-channel-graph.js';
const frames=Array.from({length:40},(_,i)=>({frame_index:i,object_transforms:[{object_index:0,translation:[i-20,0,2047],rotation_psx:[(i*16)%4096,4080,0]},{object_index:1,translation:[-2048,i,0],rotation_psx:[0,16,32]}]}));
const before=structuredClone(frames),v=nativeChannelSeries(frames,1,'translation');assert.deepEqual(v[23],[-2048,23,0]);v[0][0]=0;assert.deepEqual(frames,before);
const r=nativeChannelSeries(frames,0,'rotation_psx');assert.deepEqual(r[39],[624,4080,0]);const w=channelGraphWindow(r,32,16);assert.equal(w.end,39);assert.equal(w.min,0);assert.equal(w.max,4080);w.rows[0][0]=999;assert.equal(r[32][0],512);
assert.equal(channelGraphFrame(64,0,640,32,39),32);assert.equal(channelGraphFrame(620,0,640,32,39),39);assert.equal(channelGraphFrame(342,0,640,32,39),36);assert.equal(channelGraphFrame(-50,0,640,32,39),32);assert.equal(channelGraphFrame(900,0,640,32,39),39);assert.equal(channelGraphFrame(123,50,400,0,0),0);
for(const bad of [[],frames.slice().reverse(),[{frame_index:0,object_transforms:[{object_index:1,translation:[0,0,0]}]}]])assert.throws(()=>nativeChannelSeries(bad,0,'translation'));
const changedLayout=structuredClone(frames);changedLayout[1].object_transforms.pop();assert.throws(()=>nativeChannelSeries(changedLayout,0,'translation'));
for(const [kind,value] of [['translation',-2049],['translation',2048],['translation',true],['rotation_psx',15],['rotation_psx',4096],['rotation_psx',NaN]]){const f=structuredClone(frames);f[0].object_transforms[0][kind][0]=value;assert.throws(()=>nativeChannelSeries(f,0,kind));}
for(const args of [[frames,2,'translation'],[frames,0,'scale'],[frames,-1,'translation'],[Array(4097).fill(frames[0]),0,'translation']])assert.throws(()=>nativeChannelSeries(...args));
for(const args of [[r,40,16],[r,0,17],[[],0,16],[r,-1,16]])assert.throws(()=>channelGraphWindow(...args));assert.throws(()=>channelGraphFrame(10,0,0,0,1));
console.log('Native channel series, exact grid, immutable windows and frame picking passed');
