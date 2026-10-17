#!/usr/bin/env python3
"""INQ SPOT 2.4.1 Gameface package builder. Never packs SWF."""
import argparse
import json
import pathlib
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent

def build(python27):
    cfg=json.loads((ROOT/'build.json').read_text(encoding='utf-8'))
    output=ROOT/'dist'
    output.mkdir(exist_ok=True)
    icons=sorted((ROOT/'gui/spottedstatus/styles').glob('*/*.png'))
    if len(icons)!=8:
        raise RuntimeError('Expected eight PNG icons in gui/spottedstatus/styles/')
    assets=sorted((ROOT/'resources/gui/gameface/mods/inq_spot').glob('*'))
    if len(assets)<3:
        raise RuntimeError('Missing HTML/CSS/JS Gameface assets')
    source=[ROOT/'src/mod_inq_spot.py',ROOT/'src/inq_spot_gameface.py']
    with tempfile.TemporaryDirectory() as tmp:
        compiled=[]
        for src in source:
            target=pathlib.Path(tmp)/(src.stem+'.pyc')
            subprocess.run([python27,'-c',
              'import py_compile,sys;py_compile.compile(sys.argv[1],cfile=sys.argv[2],dfile=sys.argv[1].split("/")[-1],doraise=True)',
              str(src),str(target)],check=True)
            if target.read_bytes()[:4]!=bytes.fromhex('03f30d0a'):
                raise RuntimeError('Python 2.7 interpreter is required')
            compiled.append((src,target))
        root=ET.Element('root')
        for key in ('id','version','name','description'):
            ET.SubElement(root,key).text=cfg[key]
        target=output/('INQ_SPOT_'+cfg['version']+'.wotmod')
        with zipfile.ZipFile(target,'w',zipfile.ZIP_STORED) as z:
            z.writestr('meta.xml',ET.tostring(root,encoding='utf-8',xml_declaration=True))
            for src,pyc in compiled:
                z.write(pyc,'res/scripts/client/gui/mods/'+src.stem+'.pyc')
            for icon in icons:
                z.write(icon,'res/'+icon.relative_to(ROOT).as_posix())
            for asset in assets:
                if asset.is_file():
                    z.write(asset,'res/'+asset.relative_to(ROOT/'resources').as_posix())
            for item in (ROOT/'resources/gui/gen_resources').glob('*.json'):
                z.write(item,'res/'+item.relative_to(ROOT/'resources').as_posix())
        with zipfile.ZipFile(target) as z:
            if z.testzip() is not None: raise RuntimeError('Bad WOTMOD archive')
            assert not any(n.endswith('.swf') for n in z.namelist())
            assert all(item.compress_type == zipfile.ZIP_STORED for item in z.infolist()), 'WoT requires stored entries'
            assert z.namelist()[0] == 'meta.xml', 'meta.xml must be first entry'
            unexpected = [item.filename for item in z.infolist() if item.filename != 'meta.xml' and not item.filename.startswith('res/')]
            if unexpected:
                raise RuntimeError('Unexpected package paths: %s' % unexpected)
        print(target)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--python27',required=True)
    build(parser.parse_args().python27)
