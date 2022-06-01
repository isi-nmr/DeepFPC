import math

import numpy as np
import torch
from matplotlib import pyplot as plt
from torch import nn
import pytorch_lightning as pl


class ConvNet(torch.nn.Module):
    def __init__(self, depth, batch, outsize):
        super().__init__()
        layers = []
        init = torch.nn.Sequential(torch.nn.Dropout(0.2),
            torch.nn.Conv1d(2, 16, 5, stride=2), torch.nn.ReLU(),
            torch.nn.Conv1d(16, 24, 3, stride=2), torch.nn.ReLU())
        layers.append(init)
        inc = 24
        for i in range(0, depth):
            outc = inc + 8
            if batch == False:
                temp = torch.nn.Sequential(torch.nn.Conv1d(inc, outc, 3, stride=2), torch.nn.ReLU())
            else:
                temp = torch.nn.Sequential(torch.nn.Conv1d(inc, outc, 3, stride=2), torch.nn.BatchNorm1d(outc),
                                           torch.nn.ReLU())
            layers.append(temp)
            inc = outc
        layers.append(torch.nn.Flatten())
        self.encoder = torch.nn.Sequential(*layers)
        self.reg = torch.nn.Sequential(
                torch.nn.LazyLinear(outsize))
        # self.reg = torch.nn.Sequential(
        #         torch.nn.LazyLinear(256), torch.nn.ReLU(),
        #         torch.nn.Linear(256, 128),
        #         torch.nn.ReLU(),
        #         torch.nn.Linear(128, 64),  torch.nn.ReLU(),
        #         torch.nn.Dropout(0.2),torch.nn.Linear(64, outsize))

    def forward(self,x):
        x = self.encoder(x)
        x = self.reg(x)
        return x
class MLPNet(torch.nn.Module):
    def __init__(self, depth, batch, outsize):
        super().__init__()
        layers = []
        init = torch.nn.Sequential(torch.nn.Dropout(0.2),
            torch.nn.LazyLinear(512), torch.nn.ReLU())
        layers.append(init)
        inc = 512
        for i in range(0, depth):
            outc = int(inc/2*(i+1))
            if batch == False:
                temp = torch.nn.Sequential(torch.nn.Linear(inc,outc), torch.nn.ReLU())
            else:
                temp = torch.nn.Sequential(torch.nn.Linear(inc,outc), torch.nn.ReLU(), torch.nn.BatchNorm1d(outc),
                                           torch.nn.ReLU())
            layers.append(temp)
            inc = outc
        # layers.append(torch.nn.Flatten())
        self.encoder = torch.nn.Sequential(*layers)
        self.reg = torch.nn.Sequential(torch.nn.Flatten(),
                torch.nn.LazyLinear(outsize))

    def forward(self,x):
        x = x.permute(0, 2, 1)
        x = self.encoder(x)
        x = x.permute(0, 1, 2)
        x = self.reg(x)
        return x
