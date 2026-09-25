# RevealLine Archive 86

Prepared preservation infrastructure for the exact published v0.116.1 release.

This new archive has zero previously accepted paths. Deployment, complete public-byte verification and scoped browser acceptance are pending. The donor repository and commit in input-authority.json identify the unchanged scaffold origin; donor public-acceptance records are not Archive86 evidence. The source qualification and frozen test-policy bytes retain their original historical scope.

input-authority.json pins the fresh release/tag/source descriptors. Run `python3 -B tools/configure.py --check` to verify generated source-lock and inventory against those originals. To generate only a new scaffold, use `--write` with both output paths absent; existing files cannot be overwritten.

Run all archive infrastructure tests with `python3 -B -m unittest discover -s tools -p 'test_*.py' -v`. The workflow runs these and the unchanged pinned extractor tests unconditionally. Hosted extraction requires at least 3 GiB free, verifies the original ZIP and every member, then independently rereads the complete finite artifact. No game rebuild is performed.

All immutable game bytes, original workers, tag/source identities, checksum pins and the 800,000,000-byte archive budget remain unchanged. The main publisher may adopt this archive only after its separate byte/browser admission.
