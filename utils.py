"""Common functions you may find useful in your implementation."""
import os
import json
import random
import torch
import torch.nn as nn
import numpy as np
from collections import OrderedDict


EPS = 1e-7


def assert_eq(real, expected):
    assert real == expected, '%s (true) vs %s (expected)' % (real, expected)


def tensor_eq(t1, t2):
    if t1.size() != t2.size():
        print('Warning: size mismatch', t1.size(), 'vs', t2.size())
        return False

    t1 = t1.cpu().numpy()
    t2 = t2.cpu().numpy()
    diff = abs(t1 - t2)
    eq = (diff < 1e-5).all()
    return eq


def assert_zero_grads(params):
    for p in params:
        if p.grad is not None:
            assert_eq(p.grad.data.sum(), 0)


def assert_frozen(module):
    for p in module.parameters():
        assert not p.requires_grad


def weights_init(m):
    """custom weights initialization"""
    if isinstance(m, nn.Linear) or isinstance(m, nn.Conv2d):
        # nn.init.kaiming_normal(m.weight.data)
        nn.init.orthogonal(m.weight.data)
    else:
        print('%s is not custom-initialized.' % m.__class__)


def init_net(net, net_file):
    if net_file:
        net.load_state_dict(torch.load(net_file))
    else:
        net.apply(weights_init)


def count_output_size(input_shape, module):
    fake_input = torch.FloatTensor(*input_shape)
    output_size = module.forward(fake_input).view(-1).size()[0]
    return output_size


def one_hot(x, n):
    assert x.dim() == 2
    one_hot_x = torch.zeros(x.size(0), n).cuda()
    one_hot_x.scatter_(1, x, 1)
    return one_hot_x


def large_randint():
    return random.randint(int(1e4), int(1e6))


def set_all_seeds(rand_seed):
    random.seed(rand_seed)
    np.random.seed(large_randint())
    torch.manual_seed(large_randint())
    torch.cuda.manual_seed(large_randint())


def num2str(n):
    if n < 1e3:
        s = str(n)
        unit = ''
    elif n < 1e6:
        n /= 1e3
        s = '%.3f' % n
        unit = 'K'
    else:
        n /= 1e6
        s = '%.3f' % n
        unit = 'M'

    s = s.rstrip('0').rstrip('.')
    return s + unit


class Config:
    """helper class to handle configs

    train_config, eval_config etc."""

    def __init__(self, attrs):
        self.__dict__.update(attrs)

    @classmethod
    def load(cls, filename):
        with open(filename, 'r') as f:
            attrs = json.load(f)
        return cls(attrs)

    def dump(self, filename):
        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        print('Results will be stored in:', dirname)

        with open(filename, 'w') as f:
            json.dump(vars(self), f, sort_keys=True, indent=2)
            f.write('\n')

    def __repr__(self):
        return json.dumps(vars(self), sort_keys=True, indent=2)


class Logger(object):
    """helper class to handle logging issue"""

    def __init__(self, output_name):
        self.log_file = open(output_name, 'w')
        self.infos = OrderedDict()

    def append(self, key, val):
        vals = self.infos.setdefault(key, [])
        vals.append(val)

    def log(self, *, delimiter='\n'):
        msgs = []
        for key, vals in self.infos.items():
            if isinstance(vals, list):
                vals = torch.tensor(vals)
            msgs.append("%s %.6f" % (key, vals.mean().item()))
        msg = delimiter.join(msgs)
        self.log_file.write(msg + '\n')
        self.log_file.flush()
        self.infos = OrderedDict()
        print(msg)

    def write(self, msg):
        self.log_file.write(msg + '\n')
        self.log_file.flush()
        print(msg)
