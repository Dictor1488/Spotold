import { ModelObserver } from "../libs/model.js";
const observer = ModelObserver();
const root = document.createElement('div');
root.id = 'inq-spot-layer';
root.style.cssText = 'position:fixed;inset:0;pointer-events:none;z-index:1';
document.body.appendChild(root);
const nodes = new Map();
function render(model) {
    if (!model) return;
    let data;
    try { data = JSON.parse(String(model.payload || '{}')); } catch (_) { return; }
    const vehicles = data.vehicles || {};
    const active = new Set(Object.keys(vehicles));
    for (const [id,node] of nodes) if (!active.has(id)) {node.remove();nodes.delete(id)}
    for (const [id,vehicle] of Object.entries(vehicles)) {
        let img = nodes.get(id);
        if (!img) { img=document.createElement('img');img.className='inq-spot-icon';root.appendChild(img);nodes.set(id,img); }
        const name = vehicle.state===1?'missing':vehicle.state===2?'detected':
                     vehicle.state===3?(vehicle.colorblind?'colorblind':'undetected'):'';
        img.style.display = name ? 'block':'none';
        if (name) img.src = 'coui://gui/spottedstatus/styles/'+vehicle.style+'/'+name+'.png';
        // Mapping vehicle IDs to player-panel row coordinates requires the
        // actual Gameface player-panel DOM/ViewModel. Do not invent coordinates.
    }
}
observer.subscribe(render);
