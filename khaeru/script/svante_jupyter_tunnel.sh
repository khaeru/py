#!/bin/sh
# See svante_jupyter_job.sh

HEAD_NODE=svante
KG_PORT=8888

ssh -fNL $KG_PORT:localhost:$KG_PORT $HEAD_NODE
