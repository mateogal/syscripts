#!/bin/bash
# This script is part of (https://github.com/mateogal/Syscripts)

VM_ARRAY=("VM1" "VM2" "VM3")
RUNNING=0
VM_PATH="/Data/VMs"
MOVE_PATH="/VMs-BKP" # Directory to move backups when finished

for vm in "${VM_ARRAY[@]}"; do
    virsh backup-begin "$vm"
    ((RUNNING++))
done

while [[ $RUNNING -gt 0 ]]; do
    for vm in "${VM_ARRAY[@]}"; do
        # Change "None" to the correct word for your OS language
        check=$(virsh domjobinfo "$vm" | grep "None")
        if [[ -n $check ]]; then
            ((RUNNING--))
        fi
    done
    sleep 5
done

for vm in "${VM_ARRAY[@]}"; do
    mkdir -p "$MOVE_PATH/$vm"
    mv "$VM_PATH/$vm.qcow2.*" "$MOVE_PATH/$vm/"
done