#!/bin/bash
#SBATCH --nodes 1
#SBATCH --partition ddr
#SBATCH --output jupyter-kg.log
#SBATCH --open-mode append

# Modified from https://gist.github.com/zonca/5f8b5ccb826a774d3f89, as described
# at https://zonca.github.io/2015/09/ipython-jupyter-notebook-sdsc-comet.html

# Once gateway has exited/been killed, close the tunnel
cleanup()
{
    echo "Caught TERM, cleaning up…"
    ssh -O exit $SLURM_SUBMIT_HOST
    rm -f ~/.ssh/ctl-sock-jupyter-kg
    exit 0
}

trap 'cleanup' TERM

echo "Starting new kernel gateway on $SLURM_NODELIST…"

# svante sets a non-writeable value for this
unset XDG_RUNTIME_DIR

# Choose your own unique port between 8000 and 9999
export KG_PORT=8888

# Setup tunnel between computing and login node
rm -f ~/.ssh/ctl-sock-jupyter-kg
ssh -fMNR $KG_PORT:localhost:$KG_PORT $SLURM_SUBMIT_HOST

# Launch the kernel gateway
jupyter kernelgateway
