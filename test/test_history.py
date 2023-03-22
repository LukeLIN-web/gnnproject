import torch
from torch_geometric.loader import NeighborSampler

from microGNN import History
from microGNN.models import ScaleSAGE
from microGNN.prune import prune, prune_computation_graph
from microGNN.utils import get_nano_batch
from microGNN.utils.common_class import Adj, Nanobatch

# yapf: disable
edge_index = torch.tensor([[0, 0, 1, 1, 2, 2, 6, 7],
                           [1, 6, 0, 2, 1, 7, 0, 2]], dtype=torch.long)

x = torch.tensor([[0, 0], [1, 1], [2, 2], [3, 3], [4, 4], [5, 5], [6, 6], # noqa
                  [8, 3], [9, 3], [10, 3]],dtype=torch.float) # noqa
# yapf: enable


# sample and then get nano batch,
# then forward nano batch, get what node has be calculated ,return them.
def test_load_embedding():
    histories = torch.nn.ModuleList([History(5, 2, 'cpu') for _ in range(1)])
    histories[0].emb[3] = torch.tensor([3.2, 0.2])
    histories[0].emb[2] = torch.tensor([2.2, 2.3])
    histories[0].cached_nodes = torch.tensor([False, False, True, True, False])
    nb = Nanobatch(torch.tensor([0, 1, 2, 3, 4]), 5, [
        Adj(torch.tensor([[1, 2, 3, 4], [0, 0, 1, 2]]), None, (5, )),
        Adj(torch.tensor([[1, 2], [0, 0]]), None, (3, 1))
    ])
    pruned_adjs = prune_computation_graph(nb, histories)
    assert pruned_adjs[0].edge_index.tolist() == [[1, 2, 3], [0, 0, 1]]
    assert pruned_adjs[1].edge_index.tolist() == [[1, 2], [0, 0]]
    torch.manual_seed(0)
    hop = [-1, -1]
    num_layers = len(hop)
    num_hidden = 2
    n_id = torch.tensor([0, 1, 2, 3, 4, 5, 6, 7])
    model = ScaleSAGE(in_channels=2,
                      hidden_channels=num_hidden,
                      out_channels=2,
                      num_layers=num_layers)
    x = torch.tensor([[0, 0], [1, 1], [2, 2], [3, 3], [4, 4]],
                     dtype=torch.float)  # noqa
    model.eval()
    model(x, pruned_adjs, n_id, histories)


# sample and then get nano batch,
# then forward nano batch, save the embedding of the node in the nano batch
def test_save_embedding():
    hop = [-1, -1]
    num_layers = len(hop)
    train_loader = NeighborSampler(
        edge_index,
        sizes=hop,
        batch_size=2,
        shuffle=False,
        drop_last=True,
    )
    num_hidden = 2
    torch.manual_seed(0)
    batch_size, n_id, adjs = next(iter(train_loader))
    model = ScaleSAGE(in_channels=2,
                      hidden_channels=num_hidden,
                      out_channels=2,
                      num_layers=num_layers)
    model.eval()
    nano_batchs = get_nano_batch(adjs,
                                 n_id,
                                 batch_size,
                                 num_nano_batch=2,
                                 relabel_nodes=True)
    histories = torch.nn.ModuleList(
        [History(len(n_id), num_hidden, 'cpu') for _ in range(num_layers - 1)])
    nb = nano_batchs[0]
    model(x[n_id][nb.n_id], nb.adjs, nb.n_id, histories)
    assert torch.equal(histories[0].emb[3],
                       torch.tensor([0.0, 0.0]))  # node 2 don't save
    assert torch.equal(histories[0].cached_nodes,
                       torch.tensor([True, True, True, False, False]))
    histories[0].reset_parameters()

    nb = nano_batchs[1]
    model(x[n_id][nb.n_id], nb.adjs, nb.n_id, histories)
    assert torch.equal(histories[0].emb[2],
                       torch.tensor([0.0, 0.0]))  # node 6 don't save
    assert torch.equal(histories[0].cached_nodes,
                       torch.tensor([True, True, False, True, False]))


def test_prune():
    edge1 = torch.tensor([[3, 4], [2, 2]])
    adjs1 = Adj(edge1, None, (3, 1))
    edge2 = torch.tensor([[3, 4, 6, 7, 5, 8], [2, 2, 3, 3, 4, 4]])
    adjs2 = Adj(edge2, None, (7, 3))
    adjs = [adjs2, adjs1]  # hop2会排序吗? 不一定. 不过hop1节点都在hop2前面
    target_node = torch.tensor([2])

    cached_nodes = torch.tensor([[3], [4]])  # target node, 1hop, 2hop ...
    sub_n_id, sub_adjs = prune(target_node, adjs, cached_nodes)
    assert torch.equal(sub_n_id, torch.tensor([2, 3, 4, 6, 7]))
    assert torch.equal(
        sub_adjs[1].edge_index,
        torch.tensor([[3, 4, 6, 7, 5, 8], [2, 2, 3, 3, 4, 4]]),
    )
    assert torch.equal(sub_adjs[0].edge_index, torch.tensor([[3, 4], [2, 2]]))


if __name__ == "__main__":
    # test_prune()
    test_save_embedding()
    # test_load_embedding()
