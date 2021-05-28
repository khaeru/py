#!/bin/sh
# See svante_jupyter_job.sh

# Generate an SSH key with no passphrase
ssh-keygen -N "" -f ~/.ssh/id_rsa_jupyter_kg

# Authorize the key for this account
cat ~/.ssh/id_rsa_jupyter_kg.pub >>~/.ssh/authorized_keys

# Configure SSH to use the key when connecting to svante-login
cat <<EOF >>~/.ssh/config
Host c* svante-login
  ControlPath ~/.ssh/ctl-sock-jupyter-kg
  IdentityFile ~/.ssh/id_rsa_jupyter_kg
  StrictHostKeyChecking no
EOF
