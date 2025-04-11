#!/bin/bash
# This script belongs to (https://github.com/mateogal/Syscripts)

echo "$(date +"%Y-%m-%d %H:%M:%S"): Backups started" > /tmp/virsh-backups.log 2>&1

VM_ARRAY=("VM1" "VM2" "VM3")
BKP_PATH="/VMs-BKP" # Directory to move backups when it's finished
VM_PENDING=("${VM_ARRAY[@]}")

for vm in "${VM_ARRAY[@]}"; do
    echo "$(date +"%Y-%m-%d %H:%M:%S"): Backup for $vm started" >> /tmp/virsh-backups.log 2>&1
    virsh backup-begin "$vm"
done

i=0
while [[ ${#VM_PENDING[@]} -gt 0 ]]; do
    vm="${VM_PENDING[$i]}"
    # Change "None" to the correct word for your OS language
    check=$(virsh domjobinfo "$vm" 2>/dev/null | grep "None")

    if [[ -n $check ]]; then
        echo "$(date +"%Y-%m-%d %H:%M:%S"): Backup for $vm finished" >> /tmp/virsh-backups.log 2>&1
        unset 'VM_PENDING[i]'
        VM_PENDING=("${VM_PENDING[@]}")
        i=0
    else
        ((i++))
        [[ $i -ge ${#VM_PENDING[@]} ]] && i=0
    fi
    sleep 1
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