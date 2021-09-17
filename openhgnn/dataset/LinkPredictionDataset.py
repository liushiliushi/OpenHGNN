import dgl
import numpy as np
import torch as th
from dgl.data.utils import load_graphs
from dgl.data.knowledge_graph import load_data
from . import BaseDataset, register_dataset
from . import AcademicDataset, HGBDataset
from ..utils import add_reverse_edges


@register_dataset('link_prediction')
class LinkPredictionDataset(BaseDataset):
    """
    metric: Accuracy, multi-label f1 or multi-class f1. Default: `accuracy`
    """
    def __init__(self,):
        super(LinkPredictionDataset, self).__init__()


@register_dataset('demo_link_prediction')
class Test_LinkPrediction(LinkPredictionDataset):
    def __init__(self, dataset_name):
        super(Test_LinkPrediction, self).__init__()
        self.g = self.load_HIN('./openhgnn/debug/data.bin')
        self.target_link = 'user-item'
        self.has_feature = False
        self.preprocess()
        #self.generate_negative()

    def load_HIN(self, dataset_name):
        g, _ = load_graphs(dataset_name)
        return g[0]

    def preprocess(self):
        test_mask = self.g.edges[self.target_link].data['test_mask']
        index = th.nonzero(test_mask).squeeze()
        self.test_edge = self.g.find_edges(index, self.target_link)
        self.pos_test_graph = dgl.heterograph({('user', 'user-item', 'item'): self.test_edge}, {ntype: self.g.number_of_nodes(ntype) for ntype in ['user', 'item']})
        self.g.remove_edges(index, self.target_link)
        self.g.remove_edges(index, 'item-user')
        self.neg_test_graph, _ = dgl.load_graphs('./openhgnn/debug/neg.bin')
        self.neg_test_graph = self.neg_test_graph[0]
        return

    def generate_negative(self):
        k = 99
        e = self.pos_test_graph.edges()
        neg_src = []
        neg_dst = []
        for i in range(self.pos_test_graph.number_of_edges()):
            src = e[0][i]
            exp = self.pos_test_graph.successors(src)
            dst = th.randint(high=self.g.number_of_nodes('item'), size=(k,))
            for d in range(len(dst)):
                while dst[d] in exp:
                    dst[d] = th.randint(high=self.g.number_of_nodes('item'), size=(1,))
            src = src.repeat_interleave(k)
            neg_src.append(src)
            neg_dst.append(dst)
        neg_edge = (th.cat(neg_src), th.cat(neg_dst))
        neg_graph = dgl.heterograph({('user', 'user-item', 'item'): neg_edge}, {ntype: self.g.number_of_nodes(ntype) for ntype in ['user', 'item']})
        dgl.save_graphs('./openhgnn/debug/neg.bin', neg_graph)


@register_dataset('hin_link_prediction')
class HIN_LinkPrediction(LinkPredictionDataset):
    def __init__(self, dataset_name):
        super(HIN_LinkPrediction, self).__init__()
        self.g = self.load_HIN(dataset_name)

    def load_link_pred(self, path):
        u_list = []
        v_list = []
        label_list = []
        with open(path) as f:
            for i in f.readlines():
                u, v, label = i.strip().split(', ')
                u_list.append(int(u))
                v_list.append(int(v))
                label_list.append(int(label))
        return u_list, v_list, label_list

    def load_HIN(self, dataset_name):
        if dataset_name == 'academic4HetGNN':
            # which is used in HetGNN
            dataset = AcademicDataset(name='academic4HetGNN', raw_dir='')
            g = dataset[0].long()

            self.train_batch = self.load_link_pred('./openhgnn/dataset/' + dataset_name + '/a_a_list_train.txt')
            self.test_batch = self.load_link_pred('./openhgnn/dataset/' + dataset_name + '/a_a_list_test.txt')
            self.category = 'author'
        return g


