#!/bin/bash
# execute: ./parallel.sh 2
# 2 means gpu
aggrs=(gcnconv gatconv sageconv ginconv)
#aggrs=(gcnconv)
datasets=(HGBn-ACM HGBn-DBLP HGBn-Freebase HGBn-IMDB)
models=(homo_GNN relation_HGNN mp_GNN)
#models=(homo_GNN relation_HGNN)
ran=(1 2)
for aggr in ${aggrs[*]}; do
  for i in ${ran[*]}; do
    yaml="yamlpath: ${aggr}_${i}.yaml"
    echo "===================================================================================="
    echo ${yaml}
    python space4hgnn/generate_yaml.py -a ${aggr} -s ${i} -k $2 -v $3
    for dataset in ${datasets[*]}; do
    	for model in ${models[*]}; do
        {
        para="-a ${aggr} -s ${i} -m ${model} -d ${dataset} -g $1 -t node_classification -k $2 -v $3 -r 1"
        echo "***************************************************************************************"
        echo ${para}
        python run.py ${para}
        }&
      done
      wait
    done
  done
done

