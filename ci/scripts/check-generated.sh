#!/bin/bash
# Copyright lowRISC contributors (OpenTitan project).
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

set -e

source ci/scripts/lib/snapshot.sh

# Run a command and then check the tree is still clean. Print a message if not.
_gen_and_check() {
    local before="$1"
    local thing="$2"
    local cmd="$3"
    ${cmd} || {
        echo "::error::Failed to auto-generate ${thing}. (command: '${cmd}')"
        echo
        return 1
    }

    is_clean "${before}" || {
        echo "::error::Auto-generated ${thing} not up-to-date. Regenerate with '${cmd}'."
        echo
        return 1
    }
}

# Run a command with a given before state of the repo and check that the state after running the 
# command is the same.
gen_and_check() {
  local before="$1"
  local thing="$2"
  shift
  shift
  local cmd="$*"
  _gen_and_check "$before" "$thing" "$cmd"
}

# Run a make target with a given before state of the repo and check that the state after running the 
# make target is the same.
gen_mk_and_check() {
  local before="$1";
  local thing="$2";
  shift 
  shift
  local cmd="make -k -C hw $*"
  _gen_and_check "$before" "$thing" "$cmd"
}

# Check generated files are up to date
before=$(snapshot)

gen_mk_and_check "$before" "Register headers" regs

# This runs both top and cmdgen targets together since for ipgen
# ips the top target will not run cmdgen on generated md files,
# causing this check to fail.
gen_mk_and_check "$before" "top and cmdgen" top_and_cmdgen

gen_mk_and_check "$before" "top_sim_cfgs" dvgen

gen_and_check "$before" \
    "secded primitive code" \
    util/design/secded_gen.py --no_fpv

gen_and_check "$before" "MUBI package" util/design/gen-mubi.py

gen_and_check "$before" "HW block summary" util/gen_doc_hw_summary_table.py

if is_clean "$before"; then
  exit 0
else
  exit 1
fi
