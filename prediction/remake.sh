#!/bin/bash
#1: gpu
#2: repeat
#3: key
#4: value
if [ ! -n "$1" ]; then
  echo "gpu is empty"
  exit 0
fi
if [ ! -n "$2" ]; then
  echo "repeat is empty"
  exit 0
fi
if [ ! -n "$3" ]; then
  echo "key is empty"
  exit 0
fi
if [ ! -n "$4" ]; then
  echo "value is empty"
  exit 0
fi
rans=(1 2)
models=(homo_GNN mp_GNN relation_HGNN)
aggrs=(gatconv gcnconv ginconv sageconv)
datasets=(ACM DBLP Freebase IMDB)
predictdir="$3_$4"
count=0
cd ${predictdir} || exit
project_path=$(cd `dirname $0`; pwd)
echo $project_path
for model in ${models[*]}; do
  for aggr in ${aggrs[*]}; do
    for ran in ${rans[*]}; do
      dir="${model}_${aggr}_${ran}"
      echo ${dir}
      if [ ! -d ${dir} ]
      then
        mkdir ${dir}
      fi
      cd ${dir} || exit

      for dataset in ${datasets[*]}; do
        for i in `seq 1 $2`; do
        {
          file="${dataset}_${i}.txt"
          if [ ! -f ${file} ]
          then
            count=$count+1
            hgb="HGBn-${dataset}"
            cd "/home/ubuntu/liushi/workspace/OpenHGNN/" || exit
            para="-a ${aggr} -s ${i} -m ${model} -d ${hgb} -g $1 -t node_classification -k $3 -v $4 -r 1"
            echo "***************************************************************************************"
            echo ${para}
            python run.py ${para}
            cd ${project_path} || exit
          fi
        }&
        done
        wait
      done

      cd ..
    done
  done
done
echo "Count:"
echo ${count}
#project_path=$(cd `dirname $0`; pwd)
#project_name="${project_path##*/}"
#echo $project_path
#echo $project_name
