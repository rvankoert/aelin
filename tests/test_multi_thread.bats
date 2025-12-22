#!/bin/env bats

SCRIPT="./find-corrupted-multithreaded.sh"
TEST_DIR="tests/fixtures"

@test "multi-threaded checker finds corrupted jpg and writes to output file" {

    run "$SCRIPT" "$TEST_DIR"
    
    find "$TEST_DIR" -name corrupted_jpgs_summary.txt -exec \
        grep -q "^corrupted\.jpg[[:space:]]\+1$" {} \; \
        -quit
}
