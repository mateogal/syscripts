#!/bin/bash
# This script belongs to (https://github.com/mateogal/Syscripts)

echo "$(date +"%Y-%m-%d %H:%M:%S"): Backups started" > /tmp/virsh-backups.log 2>&1

VM_ARRAY=("VM1" "VM2" "VM3")
RUNNING=0
BKP_PATH="/VMs-BKP" # Directory to move backups when it's finished

for vm in "${VM_ARRAY[@]}"; do
    echo "$(date +"%Y-%m-%d %H:%M:%S"): Backup for $vm started" >> /tmp/virsh-backups.log 2>&1
    virsh backup-begin "$vm"
    ((RUNNING++))
done

while [[ $RUNNING -gt 0 ]]; do
    for vm in "${VM_ARRAY[@]}"; do
        # Change "None" to the correct word for your OS language
        check=$(virsh domjobinfo "$vm" | grep "None")
        if [[ -n $check ]]; then
            echo "$(date +"%Y-%m-%d %H:%M:%S"): Backup for $vm finished" >> /tmp/virsh-backups.log 2>&1
            ((RUNNING--))
        fi
    done
    sleep 5
done

for vm in "${VM_ARRAY[@]}"; do
    mkdir -p "$BKP_PATH/$vm"
    disks=($(virsh domblklist "$vm" | grep -v '.iso' | awk 'NR > 2 { print $2 }' | grep -v '^$'))
    for disk in "${disks[@]}"; do
        echo "$(date +"%Y-%m-%d %H:%M:%S"): Moving backup of $disk" >> /tmp/virsh-backups.log 2>&1
        mv "$disk".* "$BKP_PATH/$vm/" >> /tmp/virsh-backups.log 2>&1
    done
done

echo "$(date +"%Y-%m-%d %H:%M:%S"): Backups finished" >> /tmp/virsh-backups.log 2>&1