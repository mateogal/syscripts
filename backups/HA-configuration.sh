#!/bin/bash
# This script is part of (https://github.com/mateogal/Syscripts)
# THIS SCRIPT IS NOT COMPLETE

RED='\033[1;31m'
GREEN='\033[1;32m'
BLUE='\033[1;34m'
NC='\033[0m' # No Color

# https://www.golinuxcloud.com/how-to-setup-drbd-cluster-file-system-centos8#How_to_configure_DRBD_Cluster_File_System
# https://www.golinuxcloud.com/how-to-install-configure-two-node-cluster-linux-centos-7/
# https://linbit.com/drbd-user-guide/drbd-guide-9_0-en/#ch-configure
# https://www.youtube.com/watch?v=5JLLGfAuznc&list=PLK_pwPC2gL5cMuLctffVZOQFvh1I6ysJR&index=14
# https://www.youtube.com/watch?v=oyLWUjLTiX8

clear

SUSE_LEAP="drbd ha-cluster-bootstrap conntrack-tools corosync-qdevice pacemaker csync2 hawk2 crmsh yast2-cluster yast2-drbd"
SUSE_TUMBLEWEED="drbd conntrack-tools corosync-qdevice pacemaker csync2 hawk2 crmsh yast2-cluster yast2-drbd"
SUSE_ENTERPRISE=""

if [ "$(id -u)" != "0" ]; then
   echo "You must execute this script as root." 1>&2
   exit 1
fi

if [ "$(grep "openSUSE" /etc/os-release)" == "" ]; then
   echo "This script only work in SUSE distros."
   exit 1
fi

SUSE_VERSION=$(grep -w "NAME" /etc/os-release | cut -f2 -d " " | cut -f1 -d '"')
case $SUSE_VERSION in
"Tumbleweed")
   PACKAGES=$SUSE_TUMBLEWEED
   ;;
"Leap")
   PACKAGES=$SUSE_LEAP
   ;;
esac
echo "#############################################################"
echo -e "openSUSE ${GREEN}$SUSE_VERSION ${NC}DETECTED"
echo "#############################################################"

configure_new_cluster() {
   read -p "Enter your new cluster name: " clusterName
   read -p "You want to add an resource? Y/N: " addResource
   if [ "$addResource" == "Y" ] || [ "$addResource" == "y" ]; then
      read -p "Enter device name: " deviceName
   fi
   read -p "You want to add an default network interface? Y/N: " addInterface
   if [ "$addInterface" == "Y" ] || [ "$addInterface" == "y" ]; then
      read -p "Enter device name: " deviceName
   fi
}

join_node_to_cluster() {
   read -p "You want to add an default network interface? Y/N: " addInterface
   if [ "$addInterface" == "Y" ] || [ "$addInterface" == "y" ]; then
      read -p "Enter device name: " deviceName
      crm cluster join -i $deviceName
   else
      crm cluster join
   fi
}

generate_resource_node_cfg(){
   srcLines=$(head -n 5 /tmp/drbdNodeCfg.tmp)
   hostname=$(echo $srcLines | cut -f1 -d " ")
   ip=$(echo $srcLines | cut -f2 -d " ")
   port=$(echo $srcLines | cut -f3 -d " ")
   device=$(echo $srcLines | cut -f4 -d " ")
   partition=$(echo $srcLines | cut -f5 -d " ")
   nodeCfg = (echo -e "on $hostname {
 		   device $device;
       	disk $partition;
        	meta-disk internal;
         address $ip:$port;
      }")
   tail -n +6 /tmp/drbdNodeCfg.tmp > /tmp/drbdNodeCfg.tmp
   return $nodeCfg
}

generate_resource_file(){
   echo -e "
   resource $1 {
      $(for ((i=0; i<$2; i++));do 
         generate_resource_node_cfg
         "$?"
      done)
   }" > /etc/drbd.d/$1.res
}

while true; do
   read -p "
1) Install required packages
2) DRBD configuration
3) Pacemaker configuration
4) BTRFS automatic snapshot schedule configuration
5) Exit

Choose an option: " menu

   case $menu in
   1)
      echo "######################################################################"
      echo -e "#################### ${BLUE}INSTALLING REQUIRED PACKAGES ${NC}####################"
      echo "######################################################################"
      zypper install $PACKAGES
      if [ $(echo $?) == 0 ]; then
         echo "######################################################################"
         echo -e "################ ALL PACKAGES INSTALLED ${GREEN}SUCCESSFULLY ${NC}#################"
         echo "######################################################################"
      else
         echo "######################################################################################"
         echo -e "#################### ${RED}Some errors detected. Please check manually. ####################"
         echo "######################################################################################"
         exit 1
      fi
      ;;
   2) 
      read -p "Enter name for new resource: " newResource
      read -p "How many nodes you will replicate? : " nodesQty
      for ((i=0; i<$nodesQty; i++)); do
         read -p "Enter your node hostname: " nodeHostname
         read -p "Enter your node IP: " nodeIP
         read -p "Enter your node DRBD port: " nodePort
         read -p "Enter your DRBD device [/dev/drbdX]: " nodeDevice
         read -p "Enter your partition name: " nodePartition
         echo -e "$nodeHostname
         $nodeIP
         $nodePort
         $nodeDevice
         $nodePartition" >> /tmp/drbdNodeCfg.tmp
      done
      generate_resource_file $newResource $nodesQty
      read -p "You want to propagate configuration files to nodes? [Y/N]: " isProp
      if [ "$isProp" == "Y" ] || [ "$isProp" == 'y' ]; then
         for ((i=0; i < $nodesQty; i++)); do
            read -p "Enter your node SSH user: " nodeUser
            read -p "Enter your node SSH Port: " nodeSshPort
            read -p "Enter your node IP: " nodeIP
            scp -p $nodeSshPort /etc/drbd.d/$newResource.res $nodeUser@$nodeIP:/etc/drbd.d/$newResource.res
      fi
      drbdadm create-md $newResource
      ;;
   3)
      echo "################################################################################################"
      echo -e "#################### ${RED}ALL NODES MUST HAVE THE SAME NETWORK INTERFACE NAMES ${NC}. ####################"
      echo "################################################################################################"
      while true; do
         echo -en "${GREEN}J${NC}oin node to a Cluster or make a ${GREEN}N${NC}ew Cluster? J/N: "
         read clusterOpt
         if [ "$clusterOpt" == "J" ] || [ "$clusterOpt" == "j" ]; then
            join_node_to_cluster
            break
         elif [ "$clusterOpt" == "N" ] || [ "$clusterOpt" == "n" ]; then
            configure_new_cluster
            break
         else
            echo -e "${RED}Invalid option${NC}"
         fi
      done
      ;;
   4) ;;
   5)
      exit
      ;;
   *)
      echo -e "${RED}Invalid option${NC}"
      ;;
   esac

done