@register_dataset('HGBl_link_prediction')
class HGB_LinkPrediction(LinkPredictionDataset):
    r"""
    The HGB dataset will be used in task *link prediction*.

    Dataset Name :
    HGBn-amazon/HGBn-LastFM/HGBn-PubMed

    So if you want to get more information, refer to
    `HGB datasets <https://github.com/THUDM/HGB>`_

    Attributes
    -----------
    has_feature : bool
        Whether the dataset has feature. Except HGBl-LastFM, others have features.
    target_link : list of tuple[canonical_etypes]
        The etypes of test link. HGBl-amazon has two etypes of test link. other has only one.

    """
    def __init__(self, dataset_name):
        super(HGB_LinkPrediction, self).__init__()
        self.dataset_name = dataset_name
        self.has_feature = True
        if dataset_name == 'HGBl-amazon':
            dataset = HGBDataset(name=dataset_name, raw_dir='')
            g = dataset[0].long()
            self.has_feature = True
            self.target_link = [('product', 'product-product-0', 'product'),
                                ('product', 'product-product-1', 'product')]
            self.link = [0, 1]
            self.node_type = ["product"]
            self.test_edge_type = {'product-product-0': 0, 'product-product-1': 1}
            self.meta_paths = [(('product', 'product-product-0', 'product'), ('product', 'product-product-1', 'product')),
                               (('product', 'product-product-1', 'product'), ('product', 'product-product-0', 'product')),
                               ]

        elif dataset_name == 'HGBl-LastFM':
            dataset = HGBDataset(name=dataset_name, raw_dir='')
            g = dataset[0].long()
            self.has_feature = False
            self.target_link = [('user', 'user-artist', 'artist')]
            self.node_type = ['user', 'artist', 'tag']
            self.test_edge_type = {'user-artist': 0}
            g = add_reverse_edges(g)
            self.meta_paths = [
                (('user', 'user-artist', 'artist'), ('artist', 'user-artist-rev', 'user')),
                (('user', 'user-artist', 'artist'), ('artist', 'artist-tag', 'tag'),
                 ('tag', 'artist-tag-rev', 'artist'), ('artist', 'user-artist-rev', 'user')),
                (('artist', 'user-artist-rev', 'user'), ('user', 'user-artist', 'artist')),
                (('artist', 'artist-tag', 'tag'), ('tag', 'artist-tag-rev', 'artist'))
                ]


        elif dataset_name == 'HGBl-PubMed':
            dataset = HGBDataset(name=dataset_name, raw_dir='')
            g = dataset[0].long()
            self.has_feature = True
            self.target_link = [('1', '1_to_1', '1')]
            self.node_type = ['0', '1', '2', '3']
            self.test_edge_type = {'1_to_1': 2}
            g = add_reverse_edges(g)


        self.g = g
        self.shift_dict = self.calculate_node_shift()

    def load_link_pred(self, path):
        return

    def calculate_node_shift(self):
        node_shift_dict = {}
        count = 0
        for type in self.node_type:
            node_shift_dict[type] = count
            count += self.g.num_nodes(type)
        return node_shift_dict

    def get_idx(self):
        r"""
        Get graphs for train, valid or test.

        The dataset has not validation_mask, so we split train edges randomly.
        """
        val_edge_dict = {}
        test_edge_dict = {}
        out_ntypes = []
        train_graph = self.g
        val_ratio = 0.1
        for etype in self.target_link:
            train_mask = self.g.edges[etype].data['train_mask'].squeeze()
            train_index = th.nonzero(train_mask).squeeze()
            random_int = th.randperm(len(train_index))[:int(len(train_index) * val_ratio)]
            val_index = train_index[random_int]
            val_edge = self.g.find_edges(val_index, etype)

            test_mask = self.g.edges[etype].data['test_mask'].squeeze()
            test_index = th.nonzero(test_mask).squeeze()
            test_edge = self.g.find_edges(test_index, etype)

            val_edge_dict[etype] = val_edge
            test_edge_dict[etype] = test_edge
            out_ntypes.append(etype[0])
            out_ntypes.append(etype[2])

            train_graph = dgl.remove_edges(train_graph, th.cat((val_index, test_index)), etype)
        self.out_ntypes = set(out_ntypes)
        val_graph = dgl.heterograph(val_edge_dict,
                                         {ntype: self.g.number_of_nodes(ntype) for ntype in set(out_ntypes)})
        test_graph = dgl.heterograph(test_edge_dict,
                                          {ntype: self.g.number_of_nodes(ntype) for ntype in set(out_ntypes)})

        return train_graph, val_graph, test_graph

    def save_results(self, hg, score, file_path):
        with hg.local_scope():
            src_list = []
            dst_list = []
            edge_type_list = []
            for etype in hg.canonical_etypes:
                edges = hg.edges(etype=etype)
                src_id = edges[0]+self.shift_dict[etype[0]]
                dst_id = edges[1]+self.shift_dict[etype[2]]
                src_list.append(src_id)
                dst_list.append(dst_id)
                edge_type_list.append(th.full((src_id.shape[0],), self.test_edge_type[etype[1]]))

            src_list = th.cat(src_list)
            dst_list = th.cat(dst_list)
            edge_type_list = th.cat(edge_type_list)
            with open(file_path, "w") as f:
                for l, r, edge_type, c in zip(src_list, dst_list, edge_type_list,score):
                    f.write(f"{l}\t{r}\t{edge_type}\t{c}\n")


