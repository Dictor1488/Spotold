#!/usr/bin/env python3
"""Deterministic INQ SPOT .wotmod builder (WoT Python 2.7)."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parent
SOURCES = (
    "mod_inq_spot.py",
    "mod_inq_spot_panelmode.py",
    "mod_inq_spot_visibility.py",
)
RESOURCES = (
    "gui/gameface/mods/spotted/SpottedPanel.html",
    "gui/gameface/mods/spotted/SpottedPanel.css",
    "gui/gameface/mods/spotted/SpottedPanel.js",
    "gui/gen_resources/tv.dictor.spot.json",
    "mods/configs/me_inq_spotted/config.json",
)

def write_entry(archive, name, content):
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_STORED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, content)

def build(python27):
    config = json.loads((ROOT / "build.json").read_text(encoding="utf-8-sig"))
    resources = list(RESOURCES)
    resources.extend("gui/spottedstatus/styles/%s/%s.png" % (style, name)
                     for style in (0, 1)
                     for name in ("colorblind", "detected", "missing", "undetected"))
    expected_src = [ROOT / "src" / name for name in SOURCES]
    expected_res = [ROOT / "res" / name for name in RESOURCES]
    icons = [ROOT / name for name in resources[len(RESOURCES):]]
    missing = [str(path.relative_to(ROOT))
               for path in expected_src + expected_res + icons if not path.is_file()]
    if missing:
        raise RuntimeError("Missing inputs: %s" % ", ".join(missing))
    output = ROOT / "dist"
    output.mkdir(exist_ok=True)
    artifact = output / ("INQ_SPOT_%s.wotmod" % config["version"])
    with tempfile.TemporaryDirectory() as temp:
        compiled = []
        for src in expected_src:
            pyc = Path(temp) / (src.stem + ".pyc")
            subprocess.run([python27, "-c",
                'import py_compile,sys;py_compile.compile(sys.argv[1],cfile=sys.argv[2],dfile=sys.argv[1].split("/")[-1],doraise=True)',
                str(src), str(pyc)], check=True)
            if pyc.read_bytes()[:4] != bytes.fromhex("03f30d0a"):
                raise RuntimeError("Python 2.7 required: %s" % src)
            compiled.append((src, pyc))
        meta = ET.Element("root")
        for key in ("id", "version", "name", "description"):
            ET.SubElement(meta, key).text = config[key]
        with zipfile.ZipFile(artifact, "w", compression=zipfile.ZIP_STORED, allowZip64=False) as z:
            write_entry(z, "meta.xml", ET.tostring(meta, encoding="utf-8", xml_declaration=True))
            for src, pyc in compiled:
                write_entry(z, "res/scripts/client/gui/mods/%s.pyc" % src.stem, pyc.read_bytes())
            for name, path in zip(resources, expected_res + icons):
                write_entry(z, "res/" + name, path.read_bytes())
        with zipfile.ZipFile(artifact) as z:
            files = z.namelist()
            if z.testzip() is not None:
                raise RuntimeError("Corrupted ZIP")
            if files[0] != "meta.xml":
                raise RuntimeError("meta.xml must be the first entry")
            if len(files) != len(set(files)):
                raise RuntimeError("Duplicate archive entries")
            if any(item.compress_type != zipfile.ZIP_STORED for item in z.infolist()):
                raise RuntimeError("Archive compression is not supported by WoT")
            if any(path != "meta.xml" and not path.startswith("res/") for path in files):
                raise RuntimeError("Invalid .wotmod internal paths: %r" % files)
            if any(path.endswith((".swf", ".py")) for path in files):
                raise RuntimeError("No SWF or Python source files allowed")
            if len(files) != 1 + len(SOURCES) + len(resources):
                raise RuntimeError("Unexpected entry count")
        print(artifact)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--python27", required=True)
    build(parser.parse_args().python27)
