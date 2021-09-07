import dgl
import dgl.function as fn
import torch as th
import numpy as np
from dgl.data.rdf import AIFBDataset, MUTAGDataset, BGSDataset, AMDataset
from dgl.data.utils import load_graphs, save_graphs
from ogb.nodeproppred import DglNodePropPredDataset
from . import load_acm_raw
from . import BaseDataset, register_dataset
from . import AcademicDataset, HGBDataset


@register_dataset('node_classification')
class NodeClassificationDataset(BaseDataset):
    r"""
    Description
    -----------
    The class *NodeClassificationDataset* is a base class for datasets which can be used in task *node classification*.
    So its subclass should contain attributes such as graph, category, num_classes and so on.
    Besides, it should implement the functions *get_labels()* and *get_idx()*.

    Attributes
    -------------
    g : dgl.DGLHeteroGraph
        The heterogeneous graph.
    category : str
        The category(or target) node type need to be predict. In general, we predict only one node type.
    num_classes : int
        The target node  will be classified into num_classes categories.
    has_feature : bool
        Whether the dataset has feature. Default ``False``.
    """

    def __init__(self):
        super(NodeClassificationDataset, self).__init__()
        self.g = None
        self.category = None
        self.num_classes = None
        self.has_feature = False
        # self.in_dim = None

    def get_labels(self):
        r"""
        Description
        ------------
        The subclass of dataset should overwrite the function. We can get labels of target node.

        return
        -------
        labels : torch.Tensor
        """
        raise NotImplemented

    def get_idx(self, ):
        r"""
        Description
        ------------
        The subclass of dataset should overwrite the function. We can get idx of train, validation and test through it.

        return
        -------
        train_idx, val_idx, test_idx : torch.Tensor
        """
        raise NotImplemented


