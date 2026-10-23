#!/usr/bin/env bash
# # Usage
# before=$(snapshot)
# .
# . main script generating files
# .
# if is_clean "$before"; then
#   exit 0
# else
#   exit 1
# fi

set -e

# snapshot a hash of all the git tracked files and untracked files, but not ignored files
# in the repo at this point
snapshot() {
  git ls-files -z --cached --others --exclude-standard |
    sort -z |
    xargs -0 -r sha256sum |
    sort
}

# Returns 0 if there are no changes or untracked files, 1 otherwise.
# Show the diff on STDOUT if there's deviation.
is_clean() {
  local before="$1"
  local after
  after=$(snapshot) || return 1
  if [[ "$before" != "$after" ]]; then
    echo Diff between the regenerated content and the content in this PR/the repository:
    # the || true is to mask diff's exit code when there is a mismatch
    diff -u <(printf '%s\n' "$before") <(printf '%s\n' "$after") || true
    git diff
    return 1
  fi

  return 0
}