def build_graph_from_triplets(num_nodes, num_rels, triplets):
    """ Create a DGL graph. The graph is bidirectional because RGCN authors
        use reversed relations.
        This function also generates edge type and normalization factor
        (reciprocal of node incoming degree)
    """
    g = dgl.graph(([], []))
    g.add_nodes(num_nodes)
    src, rel, dst = triplets
    src, dst = np.concatenate((src, dst)), np.concatenate((dst, src))
    rel = np.concatenate((rel, rel + num_rels))
    edges = sorted(zip(dst, src, rel))
    dst, src, rel = np.array(edges).transpose()
    g.add_edges(src, dst)
    norm = comp_deg_norm(g)
    print("# nodes: {}, # edges: {}".format(num_nodes, len(src)))
    return g, rel.astype('int64'), norm.astype('int64')


def comp_deg_norm(g):
    g = g.local_var()
    in_deg = g.in_degrees(range(g.number_of_nodes())).float().numpy()
    norm = 1.0 / in_deg
    norm[np.isinf(norm)] = 0
    return norm


@register_dataset('kg_link_prediction')
class KG_LinkPrediction(LinkPredictionDataset):
    def __init__(self, dataset_name):
        super(KG_LinkPrediction, self).__init__()
        if dataset_name in ['wn18', 'FB15k', 'FB15k-237']:
            dataset = load_data(dataset_name)
            self.category = '_N'
            self.num_rels = dataset.num_rels * 2
            # include inverse edge
            self.num_nodes = dataset.num_nodes
            self.homo_g = dataset[0]
            self.g = self.homo_to_hetero(dataset[0])
            #self.g = self.build_g(dataset.train)
            #self.dataset = dataset

    def get_triples_directed(self, mask_mode):
        if mask_mode == 'train_mask':
            data = self.dataset.train
        elif mask_mode == 'val_mask':
            data = self.dataset.test
        elif mask_mode == 'test_mask':
            data = self.dataset.test
        s = th.LongTensor(data[:,0])
        r = th.LongTensor(data[:,1])
        o = th.LongTensor(data[:,2])
        return th.stack([s, r, o])
    def get_triples(self, mask_mode):
        '''
        :param g:
        :param mask_mode: should be one of 'train_mask', 'val_mask', 'test_mask
        :return:
        '''
        g = self.homo_g
        edges = g.edges()
        etype = g.edata['etype']
        mask = g.edata.pop(mask_mode)
        return th.stack((edges[0][mask], etype[mask], edges[1][mask]))

    def homo_to_hetero(self, g):
        edges = g.edges()
        etype = g.edata['etype']
        train_mask = g.edata['train_mask']
        hg = self.build_graph((edges[0][train_mask], edges[1][train_mask]), etype[train_mask])
        return hg
    def build_graph(self, edges, etype):
        edge_dict = {}
        for i in range(self.num_rels):
            mask = (etype==i)
            edge_name = (self.category , str(i), self.category )
            edge_dict[edge_name] = (edges[0][mask], edges[1][mask])
        hg = dgl.heterograph(edge_dict, {self.category: self.num_nodes})
        return hg
    def build_g(self, train):
        s = train[:,0]
        r = train[:,1]
        o = train[:,2]
        edge_dict = {}
        for i in range(self.num_rels):
            mask = (r==i)
            edge_name = (self.category, str(i), self.category )
            edge_dict[edge_name] = (th.LongTensor(s[mask]), th.LongTensor(o[mask]))
        hg = dgl.heterograph(edge_dict, {self.category: self.num_nodes})
        return hg

