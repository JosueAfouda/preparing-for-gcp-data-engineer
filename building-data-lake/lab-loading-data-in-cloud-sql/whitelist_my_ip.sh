#!/bin/bash

# Name of your Cloud SQL instance
INSTANCE_NAME="taxi"

# Gets the public IPv4 address and adds /32 for CIDR
MY_IP=$(curl -4 -s ifconfig.me)/32

echo "Adresse IP détectée : $MY_IP"
echo "Ajout à la whitelist de l'instance Cloud SQL : $INSTANCE_NAME..."

# Apply the patch with the IP address
gcloud sql instances patch "$INSTANCE_NAME" --authorized-networks="$MY_IP"

# Check if everything went well
if [ $? -eq 0 ]; then
  echo "IP $MY_IP successfully authorized for the instance $INSTANCE_NAME."
else
  echo "An error occurred while updating the whitelist."
fi
