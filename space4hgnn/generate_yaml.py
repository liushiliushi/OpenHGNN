import yaml
from random import choice
from random import randint
from random import random
from random import uniform
import argparse
import os
hidden_dim = [64]
layers_pre_mp = [1,2,3]
layers_post_mp = [1,2,3]
layers_gnn = [2,4,6,8]
stage_type = ['stack','skipsum','skipconcat']
activation = ['relu']
has_bn = [True, False]
gnn_type = ['gcnconv']
has_l2norm = [True, False]
mini_batch_flag = [False]
macro_func = ['attention', 'sum', 'mean','max']
dropout = [0.0, 0.3, 0.6]
lr = [0.1, 0.01, 0.001]
weight_decay = 0.0001
patience = 40
max_epoch = 400


def makeDict( aggr):
    dict = {
        'hidden_dim': choice(hidden_dim),
        'layers_pre_mp': choice(layers_pre_mp),
        'layers_post_mp': choice(layers_post_mp),
        'layers_gnn': choice(layers_gnn),
        'stage_type': choice(stage_type),
        'activation': choice(activation),
        'dropout': choice(dropout),
        'has_bn': choice(has_bn),

        'has_l2norm': choice(has_l2norm),
        'lr': choice(lr),
        'weight_decay': weight_decay,
        'patience': patience,
        'max_epoch': max_epoch,
        'mini_batch_flag': choice(mini_batch_flag),
        'macro_func': choice(macro_func),
        'gnn_type': aggr,
    }
    return dict

def datasetDict(dataset, aggr):
    set = ()
    set.add()
    return {dataset:set}

def generate(aggr, i):
    datasets = ['HGBn-ACM', 'HGBn-IMDB', 'HGBn-DBLP', 'HGBn-Freebase']
    models = ['homo_GNN', 'relation_HGNN', 'mp_GNN']
    dicts = {}
    for a in datasets:
        dict = {}
        for b in models:
            dict[b] = makeDict(aggr)
        dicts[a] = dict
    aproject = {'node_classification': dicts
    }

    fileNamePath = os.path.split(os.path.realpath(__file__))[0]
    if not os.path.exists('./config'):
        os.makedirs('./config')
    name = './config/' + aggr + '_' + i + '.yaml'
    yamlPath = os.path.join(fileNamePath, name)

    f = open(yamlPath,'w')
    print(yaml.dump(aproject,f))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--aggr', '-a', default='gcnconv', type=str, help='gnn type')
    parser.add_argument('--times', '-s', default='1', type=str, help='times')
    args = parser.parse_args()
    generate(args.aggr, args.times)