#!/usr/bin/env python3
"""Build Archive86's exact v0.116.1 source lock and finite inventory.

All identities are read from the separately reviewed input-authority.json. This
file contains no donor release-cohort constants.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2) + "\n").encode()


def read_json(relative):
    return json.loads((ROOT / relative).read_bytes())


def exact_asset(assets, name):
    matches = [row for row in assets if row["name"] == name]
    assert len(matches) == 1
    return matches[0]


def construct():
    import sys
    sys.path.insert(0, str(ROOT / "tools"))
    import verify

    authority = read_json("input-authority.json")
    assert authority["format"] == "revealline-archive-scaffold-input.v2"
    archive = authority["archive"]
    preserved = authority["preservedRelease"]
    projection = authority["projection"]
    version = preserved["version"]
    metadata = ROOT / "metadata" / version
    record = json.loads((metadata / "release.json").read_bytes())
    manifest = json.loads((metadata / "manifest.json").read_bytes())
    checksum = (metadata / "distribution.zip.sha256").read_bytes()
    qualification = metadata / "source-qualification.json"
    policy = metadata / "test-policy.json"
    assets = preserved["assets"]
    zip_asset = exact_asset(assets, "distribution.zip")
    assert len(assets) == 9 and len({row["name"] for row in assets}) == 9
    assert record["version"] == manifest["version"] == version
    assert record["sourceRevision"] == manifest["sourceRevision"] == preserved["sourceRevision"]
    assert record["distributionSha256"] == zip_asset["sha256"] == checksum.decode().split()[0]
    assert manifest["totalBytes"] == projection["manifestBytes"]
    assert len(manifest["files"]) == projection["manifestFiles"]
    for name in ("release.json", "manifest.json", "distribution.zip.sha256", "source-qualification.json"):
        expected = exact_asset(assets, name)
        file = metadata / name
        assert file.stat().st_size == expected["bytes"] and sha(file.read_bytes()) == expected["sha256"]
    policy_pin = preserved["policyEvidence"]
    assert policy.stat().st_size == policy_pin["bytes"] and sha(policy.read_bytes()) == policy_pin["sha256"]

    release = {
        "version": version,
        "sourceRevision": preserved["sourceRevision"],
        "sourceTree": preserved["sourceTree"],
        "tagObject": preserved["tagObject"],
        "distributionSha256": zip_asset["sha256"],
        "distributionBytes": zip_asset["bytes"],
        "metadata": {
            name: sha((metadata / name).read_bytes())
            for name in ("release.json", "manifest.json", "distribution.zip.sha256")
        },
        "sourceQualification": {
            "bytes": qualification.stat().st_size,
            "sha256": sha(qualification.read_bytes()),
            "policyEvidence": policy_pin,
        },
    }
    lock = {
        "format": "revealline-archive-originals.v2",
        "archiveId": archive["id"],
        "repository": archive["repository"],
        "sourceRepository": "mekhovov/revealline",
        "toolingCommit": archive["toolingCommit"],
        "extractorPath": archive["extractorPath"],
        "extractorSha256": archive["extractorSha256"],
        "budgetBytes": archive["budgetBytes"],
        "releases": [release],
    }
    rows = verify.metadata_inventory(ROOT, release)
    rows.extend([
        {"path": ".nojekyll", "bytes": 0, "sha256": sha(b"")},
        {"path": "index.html", "bytes": (ROOT / "index.html").stat().st_size, "sha256": sha((ROOT / "index.html").read_bytes())},
        {"path": "releases/index.html", "bytes": (ROOT / "releases/index.html").stat().st_size, "sha256": sha((ROOT / "releases/index.html").read_bytes())},
    ])
    rows.sort(key=lambda row: row["path"])
    inventory = {"base": f"https://mekhovov.github.io/{archive['repository'].split('/', 1)[1]}/", "files": rows}
    inventory_raw = json_bytes(inventory)
    lock.update({
        "expectedInventorySha256": sha(inventory_raw),
        "expectedFiles": len(rows),
        "expectedBytes": sum(row["bytes"] for row in rows),
    })
    assert lock["expectedFiles"] == projection["expectedFiles"]
    assert lock["expectedBytes"] == projection["expectedBytes"]

    original = read_json("authority/preserved-release-original.json")
    assert original["id"] == preserved["releaseId"] and original["tag_name"] == version
    assert not original["draft"] and not original["prerelease"] and len(original["assets"]) == 9
    api_assets = sorted([
        {"id": row["id"], "name": row["name"], "bytes": row["size"], "sha256": row["digest"].removeprefix("sha256:")}
        for row in original["assets"]
    ], key=lambda row: row["name"])
    assert api_assets == assets
    assert read_json("authority/reviewed-release-descriptors.json")["assets"] == assets
    tag = read_json("authority/preserved-tag-original.json")
    ref = read_json("authority/preserved-tag-ref-original.json")
    commit = read_json("authority/preserved-source-commit-original.json")
    assert tag["sha"] == ref["object"]["sha"] == preserved["tagObject"]
    assert tag["object"]["type"] == "commit" and tag["object"]["sha"] == preserved["sourceRevision"]
    assert commit["sha"] == preserved["sourceRevision"] and commit["tree"]["sha"] == preserved["sourceTree"]
    return json_bytes(lock), inventory_raw


def main():
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--write", action="store_true")
    modes.add_argument("--check", action="store_true")
    args = parser.parse_args()
    lock, inventory = construct()
    targets = ((ROOT / "source-lock.json", lock), (ROOT / "expected-inventory.json", inventory))
    mode = "--write" if args.write else "--check"
    if args.write:
        for target, raw in targets:
            with target.open("xb") as output:
                output.write(raw)
    else:
        for target, raw in targets:
            assert target.read_bytes() == raw
    print(json.dumps({"status": "PASS", "mode": mode, "sourceLockSha256": sha(lock), "inventorySha256": sha(inventory)}))


if __name__ == "__main__":
    main()
