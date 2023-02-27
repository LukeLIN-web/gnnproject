from torch_geometric.datasets import Reddit,Yelp,AmazonProducts
from ogb.nodeproppred import PygNodePropPredDataset

def get_dataset(name, root, use_sparse_tensor=False, bf16=False):
    if name == 'Reddit':
        dataset = Reddit(root + 'Reddit')
    elif name == 'Yelp':
        dataset = Yelp(root + 'Yelp')
    elif name == 'AmazonProducts':
        dataset = AmazonProducts(root + 'AmazonProducts')
    elif name == 'ogbn-products':
        dataset = PygNodePropPredDataset(name = "ogbn-products",root=root)
    else:
        raise NotImplementedError
    return dataset