#!/bin/bash
#SBATCH --job-name=T1SRO25
#SBATCH --cpus-per-task=1
#SBATCH --ntasks=1
#SBATCH --mem=4G
#SBATCH --error=test1.err
#SBATCH --output=test1.out
#SBATCH --mail-type=ALL
#SBATCH --mail-user=benjamin.pichun@pregrado.uoh.cl
#SBATCH --array=1-1000%15
#SBATCH --time=00:40:00

export OMP_NUM_THREADS=1

echo "Empezando intento $SLURM_ARRAY_TASK_ID"

singularity exec SofaRISSoftLabCluster.sif python3 MagTecSkinToolBox/main.py -n MagneticSkin -op 0 -o -ni 10 -db Journal
