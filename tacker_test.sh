#!/bin/bash
set -x
function die() {
    local exitcode=$?
    set +o xtrace
    echo $@
    exit $exitcode
}

noauth_tenant_id=me
if [ $1 == 'noauth' ]; then
    NOAUTH="--tenant_id $noauth_tenant_id"
else
    NOAUTH=
fi

FORMAT=" --request-format xml"

# test the CRUD of xxx
# TODO(yamahata)
