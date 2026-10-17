(function(){
'use strict';
var root=document.getElementById('spotted-root');
var last=null,ready=false;
var ICONS={neverSpotted:'missing',spotted:'detected',notSpotted:'undetected',killed:''};
function raw(){try{return window.model&&window.model.payload?String(window.model.payload):''}catch(e){return''}}
function render(){
  var r=raw();
  if(!r||r===last)return;
  last=r;
  var p;
  try{p=JSON.parse(r)}catch(e){return}
  root.classList.toggle('hidden',!p.visible);
  root.innerHTML='';
  var rows=p.rows||[];
  for(var i=0;i<rows.length;i++){
    var row=document.createElement('div');
    row.className='row';
    var image=document.createElement('img');
    image.className='lamp';
    var state=rows[i]||'neverSpotted';
    var icon=ICONS[state]||'';
    if(state==='notSpotted'&&p.colorblind)icon='colorblind';
    if(!icon){image.style.visibility='hidden';}else{
      image.src='coui://gui/spottedstatus/styles/'+(Number(p.style)===0?0:1)+'/'+icon+'.png';
    }
    row.appendChild(image);
    root.appendChild(row);
  }
}
function init(){
  if(ready)return;
  ready=true;
  try{if(window.viewEnv&&viewEnv.resizeViewPx)viewEnv.resizeViewPx(20,380)}catch(e){}
  if(window.engine){
    engine.on('viewEnv.onDataChanged',render);
    engine.on('self.onScaleUpdated',render);
    engine.on('clientResized',render);
  }
  try{if(window.viewEnv&&viewEnv.addDataChangedCallback)viewEnv.addDataChangedCallback('model',0,true)}catch(e){}
  render();
  try{if(window.model&&typeof window.model.onReady==='function')window.model.onReady({})}catch(e){}
}
if(window.engine&&window.engine.whenReady){
  var domReady=window.isDomBuilt?Promise.resolve():new Promise(function(resolve){engine.on('self.onDomBuilt',resolve)});
  Promise.all([window.engine.whenReady,domReady]).then(function(){requestAnimationFrame(init)});
}else{
  requestAnimationFrame(init);
}
}());
