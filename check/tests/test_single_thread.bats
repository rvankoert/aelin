#!/bin/env bats

SCRIPT="./find-corrupted-jpg.sh"
TEST_DIR="tests/fixtures"

@test "corrupted jpg is reported as corrupted" {
    run $SCRIPT $TEST_DIR
    [[ "$output" == *"tests/fixtures/corrupted.jpg 1"* ]]
}