#!/bin/bash
set -e

echo "---> Starting HTCondor-CE ..."
export CONDOR_CONFIG=/etc/condor-ce/condor_config

mkdir -p /var/lib/condor-ce/spool
chown -R condor:condor /var/lib/condor-ce
chown -R condor:condor /var/log/condor-ce /var/run/condor-ce

/usr/share/condor-ce/condor_ce_startup -f &
CE_PID=$!

echo "---> Waiting for HTCondor-CE collector ..."
until condor_status -pool 127.0.0.1:9619 >/dev/null 2>&1; do
  sleep 2
done

echo "---> Creating local test token for testce ..."
TOKEN_FILE=/home/testce/.condor/tokens.d/local
if [ ! -s "$TOKEN_FILE" ]; then
  mkdir -p /home/testce/.condor/tokens.d
  condor_token_create \
    -identity testce@users.htcondor.org \
    > "$TOKEN_FILE"
  chmod 600 "$TOKEN_FILE"
  chown -R testce:testce /home/testce/.condor
fi

echo "---> HTCondor-CE is ready."
wait "$CE_PID"