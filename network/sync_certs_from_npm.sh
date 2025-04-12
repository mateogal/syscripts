#!/bin/bash

# Configuración
REMOTE_USER=""
REMOTE_HOST=""
REMOTE_CERT_PATH=""
LOCAL_CERT_PATH=""
DOMAIN=""
LOG_PATH="/var/log/sync_certs.log"

# Remote files and local names
declare -A FILES=(
    ["fullchain.pem"]="cert.pem"
    ["privkey.pem"]="key.pem"
)

# Make a function to calculate hash
get_remote_hash() {
    ssh -i ~/.ssh/id_rsa ${REMOTE_USER}@${REMOTE_HOST} "sha256sum ${REMOTE_CERT_PATH}/$1 | cut -d ' ' -f1"
}

get_local_hash() {
    sha256sum ${LOCAL_CERT_PATH}/$1 | cut -d ' ' -f1
}

# Compare and copy if there are changes
CERT_CHANGED=0
echo "Started" > ${LOG_PATH} 2>&1
for REMOTE_FILE in "${!FILES[@]}"; do
    LOCAL_FILE="${FILES[$REMOTE_FILE]}"
    echo "Comparing $REMOTE_FILE → $LOCAL_FILE..." >> ${LOG_PATH} 2>&1

    REMOTE_HASH=$(get_remote_hash "$REMOTE_FILE")
    LOCAL_HASH=$(get_local_hash "$LOCAL_FILE")

    if [[ "$REMOTE_HASH" != "$LOCAL_HASH" ]]; then
        echo "$REMOTE_FILE was changed. Copying..." >> ${LOG_PATH} 2>&1
        scp -i ~/.ssh/id_rsa ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_CERT_PATH}/${REMOTE_FILE} ${LOCAL_CERT_PATH}/${LOCAL_FILE}
        CERT_CHANGED=1
    else
        echo "$LOCAL_FILE was not changed." >> ${LOG_PATH} 2>&1
    fi
done

if [[ "$CERT_CHANGED" == "1" ]]; then
    echo "Restarting services..." >> ${LOG_PATH} 2>&1
    docker restart $(docker ps -qaf name=postfix-mailcow) >> ${LOG_PATH} 2>&1
    docker restart $(docker ps -qaf name=nginx-mailcow) >> ${LOG_PATH} 2>&1
    docker restart $(docker ps -qaf name=dovecot-mailcow) >> ${LOG_PATH} 2>&1
    echo "Certificates updated and services restarted." >> ${LOG_PATH} 2>&1
else
    echo "No changes detected in the certificates." >> ${LOG_PATH} 2>&1
fi
