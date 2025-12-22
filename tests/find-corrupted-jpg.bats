#!/bin/env bats

@test "corrupted jpg is reported as corrupted" {
    repo_root="$(cd "$BATS_TEST_DIRNAME/.." && pwd)"
    checker_dir="$repo_root/check"
    fixtures_dir="$repo_root/tests/fixtures"
    
    run "$checker_dir/find-corrupted-jpg.sh" "$fixtures_dir"
    [ "$status" -eq 0 ]
    [[ "$output" == *"tests/fixtures/corrupted.jpg 1"* ]]
}