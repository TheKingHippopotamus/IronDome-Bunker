#!/bin/sh
# Per-connection playground session wrapper.
#
# textual-serve spawns this script once per browser connection.
# Each session gets a completely isolated temporary HOME so users
# never share vault data.  The directory is wiped on disconnect.
#
# Session hard-limit: 2 hours (prevents orphaned processes).

SESSION_DIR=$(mktemp -d /tmp/irondome-session-XXXXXXXX)

cleanup() {
    rm -rf "$SESSION_DIR"
}
trap cleanup EXIT INT TERM

export HOME="$SESSION_DIR"

exec timeout 7200 irondome
