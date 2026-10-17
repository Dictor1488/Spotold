#!/usr/bin/env python3
"""Build a WoT 2.4.1 .wotmod using a real Python 2.7 interpreter."""
import argparse
import json
import pathlib
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent

def build(python27):
    config = json.loads((ROOT / 'build.json').read_text(encoding='utf-8'))
    source = ROOT / 'src/mod_inq_spot.py'
    resources = ROOT
    icons = sorted((ROOT / 'gui/spottedstatus/styles').glob('*/*.png'))
    flash = ROOT / 'assets/flash/playersPanelAPI_modsCore.swf'
    if len(icons) != 8 or not flash.is_file():
        raise RuntimeError('Missing eight PNG icons or panel SWF in assets/.')
    output = ROOT / 'dist'
    output.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as temp:
        target = pathlib.Path(temp) / 'mod_inq_spot.pyc'
        subprocess.run([python27, '-c',
          'import py_compile,sys;py_compile.compile(sys.argv[1],cfile=sys.argv[2],dfile="mod_inq_spot.py",doraise=True)',
          str(source),str(target)],check=True)
        if target.read_bytes()[:4] != bytes.fromhex('03f30d0a'):
            raise RuntimeError('Python 2.7 required (wrong pyc magic)')
        xml = ET.Element('root')
        for key in ('id','version','name','description'):
            ET.SubElement(xml,key).text = config[key]
        archive = output / ('INQ_SPOT_' + config['version'] + '.wotmod')
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('meta.xml', ET.tostring(xml,encoding='utf-8'))
            z.write(target,'res/scripts/client/gui/mods/mod_inq_spot.pyc')
            z.write(flash,'res/gui/flash/playersPanelAPI_modsCore.swf')
            for icon in icons:
                z.write(icon,'res/'+icon.relative_to(resources).as_posix())
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
        print(archive)

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--python27',required=True)
    build(parser.parse_args().python27)
