import torch
from torch import nn

from models.archs.arch_util import ConvGnLelu, ExpansionBlock2, ConvGnSilu, ConjoinBlock, MultiConvBlock, \
    FinalUpsampleBlock2x
from models.archs.spinenet_arch import SpineNet
from utils.util import checkpoint


class BasicEmbeddingPyramid(nn.Module):
    def __init__(self, use_norms=True):
        super(BasicEmbeddingPyramid, self).__init__()
        self.initial_process = ConvGnLelu(64, 64, kernel_size=1, bias=True, activation=True, norm=False)
        self.reducers = nn.ModuleList([ConvGnLelu(64, 128, stride=2, kernel_size=1, bias=False, activation=True, norm=False),
                                  ConvGnLelu(128, 128, kernel_size=3, bias=False, activation=True, norm=use_norms),
                                  ConvGnLelu(128, 256, stride=2, kernel_size=1, bias=False, activation=True, norm=False),
                                  ConvGnLelu(256, 256, kernel_size=3, bias=False, activation=True, norm=use_norms)])
        self.expanders = nn.ModuleList([ExpansionBlock2(256, 128, block=ConvGnLelu),
                                   ExpansionBlock2(128, 64, block=ConvGnLelu)])
        self.embedding_processor1 = ConvGnSilu(256, 128, kernel_size=1, bias=True, activation=True, norm=False)
        self.embedding_joiner1 = ConjoinBlock(128, block=ConvGnLelu, norm=use_norms)
        self.embedding_processor2 = ConvGnSilu(256, 256, kernel_size=1, bias=True, activation=True, norm=False)
        self.embedding_joiner2 = ConjoinBlock(256, block=ConvGnLelu, norm=use_norms)

        self.final_process = nn.Sequential(ConvGnLelu(128, 96, kernel_size=1, bias=False, activation=False, norm=False,
                                                      weight_init_factor=.1),
                                           ConvGnLelu(96, 64, kernel_size=1, bias=False, activation=False, norm=False,
                                                      weight_init_factor=.1),
                                           ConvGnLelu(64, 64, kernel_size=1, bias=False, activation=False, norm=False,
                                                      weight_init_factor=.1),
                                           ConvGnLelu(64, 64, kernel_size=1, bias=False, activation=False, norm=False,
                                                      weight_init_factor=.1))

    def forward(self, x, *embeddings):
        p = self.initial_process(x)
        identities = []
        for i in range(2):
            identities.append(p)
            p = self.reducers[i*2](p)
            p = self.reducers[i*2+1](p)
            if i == 0:
                p = self.embedding_joiner1(p, self.embedding_processor1(embeddings[0]))
            elif i == 1:
                p = self.embedding_joiner2(p, self.embedding_processor2(embeddings[1]))
        for i in range(2):
            p = self.expanders[i](p, identities[-(i+1)])
        x = self.final_process(torch.cat([x, p], dim=1))
        return x


class ChainedEmbeddingGen(nn.Module):
    def __init__(self):
        super(ChainedEmbeddingGen, self).__init__()
        self.initial_conv = ConvGnLelu(3, 64, kernel_size=7, bias=True, norm=False, activation=False)
        self.spine = SpineNet(arch='49', output_level=[3, 4], double_reduce_early=False)
        self.blocks = nn.ModuleList([BasicEmbeddingPyramid() for i in range(5)])
        self.upsample = FinalUpsampleBlock2x(64)

    def forward(self, x):
        emb = checkpoint(self.spine, x)
        fea = self.initial_conv(x)
        for block in self.blocks:
            fea = fea + checkpoint(block, fea, *emb)
        return checkpoint(self.upsample, fea),