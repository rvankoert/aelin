#!/usr/bin/env bats

@test "multi-threaded checker writes summary including corrupted jpg" {
    repo_root="$(cd "$BATS_TEST_DIRNAME/.." && pwd)"
    checker_dir="$repo_root/check"
    fixtures_dir="$repo_root/tests/fixtures"
    num_threads=8

    tmpdir="$(mktemp -d)"
    outfile="$tmpdir/corrupted_jpgs_summary.txt"

    cp "$checker_dir/find-corrupted-jpg.sh" "$tmpdir/"
    chmod +x "$tmpdir/find-corrupted-jpg.sh"

    cd "$tmpdir"
    run "$checker_dir/find-corrupted-multithreaded.sh" \
        "$fixtures_dir" \
        "$num_threads" \
        "$outfile"

    [ -f "$outfile" ]
    grep -q "corrupted\.jpg[[:space:]]\+1$" "$outfile"


}
