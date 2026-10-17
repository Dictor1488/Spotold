#!/usr/bin/env python3
"""Build INQ SPOT AS3 (Scaleform) WOTMOD. Requires compiled SWF + Python 2.7."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parent
SOURCES = ("mod_inq_spot.py", "inq_spot_as3.py")
SWF = ROOT / "as3/bin/inqSpotPanel.swf"

def write(archive, name, data):
    info=zipfile.ZipInfo(name, date_time=(1980,1,1,0,0,0))
    info.compress_type=zipfile.ZIP_STORED
    info.external_attr=0o100644 << 16
    archive.writestr(info,data)

def build(python27):
    cfg=json.loads((ROOT/"build.json").read_text(encoding="utf-8-sig"))
    if not SWF.is_file() or SWF.stat().st_size < 512:
        raise RuntimeError("Missing compiled as3/bin/inqSpotPanel.swf")
    icons=sorted((ROOT/"gui/spottedstatus/styles").glob("*/*.png"))
    if len(icons)!=8:
        raise RuntimeError("Expected eight PNG icons")
    output=ROOT/"dist"
    output.mkdir(exist_ok=True)
    path=output/("INQ_SPOT_%s.wotmod" % cfg["version"])
    with tempfile.TemporaryDirectory() as tmp:
        compiled=[]
        for name in SOURCES:
            source=ROOT/"src"/name
            target=Path(tmp)/(source.stem+".pyc")
            subprocess.run([python27,"-c",
                'import py_compile,sys;py_compile.compile(sys.argv[1],cfile=sys.argv[2],dfile=sys.argv[1].split("/")[-1],doraise=True)',
                str(source),str(target)],check=True)
            if target.read_bytes()[:4]!=bytes.fromhex("03f30d0a"):
                raise RuntimeError("Expected Python 2.7 bytecode")
            compiled.append((source,target))
        root=ET.Element("root")
        for key in ("id","version","name","description"):
            ET.SubElement(root,key).text=cfg[key]
        with zipfile.ZipFile(path,"w",compression=zipfile.ZIP_STORED,allowZip64=False) as z:
            write(z,"meta.xml",ET.tostring(root,encoding="utf-8",xml_declaration=True))
            for source,pyc in compiled:
                write(z,"res/scripts/client/gui/mods/"+source.stem+".pyc",pyc.read_bytes())
            write(z,"res/gui/flash/inqSpotPanel.swf",SWF.read_bytes())
            for icon in icons:
                write(z,"res/"+icon.relative_to(ROOT).as_posix(),icon.read_bytes())
        with zipfile.ZipFile(path) as z:
            if z.testzip() is not None: raise RuntimeError("Corrupt .wotmod")
            names=z.namelist()
            if len(names)!=len(set(names)):raise RuntimeError("Duplicate entries")
            if names[0]!="meta.xml":raise RuntimeError("Missing meta.xml first")
            if any(x.compress_type!=zipfile.ZIP_STORED for x in z.infolist()):
                raise RuntimeError("Unsupported compression")
            if len(names)!=12:raise RuntimeError("Unexpected entry count: %s" % names)
        print(path)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--python27",required=True)
    build(parser.parse_args().python27)
