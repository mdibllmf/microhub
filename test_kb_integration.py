#!/usr/bin/env python3
"""
Integration tests for Microscope Knowledge Base v2.

Runs 10 test cases through the equipment and software agents
to verify KB-powered extraction and inference.
"""

import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline.agents.equipment_agent import EquipmentAgent
from pipeline.agents.software_agent import SoftwareAgent
from pipeline.kb_loader import (
    load_kb, resolve_alias, infer_brand_from_model,
    infer_techniques_from_system, infer_software_from_brand,
    infer_brand_from_software, get_system_category,
)


def _extract(agent, text, section="methods"):
    """Run agent and return dict of {label: [canonical, ...]}."""
    exts = agent.analyze(text, section)
    result = {}
    for ext in exts:
        result.setdefault(ext.label, []).append(ext.canonical())
    return result


def _has(result, label, value):
    """Check if result contains value (case-insensitive) under label."""
    values = result.get(label, [])
    return any(v.lower() == value.lower() for v in values)


def _has_any(result, label, values):
    """Check if any of the values appear under label."""
    return any(_has(result, label, v) for v in values)


def run_tests():
    equip = EquipmentAgent()
    software = SoftwareAgent()

    passed = 0
    failed = 0
    total = 10

    # -------- Test 1: Zeiss LSM 880 with Airyscan --------
    text = "Images were acquired on a Zeiss LSM 880 with Airyscan detector."
    result = _extract(equip, text)
    ok = (
        _has(result, "MICROSCOPE_BRAND", "Zeiss") and
        _has_any(result, "MICROSCOPE_MODEL", ["LSM 880", "Zeiss LSM 880"]) and
        _has_any(result, "DETECTOR", ["Airyscan", "Zeiss Airyscan"])
    )
    if ok:
        passed += 1
        print("PASS  1: Zeiss LSM 880 with Airyscan")
    else:
        failed += 1
        print(f"FAIL  1: Zeiss LSM 880 with Airyscan")
        print(f"         Got: {result}")

    # -------- Test 2: STELLARIS 8 FALCON --------
    text = "We used a Leica STELLARIS 8 FALCON for FLIM experiments."
    result = _extract(equip, text)
    ok = (
        _has(result, "MICROSCOPE_BRAND", "Leica") and
        _has_any(result, "MICROSCOPE_MODEL", [
            "STELLARIS 8 FALCON", "Stellaris", "STELLARIS 8",
            "Leica Stellaris",
        ])
    )
    if ok:
        passed += 1
        print("PASS  2: STELLARIS 8 FALCON")
    else:
        failed += 1
        print(f"FAIL  2: STELLARIS 8 FALCON")
        print(f"         Got: {result}")

    # -------- Test 3: Nikon AX R with NSPARC --------
    text = "Confocal imaging was performed on a Nikon AX R with NSPARC detector."
    result = _extract(equip, text)
    ok = (
        _has(result, "MICROSCOPE_BRAND", "Nikon") and
        _has_any(result, "MICROSCOPE_MODEL", ["AX R", "AX", "Nikon AX", "Nikon AX R"])
    )
    if ok:
        passed += 1
        print("PASS  3: Nikon AX R with NSPARC")
    else:
        failed += 1
        print(f"FAIL  3: Nikon AX R with NSPARC")
        print(f"         Got: {result}")

    # -------- Test 4: FV4000 --------
    text = "Fluorescence images were captured using an FV4000 confocal microscope."
    result = _extract(equip, text)
    ok = (
        _has_any(result, "MICROSCOPE_BRAND", ["Evident (Olympus)", "Olympus"]) and
        _has_any(result, "MICROSCOPE_MODEL", [
            "FV4000", "Olympus FV4000", "Evident FV4000",
            "Evident (Olympus) FV4000",
        ])
    )
    if ok:
        passed += 1
        print("PASS  4: FV4000 → Evident/Olympus")
    else:
        failed += 1
        print(f"FAIL  4: FV4000 → Evident/Olympus")
        print(f"         Got: {result}")

    # -------- Test 5: Dragonfly 600 --------
    text = "We used an Andor Dragonfly 600 spinning disk confocal."
    result = _extract(equip, text)
    ok = (
        _has(result, "MICROSCOPE_BRAND", "Andor") and
        _has_any(result, "MICROSCOPE_MODEL", ["Dragonfly 600", "Andor Dragonfly 600"])
    )
    if ok:
        passed += 1
        print("PASS  5: Dragonfly 600 → Andor")
    else:
        failed += 1
        print(f"FAIL  5: Dragonfly 600 → Andor")
        print(f"         Got: {result}")

    # -------- Test 6: Titan Krios G4 --------
    text = "Cryo-EM data were collected on a Titan Krios G4 equipped with a Falcon 4i detector."
    result = _extract(equip, text)
    ok = (
        _has_any(result, "MICROSCOPE_BRAND", ["Thermo Fisher", "FEI"]) and
        _has_any(result, "MICROSCOPE_MODEL", [
            "Titan Krios", "Titan", "Krios G4",
            "FEI Titan", "Thermo Fisher Titan Krios",
        ])
    )
    if ok:
        passed += 1
        print("PASS  6: Titan Krios G4 → Thermo Fisher/FEI")
    else:
        failed += 1
        print(f"FAIL  6: Titan Krios G4 → Thermo Fisher/FEI")
        print(f"         Got: {result}")

    # -------- Test 7: ORCA-Quest 2 --------
    text = "Images were acquired with a Hamamatsu ORCA-Quest 2 sCMOS camera."
    result = _extract(equip, text)
    ok = (
        _has(result, "MICROSCOPE_BRAND", "Hamamatsu") and
        _has_any(result, "DETECTOR", [
            "ORCA-Quest 2", "Hamamatsu ORCA-Quest 2",
            "ORCA Quest 2", "Hamamatsu ORCA Quest 2",
        ])
    )
    if ok:
        passed += 1
        print("PASS  7: ORCA-Quest 2 → Hamamatsu")
    else:
        failed += 1
        print(f"FAIL  7: ORCA-Quest 2 → Hamamatsu")
        print(f"         Got: {result}")

    # -------- Test 8: Opera Phenix Plus --------
    text = "High-content screening was performed on an Opera Phenix Plus system."
    result = _extract(equip, text)
    ok = (
        _has_any(result, "MICROSCOPE_BRAND", ["Revvity", "PerkinElmer"]) and
        _has_any(result, "MICROSCOPE_MODEL", [
            "Opera Phenix Plus", "Opera Phenix",
            "Revvity Opera Phenix Plus", "Revvity Opera Phenix",
        ])
    )
    if ok:
        passed += 1
        print("PASS  8: Opera Phenix Plus → Revvity")
    else:
        failed += 1
        print(f"FAIL  8: Opera Phenix Plus → Revvity")
        print(f"         Got: {result}")

    # -------- Test 9: NIS-Elements → Nikon brand inference --------
    text = "Image analysis was performed using NIS-Elements software."
    sw_result = _extract(software, text)
    ok = _has_any(sw_result, "IMAGE_ACQUISITION_SOFTWARE", [
        "NIS-Elements", "NIS Elements",
    ])
    # Verify the KB can infer brand from software
    brand = infer_brand_from_software("NIS-Elements")
    ok = ok and (brand == "Nikon")
    if ok:
        passed += 1
        print("PASS  9: NIS-Elements detected + KB infers Nikon")
    else:
        failed += 1
        print(f"FAIL  9: NIS-Elements detected + KB infers Nikon")
        print(f"         Software result: {sw_result}")
        print(f"         KB brand inference: {brand}")

    # -------- Test 10: Bergamo II multiphoton --------
    text = "Two-photon imaging was performed on a Thorlabs Bergamo II multiphoton system."
    result = _extract(equip, text)
    ok = (
        _has(result, "MICROSCOPE_BRAND", "Thorlabs") and
        _has_any(result, "MICROSCOPE_MODEL", ["Bergamo", "Bergamo II", "Thorlabs Bergamo"])
    )
    if ok:
        passed += 1
        print("PASS 10: Bergamo II → Thorlabs")
    else:
        failed += 1
        print(f"FAIL 10: Bergamo II → Thorlabs")
        print(f"         Got: {result}")

    # -------- Summary --------
    print()
    print("=" * 50)
    print(f"RESULTS: {passed}/{total} passed, {failed}/{total} failed")
    print("=" * 50)

    # -------- Bonus: KB loader smoke tests --------
    print()
    print("KB Loader smoke tests:")
    kb = load_kb()
    print(f"  Systems loaded: {len(kb['systems'])}")
    print(f"  Alias groups: {len(kb['aliases'])}")
    print(f"  Brand→software mappings: {len(kb['brand_software'])}")

    sys_lsm = resolve_alias("LSM 880")
    if sys_lsm:
        print(f"  resolve_alias('LSM 880') → {sys_lsm['brand']} {sys_lsm['model']}")
    else:
        print("  resolve_alias('LSM 880') → None (UNEXPECTED)")

    brand = infer_brand_from_model("Stellaris")
    print(f"  infer_brand_from_model('Stellaris') → {brand}")

    techniques = infer_techniques_from_system("LSM 980")
    print(f"  infer_techniques_from_system('LSM 980') → {len(techniques)} techniques")

    sw = infer_software_from_brand("Zeiss")
    print(f"  infer_software_from_brand('Zeiss') → {sw}")

    cat = get_system_category("LSM 880")
    print(f"  get_system_category('LSM 880') → {cat}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_tests())
