from torch import Tensor
from typing import List
from torch_geometric.loader import NeighborSampler
import torch
from sampler.get_micro_batch import *


def test_get_micro_batch():
    # three hop
    edge_index = torch.tensor([[0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 6, 6, 6, 7, 7, 7, 8, 8, 8, 9, 9, 9],
                               [1, 6, 0, 2, 6, 1, 3, 7, 2, 4, 8, 3, 5, 9, 4, 9, 0, 1, 7, 2, 6, 8, 3, 7, 9, 4, 5, 8]], dtype=torch.long)
    x = Tensor([[1,2], [2,3], [3,3], [4,3], [5,3], [6,3], [7,3], [8,3], [9,3], [10,3]])
    hop = [-1, -1, -1]
    train_loader = NeighborSampler(edge_index,
                                   sizes=hop, batch_size=4,
                                   shuffle=False, num_workers=0)
    num_features, hidden_size, num_classes = 2, 16, 1
    model = SAGE(num_features, hidden_size, num_classes, num_layers=3)
    for batch_size, n_id, adjs in train_loader:
        out = model(x[n_id], adjs)
        num_micro_batch = 4
        micro_batchs = get_micro_batch(adjs,
                                       n_id,
                                       batch_size, num_micro_batch)
        subgraphout = []
        for micro_batch in micro_batchs:
            subgraphout.append(
                model(x[n_id][micro_batch.nid], micro_batch.adjs))
        subgraphout = torch.cat(subgraphout, 0)
        assert torch.abs((out - subgraphout).mean()) < 0.01
