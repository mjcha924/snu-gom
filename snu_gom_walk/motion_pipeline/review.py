"""Offline, dependency-free 3D collider review with angle/torque plots."""
import json


def render(path,clips,manifest):
    template='''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>SNU GOM 모션 검토</title>
<style>*{box-sizing:border-box}body{margin:0;background:#f3f6f5;color:#203a40;font:14px/1.6 system-ui,"Malgun Gothic",sans-serif}main{max-width:1400px;margin:auto;padding:28px}h1{font-size:25px;margin:0}p{color:#5d7378}.toolbar,.panel{background:white;border:1px solid #d1e0dd;border-radius:12px;padding:18px;margin:18px 0}.row{display:flex;gap:18px}.panel{flex:1;min-width:0}.view{width:100%;height:420px;background:#edf3f1;border-radius:8px;touch-action:none}.graph{height:160px;width:100%;background:#f7faf9}select,button{font:inherit;padding:8px 12px;border:1px solid #bfd0cb;border-radius:7px;background:white}input{width:55%;vertical-align:middle}.bad{color:#ac442e}.good{color:#087d74}#status{white-space:pre-wrap}code{font-size:12px}footer{font-size:12px;color:#647b80}@media(max-width:800px){.row{display:block}.view{height:350px}}</style>
<main><h1>SNU GOM · 모션 생성과 물리 검사</h1><p>형상·질량·제한이 연결된 후보입니다. 3D는 실제 검사용 충돌체를 표시합니다. 드래그로 시점을 돌릴 수 있습니다.</p>
<div class="toolbar"><select id="clips" aria-label="모션 선택"></select> <button id="play">일시정지</button> <input id="seek" aria-label="재생 구간" type="range" min="0" max="1" step=".001" value="0"> <span id="time"></span><p id="status"></p></div>
<div class="row"><div class="panel"><b>제작한 기준 모션 · 기구학</b><canvas id="target" class="view"></canvas></div><div class="panel"><b>자유 몸통 물리 시뮬레이션 · 관절 토크만 적용</b><canvas id="actual" class="view"></canvas></div></div>
<div class="toolbar"><select id="joint" aria-label="관절 선택"></select><div class="row"><div class="panel">기준 관절 각도 (°)<canvas id="angle" class="graph"></canvas></div><div class="panel">실제 적용 토크 (N·m)<canvas id="torque" class="graph"></canvas></div></div></div>
<details class="toolbar"><summary>선택한 후보의 검사 보고서</summary><pre id="report" style="white-space:pre-wrap;overflow-wrap:anywhere"></pre></details>
<footer>레퍼런스 사용 기준은 전 프레임 기구학과 별도의 모터 검사입니다. 물리 추종 실패는 학습 입력을 자동 차단하지 않습니다. 토크 검사는 발바닥 외곽을 사용하는 낙관적 검사이며, 균형 미해결 구간은 조건부로 표시합니다. GPU 학습·실물 검증 결과가 아닙니다. 모델 지문 <code id="hash"></code></footer></main>
<script>const DATA=__DATA__;const $=id=>document.getElementById(id);let selected=0,joint=0,playing=true,clock=0,last=performance.now(),az=-.7,el=.32;const edges=[[0,1],[0,2],[0,4],[1,3],[1,5],[2,3],[2,6],[3,7],[4,5],[4,6],[5,7],[6,7]];const signs=[];for(let x of [-1,1])for(let y of [-1,1])for(let z of [-1,1])signs.push([x,y,z]);
function option(el,value,label){const o=document.createElement('option');o.value=value;o.textContent=label;el.append(o)}
DATA.clips.forEach((r,i)=>option($('clips'),i,`${r.entry.kind} · ${r.entry.split} · ${r.entry.id} · ${r.kinematic.passed?'기구학 통과':'제외'}`));$('hash').textContent=DATA.model_id;
function resize(canvas){const ratio=Math.min(devicePixelRatio,2);canvas.width=canvas.clientWidth*ratio;canvas.height=canvas.clientHeight*ratio;let c=canvas.getContext('2d');c.setTransform(ratio,0,0,ratio,0,0);return [c,canvas.clientWidth,canvas.clientHeight]}
function draw(canvas,boxes,root,message){
  let [c,w,h]=resize(canvas);c.clearRect(0,0,w,h);c.fillStyle='#5e7678';
  if(!boxes?.length){c.fillText(message||'초기 정착 중 종료되어 재생 표본이 없습니다.',20,45);return}
  const cx=root?.[0]||0,cy=root?.[1]||0;
  function view(p){const x=p[0]-cx,y=p[1]-cy;const a=Math.cos(az)*x-Math.sin(az)*y,b=Math.sin(az)*x+Math.cos(az)*y;return [a,Math.cos(el)*p[2]-Math.sin(el)*b,b]}
  const world=boxes.map(box=>signs.map(v=>{const s=v.map((x,i)=>x*box[12+i]);return [0,1,2].map(i=>box[i]+box[3+i*3]*s[0]+box[4+i*3]*s[1]+box[5+i*3]*s[2])}));
  const points=world.flat().map(view),xs=points.map(p=>p[0]),ys=points.map(p=>p[1]);
  const left=Math.min(...xs),right=Math.max(...xs),bottom=Math.min(...ys),top=Math.max(...ys);
  const scale=Math.min((w-50)/Math.max(right-left,.15),(h-36)/Math.max(top-bottom,.2),1100);
  function project(p){const v=view(p);return [w/2+(v[0]-(left+right)/2)*scale,h/2-(v[1]-(top+bottom)/2)*scale,v[2]]}
  c.lineWidth=.7;c.strokeStyle='#ccdcd7';
  for(let i=-10;i<=10;i++){const s=i*.04;for(let axis=0;axis<2;axis++){const a=project(axis?[cx-.4,cy+s,0]:[cx+s,cy-.4,0]),b=project(axis?[cx+.4,cy+s,0]:[cx+s,cy+.4,0]);c.beginPath();c.moveTo(...a.slice(0,2));c.lineTo(...b.slice(0,2));c.stroke()}}
  const polys=world.map(box=>{const p=box.map(project);return {p,depth:p.reduce((s,v)=>s+v[2],0)}}).sort((a,b)=>a.depth-b.depth);
  for(let {p} of polys){c.fillStyle='rgba(69,129,139,.25)';c.beginPath();[0,1,3,2].forEach((i,k)=>k?c.lineTo(...p[i].slice(0,2)):c.moveTo(...p[i].slice(0,2)));c.closePath();c.fill();c.strokeStyle='#285b68';c.lineWidth=1;for(let [a,b] of edges){c.beginPath();c.moveTo(...p[a].slice(0,2));c.lineTo(...p[b].slice(0,2));c.stroke()}}
}
function plot(canvas,values){let [c,w,h]=resize(canvas);c.clearRect(0,0,w,h);if(!values.length){c.fillText('물리 실행 표본 없음',18,40);return}let lo=Math.min(...values),hi=Math.max(...values),pad=Math.max((hi-lo)*.1,.001);lo-=pad;hi+=pad;c.font='11px sans-serif';c.fillStyle='#547074';c.fillText(hi.toFixed(3),3,16);c.fillText(lo.toFixed(3),3,h-10);c.strokeStyle='#078b85';c.beginPath();values.forEach((v,i)=>{let x=48+(w-60)*i/Math.max(values.length-1,1),y=h-18-(h-35)*(v-lo)/(hi-lo);i?c.lineTo(x,y):c.moveTo(x,y)});c.stroke()}
function choose(){let r=DATA.clips[selected];clock=0;$('joint').replaceChildren();r.preview.joint_names.forEach((n,i)=>option($('joint'),i,n));joint=0;let k=r.kinematic.passed,p=r.physics,s=r.screen,eligible=r.entry.reference_eligible;$('status').className=eligible?'good':'bad';$('status').textContent=`학습 레퍼런스: ${eligible?(s?.balance_unresolved_frames?.length?'조건부 사용 가능':'사용 가능'):'제외'} · 기구학: ${k?'통과':'제외'} · 물리 추종: ${p?(p.passed?'시험 통과':'미통과'):'실행 안 함'}\n`+(s?`필요 토크/임시 상한 최대 ${((s.peak_minimum_torque_utilization||0)*100).toFixed(1)}% · 접촉 균형 미해결 ${s.balance_unresolved_frames.length}/${s.frames_checked}프레임\n`:'')+(p?`하중 접촉 일치 ${(100*p.contact_schedule_agreement).toFixed(1)}% · 번갈아 착지 ${p.alternating_touchdowns}회 · 종료 원인 ${p.failure?.reason||'시험 종료'}`:'기구학 검사를 먼저 통과해야 물리 검사를 실행합니다.');$('report').textContent=JSON.stringify({kinematic:r.kinematic,reference_screen:s,physics:r.physics},null,2);charts()}
function charts(){let r=DATA.clips[selected];plot($('angle'),r.preview.joints.map(v=>v[joint]*180/Math.PI));plot($('torque'),r.trace.map(v=>v.torque_nm[joint]))}
$('clips').onchange=()=>{selected=Number($('clips').value);choose()};$('joint').onchange=()=>{joint=Number($('joint').value);charts()};$('play').onclick=()=>{playing=!playing;$('play').textContent=playing?'일시정지':'재생'};$('seek').oninput=()=>{clock=Number($('seek').value)*DATA.clips[selected].preview.time.at(-1)};
for(let id of ['target','actual']){let x,y;$(id).onpointerdown=e=>{x=e.clientX;y=e.clientY;$(id).setPointerCapture(e.pointerId)};$(id).onpointermove=e=>{if(!$(id).hasPointerCapture(e.pointerId))return;az+=(e.clientX-x)*.01;el=Math.max(.05,Math.min(1.3,el+(e.clientY-y)*.01));x=e.clientX;y=e.clientY};$(id).onpointerup=e=>$(id).releasePointerCapture(e.pointerId)}
function tick(now){let r=DATA.clips[selected],duration=r.preview.time.at(-1);if(playing)clock=(clock+Math.min(Math.max((now-last)/1000,0),.05))%duration;last=now;let index=Math.min(r.preview.time.length-1,Math.floor(clock/duration*(r.preview.time.length-1)));let actual=r.trace.findLast(v=>v.time_s<=clock)||r.trace[0];draw($('target'),r.preview.boxes[index],r.preview.root[index]);draw($('actual'),actual?.boxes,actual?.root_pos);$('seek').value=clock/duration;$('time').textContent=clock.toFixed(2)+' / '+duration.toFixed(2)+'초';requestAnimationFrame(tick)}
choose();requestAnimationFrame(tick);addEventListener('resize',charts);</script></html>'''
    payload=json.dumps(dict(model_id=manifest['model_id'],clips=clips),ensure_ascii=False,allow_nan=False).replace('<','\\u003c')
    path.write_text(template.replace('__DATA__',payload),encoding='utf-8')
