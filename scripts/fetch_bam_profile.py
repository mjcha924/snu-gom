"""Fetch and verify one pinned upstream parameter file, without installing BAM."""

import argparse
import hashlib
from urllib.request import urlopen

from runtime import ROOT
from snu_gom_walk.bam import BAM_PROFILE_SHA256, BAM_PROFILE_URL


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    output = ROOT / ".deps/bam/xl330-m1.json"
    with urlopen(BAM_PROFILE_URL, timeout=30) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != BAM_PROFILE_SHA256:
        raise ValueError("Upstream profile checksum mismatch; no file written")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    print(output)


if __name__ == "__main__":
    main()