class FC_tiny(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = torch.nn.Sequential(
            torch.nn.LazyLinear(64), torch.nn.ReLU(),
            torch.nn.Dropout(0.2), torch.nn.Linear(64, 1))
    def forward(self,x):
        x = self.encoder(x)
        return x


# %% creating model
class Encoder_Model(pl.LightningModule):


    def __init__(self, depth,param):
        super().__init__()
        self.criterion = torch.nn.MSELoss(reduction='sum')
        self.signal = torch.from_numpy(param.refsignal.astype('complex64')).cuda()
        self.relu = torch.nn.ReLU6()
        self.sigmoid = torch.nn.Sigmoid()
        self.param = param
        self.met = []
        self.t = torch.from_numpy(param.t).float().cuda()
        if param.basisset is not None:
            self.basis = torch.from_numpy(param.basisset[0:2048, 0:param.numOfSig].astype('complex64')).cuda()
        self.criterion = torch.nn.MSELoss(reduction='sum')
        self.tr = nn.Parameter(torch.tensor(0.004).cuda(), requires_grad=True)
        self.act = nn.ReLU()
        self.lact = nn.ReLU6()
        self.sigm = nn.Sigmoid()
        self.model = None
        if param.enc_type == 'conv_simple':
            self.model = ConvNet
        if param.enc_type == 'mlp_simple':
            self.model = MLPNet

        if self.param.BG == True:
            self.encoder = self.model(depth, param.parameters['banorm'], 4)
            # self.encBG = FC_tiny()
        else:
            self.encoder = self.model(depth, param.parameters['banorm'], 4)


        if param.parameters['MM_model'] == "lorntz":
            self.MM_model = self.Lornz
        if param.parameters['MM_model'] == "gauss":
            self.MM_model = self.Gauss
        if param.type == 'dCr':
            self.decoder = self.dCr
        if 'dSR' in self.param.type:
            self.decoder = self.dSR
            self.signal = torch.from_numpy(param.dSR_refsignal.astype('complex64')).cuda()
        self.p1=1
        self.p2=self.param.truncSigLen
        if param.parameters['fbound'][0]:
            self.p1 = self.param.ppm2p(param.parameters['fbound'][2], param.truncSigLen)
            self.p2 = self.param.ppm2p(param.parameters['fbound'][1], param.truncSigLen)



    def sign(self, t, eps):
        return (t / torch.sqrt(t ** 2 + eps))

    def Gauss(self, ampl, f, d, ph, Crfr, Cra, Crd):
        return (Cra * ampl) * torch.multiply(torch.multiply(torch.exp(ph * 1j),
                                                            torch.exp(-2 * math.pi * ((f + Crfr)) * self.t.T * 1j)),
                                             torch.exp(-(d + Crd) * self.t.T * self.t.T))

    def Lornz(self, ampl, f, d, ph, Crfr, Cra, Crd):
        return (Cra * ampl) * torch.multiply(torch.multiply(torch.exp(ph * 1j),
                                                            torch.exp(-2 * math.pi * ((f + Crfr)) * self.t.T * 1j)),
                                             torch.exp(-(d + Crd) * self.t.T))

    def Voigt(self, ampl, f, dl, dg, ph, Crfr, Cra, Crd):
        return (Cra + ampl) * torch.multiply(torch.multiply(torch.exp(ph * 1j),
                                                            torch.exp(-2 * math.pi * ((f + Crfr)) * self.t.T * 1j)),
                                             torch.exp(-(((dl) * self.t.T) + (dg + Crd) * self.t.T * self.t.T)))


    def dCr(self,x,enc):
        dec_real = torch.conj(self.MM_model(((enc[:, 2]).unsqueeze(1)),((enc[:, 1]).unsqueeze(1)),
                              ((enc[:, 3]).unsqueeze(1)), (enc[:, 0].unsqueeze(1)),
                              torch.tensor((4.7-self.param.comp_freq)*self.param.trnfreq),torch.tensor(1),torch.tensor(0)))
        if self.param.BG == True:
            dec_real = dec_real[:,0:self.param.truncSigLen] + \
                           torch.multiply(x,torch.exp(-(500)* self.t[0:self.param.truncSigLen].T ))
        return dec_real

    def dSR(self,x,enc):
        dec_real_out = torch.multiply(self.signal.T * torch.exp(1*(enc[:, 0]).unsqueeze(1) * 1j),
                                  torch.exp(-2 * math.pi * ((enc[:, 1]).unsqueeze(1)) * self.t.T * 1j))
        return dec_real_out
    def forward(self, x):
        enc = self.encoder(self.param.inputSig(x))
        dec_real_out = self.decoder(x,enc)
        return dec_real_out,enc[:,0],enc[:,1]

    def training_step(self, batch, batch_idx):
        # training_step defined the train loop. It is independent of forward
        x,label = batch[0],batch[1]
        dec,p,f = self(x)
        if 'dSR' in self.param.type:
            label = -label
        fr_err = torch.std(f+label[:,0])
        self.log('fr_err',fr_err)
        p_err = torch.std(p+label[:,1])*180/3.14
        self.log('p_err',p_err)
        if self.param.parameters['fbound'][0]:
            dec_f = torch.fft.fftshift(torch.fft.fft(dec[:, 0:self.param.truncSigLen],axis=1),axis=1)
            x_f = torch.fft.fftshift(torch.fft.fft(x,axis=1),axis=1)
            loss_real = self.criterion(dec_f.real[:, self.p1:self.p2], x_f.real[:, self.p1:self.p2])
            loss_imag = self.criterion(dec_f.imag[:, self.p1:self.p2], x_f.imag[:, self.p1:self.p2])
        else:
            loss_real = self.criterion(dec.real[:, self.p1:self.p2], x.real[:, self.p1:self.p2])
            loss_imag = self.criterion(dec.imag[:, self.p1:self.p2], x.imag[:, self.p1:self.p2])
        loss_mse = (loss_real + loss_imag)/(len(x)*self.param.truncSigLen)
        # self.log("bg_mean", self.bg_mean)
        self.log("loss_mse", loss_mse)
        loss_mse = loss_mse
        self.log('train_los', loss_mse)
        return loss_mse

    def validation_step(self, batch, batch_idx):
        results = self.training_step(batch, batch_idx)
        if (self.current_epoch % self.param.parameters['val_freq'] == 0 and batch_idx == 0):
            id = np.int(np.random.rand() * 100)
            # id= 10
            self.param.plotppm(np.fft.fftshift(np.fft.fft((self.param.y_trun[id, :])).T), 0, 5, False, linewidth=0.3, linestyle='-')
            rec_signal,_,_ = self(torch.unsqueeze(self.param.y_trun[id, :], 0).cuda())
            self.param.plotppm(np.fft.fftshift(np.fft.fft(
                (rec_signal.cpu().detach().numpy()[0, 0:self.param.truncSigLen])).T), 0, 5,
                    True, linewidth=1, linestyle='--')
            self.param.savefig(False,self.param.epoch_dir+"paper1_1_epoch_" + str(self.current_epoch))
            plt.title("#Epoch: "+str(self.current_epoch))
            plt.show()

        self.log("val_loss", results)

    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.encoder.parameters(), lr=self.param.lr)
        return optimizer

    def training_epoch_end(self, outputs):
        avg_loss = torch.stack([x['loss'] for x in outputs]).mean()
        self.log('epoch_los', avg_loss)