class kg_sampler():
    def __init__(self,):
        self.sampler = 'uniform'
        return

    def generate_sampled_graph_and_labels(self, triplets, sample_size, split_size,
                                          num_rels, adj_list, degrees,
                                          negative_rate, sampler="uniform"):
        """Get training graph and signals
        First perform edge neighborhood sampling on graph, then perform negative
        sampling to generate negative samples
        """
        # perform edge neighbor sampling
        if self.sampler == "uniform":
            edges = sample_edge_uniform(adj_list, degrees, len(triplets), sample_size)
        elif self.sampler == "neighbor":
            edges = sample_edge_neighborhood(adj_list, degrees, len(triplets), sample_size)
        else:
            raise ValueError("Sampler type must be either 'uniform' or 'neighbor'.")

        # relabel nodes to have consecutive node ids
        edges = triplets[edges]
        src, rel, dst = edges.transpose()
        uniq_v, edges = np.unique((src, dst), return_inverse=True)
        src, dst = np.reshape(edges, (2, -1))
        relabeled_edges = np.stack((src, rel, dst)).transpose()

        # negative sampling
        samples, labels = negative_sampling(relabeled_edges, len(uniq_v),
                                            negative_rate)

        # further split graph, only half of the edges will be used as graph
        # structure, while the rest half is used as unseen positive samples
        split_size = int(sample_size * split_size)
        graph_split_ids = np.random.choice(np.arange(sample_size),
                                           size=split_size, replace=False)
        src = src[graph_split_ids]
        dst = dst[graph_split_ids]
        rel = rel[graph_split_ids]

        # build DGL graph
        print("# sampled nodes: {}".format(len(uniq_v)))
        print("# sampled edges: {}".format(len(src) * 2))
        g, rel, norm = build_graph_from_triplets(len(uniq_v), num_rels,
                                                 (src, rel, dst))
        return g, uniq_v, rel, norm, samples, labels


def sample_edge_neighborhood(adj_list, degrees, n_triplets, sample_size):
    """Sample edges by neighborhool expansion.
    This guarantees that the sampled edges form a connected graph, which
    may help deeper GNNs that require information from more than one hop.
    """
    edges = np.zeros((sample_size), dtype=np.int32)

    #initialize
    sample_counts = np.array([d for d in degrees])
    picked = np.array([False for _ in range(n_triplets)])
    seen = np.array([False for _ in degrees])

    for i in range(0, sample_size):
        weights = sample_counts * seen

        if np.sum(weights) == 0:
            weights = np.ones_like(weights)
            weights[np.where(sample_counts == 0)] = 0

        probabilities = (weights) / np.sum(weights)
        chosen_vertex = np.random.choice(np.arange(degrees.shape[0]),
                                         p=probabilities)
        chosen_adj_list = adj_list[chosen_vertex]
        seen[chosen_vertex] = True

        chosen_edge = np.random.choice(np.arange(chosen_adj_list.shape[0]))
        chosen_edge = chosen_adj_list[chosen_edge]
        edge_number = chosen_edge[0]

        while picked[edge_number]:
            chosen_edge = np.random.choice(np.arange(chosen_adj_list.shape[0]))
            chosen_edge = chosen_adj_list[chosen_edge]
            edge_number = chosen_edge[0]

        edges[i] = edge_number
        other_vertex = chosen_edge[1]
        picked[edge_number] = True
        sample_counts[chosen_vertex] -= 1
        sample_counts[other_vertex] -= 1
        seen[other_vertex] = True

    return edges

def sample_edge_uniform(adj_list, degrees, n_triplets, sample_size):
    """Sample edges uniformly from all the edges."""
    all_edges = np.arange(n_triplets)
    return np.random.choice(all_edges, sample_size, replace=False)