@register_dataset('rdf_node_classification')
class RDF_NodeClassification(NodeClassificationDataset):
    r"""
    Description
    ------------
    The RDF dataset will be used in task *entity classification*.
    It contains AIFB/MUTAG/MUTAG/BGS.
    And we download from dgl and process it.

    So if you want to get more information, refer to
    `RDF datasets <https://docs.dgl.ai/api/python/dgl.data.html#rdf-datasets>`_
    """
    def __init__(self, dataset_name):
        super(RDF_NodeClassification, self).__init__()
        self.g, self.category, self.num_classes = self.load_RDF_dgl(dataset_name)
        self.has_feature = False

    def load_RDF_dgl(self, dataset):
        # load graph data
        if dataset == 'aifb':
            kg_dataset = AIFBDataset()
        elif dataset == 'mutag':
            kg_dataset = MUTAGDataset()
        elif dataset == 'bgs':
            kg_dataset = BGSDataset()
        elif dataset == 'am':
            kg_dataset = AMDataset()
        else:
            raise ValueError()

        # Load from hetero-graph
        kg = kg_dataset[0]
        category = kg_dataset.predict_category
        num_classes = kg_dataset.num_classes
        return kg, category, num_classes

    def get_idx(self, validation=True):
        train_mask = self.g.nodes[self.category].data.pop('train_mask')
        test_mask = self.g.nodes[self.category].data.pop('test_mask')
        train_idx = th.nonzero(train_mask, as_tuple=False).squeeze()
        test_idx = th.nonzero(test_mask, as_tuple=False).squeeze()
        if validation:
            val_idx = train_idx[:len(train_idx) // 5]
            train_idx = train_idx[len(train_idx) // 5:]
        else:
            val_idx = train_idx
            train_idx = train_idx
        return train_idx, val_idx, test_idx

    def get_labels(self):
        if 'labels' in self.g.nodes[self.category].data:
            labels = self.g.nodes[self.category].data.pop('labels')
        else:
            raise ValueError('label in not in the hg.nodes[category].data')
        return labels


@register_dataset('hin_node_classification')
class HIN_NodeClassification(NodeClassificationDataset):
    r"""
    Description
    ------------
    The HGB dataset are all used in different papers. So we preprocess them and store them as form of dgl.DGLHeteroGraph.
    The dataset name combined with paper name through 4(for).



    Dataset Name
    ------------
    acm4NSHE/acm4GTN/acm4NARS/
    acm_han_raw/academic4HetGNN/dblp4MAGNN/imdb4MAGNN/...
    """
    def __init__(self, dataset_name):
        super(HIN_NodeClassification, self).__init__()
        self.g, self.category, self.num_classes = self.load_HIN(dataset_name)

    def load_HIN(self, name_dataset):
        if name_dataset == 'acm4NSHE':
            dataset = AcademicDataset(name='acm4NSHE', raw_dir='')
            category = 'paper'
            g = dataset[0].long()
            num_classes = 3
            self.in_dim = g.ndata['h'][category].shape[1]
        elif name_dataset == 'dblp':
            data_path = './openhgnn/dataset/dblp_graph.bin'
            category = 'author'
            num_classes = 4
            g, _ = load_graphs(data_path)
            g = g[0].long()
            self.in_dim = g.ndata['h'][category].shape[1]
        elif name_dataset == 'dblp4MAGNN':
            dataset = AcademicDataset(name='dblp4MAGNN', raw_dir='')
            category = 'A'
            g = dataset[0].long()
            num_classes = 4
            self.in_dim = g.ndata['feat'][category].shape[1]

        elif name_dataset == 'imdb4MAGNN':
            dataset = AcademicDataset(name='imdb4MAGNN', raw_dir='')
            category = 'M'
            g = dataset[0].long()
            num_classes = 3
            self.in_dim = g.ndata['feat'][category].shape[1]
        elif name_dataset == 'imdb4GTN':
            dataset = AcademicDataset(name='imdb4GTN', raw_dir='')
            category = 'movie'
            g = dataset[0].long()
            num_classes = 3
            self.in_dim = g.ndata['h'][category].shape[1]
        elif name_dataset == 'acm4GTN':
            dataset = AcademicDataset(name='acm4GTN', raw_dir='')
            category = 'paper'
            g = dataset[0].long()
            num_classes = 3
            self.in_dim = g.ndata['h'][category].shape[1]
        elif name_dataset == 'acm4NARS':
            dataset = AcademicDataset(name='acm4NARS', raw_dir='')
            g = dataset[0].long()
            num_classes = 3
            # g, labels, num_classes, train_nid, val_nid, test_nid = load_acm_nars()
            category = 'paper'
        elif name_dataset == 'academic4HetGNN':
            # which is used in HetGNN
            dataset = AcademicDataset(name='academic4HetGNN', raw_dir='')
            category = 'author'
            g = dataset[0].long()
            num_classes = 4
        elif name_dataset in ['acm_han', 'acm_han_raw']:
            if name_dataset == 'acm_han':
                pass
            elif name_dataset == 'acm_han_raw':
                g, category, num_classes, self.in_dim = load_acm_raw(False)
            else:
                return NotImplementedError('Unsupported dataset {}'.format(name_dataset))
            return g, category, num_classes
        elif name_dataset in ['demo']:
            data_path = './openhgnn/dataset/graph.bin'
            category = 'author'
            num_classes = 4
            g, _ = load_graphs(data_path)
            g = g[0].long()
            self.in_dim = g.ndata['h'][category].shape[1]
        # g, _ = load_graphs(data_path)
        # g = g[0]
        return g, category, num_classes

    def get_idx(self, validation=True):
        if 'train_mask' not in self.g.nodes[self.category].data:
            num_nodes = self.g.number_of_nodes(self.category)

            n_test = int(num_nodes * 0.2)
            n_train = num_nodes - n_test

            train, test = th.utils.data.random_split(range(num_nodes), [n_train, n_test])
            train_idx = th.tensor(train.indices)
            test_idx = th.tensor(test.indices)
            if validation:
                val_idx = train_idx[:len(train_idx) // 10]
                train_idx = train_idx[len(train_idx) // 10:]
            else:
                val_idx = train_idx
                train_idx = train_idx
        else:
            train_mask = self.g.nodes[self.category].data.pop('train_mask')
            test_mask = self.g.nodes[self.category].data.pop('test_mask')
            train_idx = th.nonzero(train_mask, as_tuple=False).squeeze()
            test_idx = th.nonzero(test_mask, as_tuple=False).squeeze()
            if validation:
                if 'val_mask' in self.g.nodes[self.category].data:
                    val_mask = self.g.nodes[self.category].data.pop('val_mask')
                    val_idx = th.nonzero(val_mask, as_tuple=False).squeeze()
                    pass
                else:
                    val_idx = train_idx[:len(train_idx) // 10]
                    train_idx = train_idx[len(train_idx) // 10:]
            else:
                val_idx = train_idx
                train_idx = train_idx
        return train_idx, val_idx, test_idx

    def get_labels(self):
        if 'labels' in self.g.nodes[self.category].data:
            labels = self.g.nodes[self.category].data.pop('labels').long()
        elif 'label' in self.g.nodes[self.category].data:
            labels = self.g.nodes[self.category].data.pop('label').long()
        else:
            raise ValueError('label in not in the hg.nodes[category].data')
        return labels


@register_dataset('HGBn_node_classification')
class HGB_NodeClassification(NodeClassificationDataset):
    r"""
    Description
    ------------
    The HGB dataset will be used in task *node classification*.
    And we download from dgl and process it.

    Dataset Name
    ------------
    HGBn-ACM/HGBn-DBLP/HGBn-Freebase/HGBn-IMDB

    So if you want to get more information, refer to
    `HGB datasets <https://github.com/THUDM/HGB>`_
    """
    def __init__(self, dataset_name):
        super(HGB_NodeClassification, self).__init__()
        self.dataset_name = dataset_name
        self.has_feature = True
        if dataset_name == 'HGBn-ACM':
            dataset = HGBDataset(name=dataset_name, raw_dir='')
            g = dataset[0].long()
            category = 'paper'
            num_classes = 4
            g.nodes['term'].data['h'] = th.eye(g.number_of_nodes('term'))
            self.in_dim = g.ndata['h'][category].shape[1]
            # graph: dgl graph object, label: torch tensor of shape (num_nodes, num_tasks)
            self.meta_paths = [(('paper', 'paper-author', 'author'), ('author', 'author-paper', 'paper')),
                               (('paper', 'paper-subject', 'subject'), ('subject', 'subject-paper', 'paper')),
                               (('paper', 'paper-term', 'term'), ('term', 'term-paper', 'paper'))]

        elif dataset_name == 'HGBn-DBLP':
            dataset = HGBDataset(name=dataset_name, raw_dir='')
            g = dataset[0].long()
            category = 'author'
            num_classes = 4
            g.nodes['venue'].data['h'] = th.eye(g.number_of_nodes('venue'))
            self.in_dim = g.ndata['h'][category].shape[1]
            self.meta_paths = [(('author', 'author-paper', 'paper'), ('paper', 'paper-author', 'author')),
                               (('author', 'author-paper', 'paper'), ('paper', 'paper-term', 'term'),
                                ('term', 'term-paper', 'paper'), ('paper', 'paper-author', 'author')),
                               (('author', 'author-paper', 'paper'), ('paper', 'paper-venue', 'venue'),
                                ('venue', 'venue-paper', 'paper'), ('paper', 'paper-author', 'author')),
                               ]
            # graph: dgl graph object, label: torch tensor of shape (num_nodes, num_tasks)
        elif dataset_name == 'HGBn-Freebase':
            dataset = HGBDataset(name=dataset_name, raw_dir='')
            g = dataset[0].long()
            category = 'BOOK'
            num_classes = 8
            self.has_feature = False
            self.meta_paths = [(('BOOK', 'BOOK-about-ORGANIZATION', 'ORGANIZATION'),
                                ('ORGANIZATION', 'ORGANIZATION-to-MUSIC', 'MUSIC'),
                                ('MUSIC', 'MUSIC-in-BOOK', 'BOOK')),
                               (('BOOK', 'BOOK-about-ORGANIZATION', 'ORGANIZATION'),
                                ('ORGANIZATION', 'ORGANIZATION-for-BUSINESS', 'BUSINESS'),
                                ('BUSINESS', 'BUSINESS-about-BOOK', 'BOOK'))]

            #self.in_dim = g.ndata['h'][category].shape[1]
            # graph: dgl graph object, label: torch tensor of shape (num_nodes, num_tasks)
        elif dataset_name == 'HGBn-IMDB':
            dataset = HGBDataset(name=dataset_name, raw_dir='')
            g = dataset[0].long()
            category = 'movie'
            num_classes = 5
            g.nodes['keyword'].data['h'] = th.eye(g.number_of_nodes('keyword'))
            self.in_dim = g.ndata['h'][category].shape[1]
            self.meta_paths = [(('movie', 'movie->actor', 'actor'), ('actor', 'actor->movie', 'movie')),
                               (('movie', 'movie->director', 'director'), ('director', 'director->movie', 'movie')),
                               (('movie', 'movie->keyword', 'keyword'), ('keyword', 'keyword->movie', 'movie'))]
            # RuntimeError: result type Float can't be cast to the desired output type Long
            self.multi_label = True
        else:
            raise ValueError
        self.g, self.category, self.num_classes = g, category, num_classes

    def get_idx(self, validation=True):
        if 'train_mask' not in self.g.nodes[self.category].data:
            num_nodes = self.g.number_of_nodes(self.category)

            n_test = int(num_nodes * 0.2)
            n_train = num_nodes - n_test

            train, test = th.utils.data.random_split(range(num_nodes), [n_train, n_test])
            train_idx = th.tensor(train.indices)
            test_idx = th.tensor(test.indices)
            if validation:
                valid_idx = train_idx[:len(train_idx) // 10]
                train_idx = train_idx[len(train_idx) // 10:]
            else:
                valid_idx = train_idx
                train_idx = train_idx
        else:
            train_mask = self.g.nodes[self.category].data.pop('train_mask')
            test_mask = self.g.nodes[self.category].data.pop('test_mask')
            train_idx = th.nonzero(train_mask, as_tuple=False).squeeze()
            test_idx = th.nonzero(test_mask, as_tuple=False).squeeze()
            if validation:
                if 'val_mask' in self.g.nodes[self.category].data:
                    val_mask = self.g.nodes[self.category].data.pop('val_mask')
                    valid_idx = th.nonzero(val_mask, as_tuple=False).squeeze()
                    pass
                else:
                    valid_idx = train_idx[:len(train_idx) // 5]
                    train_idx = train_idx[len(train_idx) // 5:]
            else:
                valid_idx = train_idx
                train_idx = train_idx
        self.train_idx = train_idx
        self.valid_idx = valid_idx
        self.test_idx = test_idx
        return self.train_idx, self.valid_idx, self.test_idx

    def get_labels(self):
        # RuntimeError: Expected object of scalar type Long but got scalar type Float for argument #2 'target' in call to _thnn_nll_loss_forward
        if 'labels' in self.g.nodes[self.category].data:
            labels = self.g.nodes[self.category].data.pop('labels').long()
        elif 'label' in self.g.nodes[self.category].data:
            labels = self.g.nodes[self.category].data.pop('label').long()
        else:
            raise ValueError('label in not in the hg.nodes[category].data')
        self.labels = labels.float() if self.dataset_name == 'HGBn-IMDB' else labels
        return self.labels

    def save_results(self, logits, file_path):
        test_logits = logits[self.test_idx]
        if self.dataset_name == 'HGBn-IMDB':
            pred = (test_logits.cpu().numpy() > 0).astype(int)
            multi_label = []
            for i in range(pred.shape[0]):
                label_list = [str(j) for j in range(pred[i].shape[0]) if pred[i][j] == 1]
                multi_label.append(','.join(label_list))
            pred = multi_label
        elif self.dataset_name in ['HGBn-ACM', 'HGBn-DBLP', 'HGBn-Freebase']:
            pred = test_logits.cpu().numpy().argmax(axis=1)
            pred = np.array(pred)
        else:
            return
        with open(file_path, "w") as f:
            for nid, l in zip(self.test_idx, pred):
                f.write(f"{nid}\t\t{0}\t{l}\n")


@register_dataset('ogbn_node_classification')
class OGB_NodeClassification(NodeClassificationDataset):
    def __init__(self, dataset_name):
        super(OGB_NodeClassification, self).__init__()
        if dataset_name == 'ogbn-mag':
            dataset = DglNodePropPredDataset(name='ogbn-mag')
            self.category = 'paper'  # graph: dgl graph object, label: torch tensor of shape (num_nodes, num_tasks)
        else:
            raise ValueError

        split_idx = dataset.get_idx_split()
        self.num_classes = dataset.num_classes
        self.train_idx, self.valid_idx, self.test_idx = split_idx["train"][self.category], split_idx["valid"][
            self.category], split_idx["test"][self.category]
        self.g, self.label_dict = dataset[0]
        self.g = self.mag4HGT(self.g)
        self.label = self.label_dict[self.category].squeeze(dim=-1)
        # 2-dim label
        self.in_dim = self.g.ndata['h'][self.category].shape[1]
        self.has_feature = True
        # pass

    def get_idx(self, validation=True):
        return self.train_idx, self.valid_idx, self.test_idx

    def get_labels(self):
        return self.label

    def mag4HGT(self, hg):
        # Add reverse edge types

        edges = {etype: hg.edges(etype=etype) for etype in hg.canonical_etypes}
        edges.update({(v, e + '_inv', u): (dst, src) for (u, e, v), (src, dst) in edges.items()})
        hg2 = dgl.heterograph(edges)
        hg2 = dgl.to_simple(hg2)

        # Initialize year
        hg2.nodes['paper'].data['timestamp'] = hg.nodes['paper'].data['year'].squeeze()
        for ntype in hg.ntypes:
            if ntype != 'paper':
                hg2.nodes[ntype].data['timestamp'] = th.zeros(hg2.num_nodes(ntype), dtype=th.int64)

        # Aggregate bag-of-paper features
        hg2.nodes['paper'].data['h'] = hg.nodes['paper'].data['feat']
        hg2.update_all(fn.copy_u('h', 'm'), fn.mean('m', 'h'), etype='has_topic')  # field_of_study
        hg2.update_all(fn.copy_u('h', 'm'), fn.mean('m', 'h'), etype='writes_inv')  # author
        hg2.update_all(fn.copy_u('h', 'm'), fn.mean('m', 'h'), etype='affiliated_with')  # institution

        # Attach log-degree to feature of each node type
        for ntype in hg2.ntypes:
            hg2.nodes[ntype].data['deg'] = th.zeros(hg2.num_nodes(ntype))
        for utype, etype, vtype in hg2.canonical_etypes:
            hg2.nodes[vtype].data['deg'] += hg2.in_degrees(etype=etype)
        for ntype in hg2.ntypes:
            hg2.nodes[ntype].data['h'] = th.cat([
                hg2.nodes[ntype].data['h'],
                th.log10(hg2.nodes[ntype].data['deg'][:, None])], 1)
            del hg2.nodes[ntype].data['deg']

        return hg2
