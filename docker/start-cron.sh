#!/usr/bin/env bash
set -euo pipefail

touch /var/log/sweepstake.log
cron
tail -F /var/log/sweepstake.log

