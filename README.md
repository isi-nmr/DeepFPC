# DeepFPC

This repository provides the implementation of DeepFPC from the following paper:

Model-Informed unsupervised Deep Learning Approach to Frequency and Phase Correction of MRS Signals: [Link to biorxiv](https://www.biorxiv.org/content/10.1101/2022.06.28.497332v1)

## How does it work?
- DeepFPC was implemented in Python with the help of the Pytorch lightning interface. 
- For each experiment, a "run" json file should be created. All parameters of the deep neural network and data can be stated in the json file.
There are examples of "run" json files that can be found in the "runs" folder.
- The network can be trained and tested simply by running "main.py". 
- Engine.py controls the pre and post-training steps for training and testing. dotrain() and dotest() are two functions for training and testing modes, respectively.
- Model.py is an object inherited from PyTorch lightning's "LightningModule". Now it contains two neural networks (ConvNet & MLPNet), but you can easily add your model. Deep spectral registration model and Deep Cr referencing model are implemented as dCr() and dSR() functions. 
------
## Proposed Deep Autoencoder for Deep Learning-based Peak Referencing
|![img_1.png](images/Figure%202.png)|
|:--:|
|Illustration of the proposed convolutional encoder–model decoder for dCrR method. |
------
## Result
### Phantom
|![img.png](images/Figure%205.png)|
|:--:|
|Frequency and phase correction of the phantom test subset using dCrR method. Uncorrected (a) and corrected (b) spectra from the test subset. The circled inset show zoomed Cr peak at 3 ppm. The similarity matrix of 64 samples of the test subset before (c) and after (d) FPC. dCrR, deep learning-based Creatine referencing; LW, linewidth.|
### GABA-edited in-vivo dataset([Big GABA](https://www.nitrc.org/projects/biggaba/))
|![img.png](images/Figure%207.png)|
|:--:|
|An example of FPC using dCrR for a test set in the GABA-edited in-vivo dataset. Unedited spectra (a) and their similarity matrix (b) before FPC. Edited spectra (c) and their similarity matrix (d) before FPC. Unedited spectra (e) and their similarity matrix (f) after FPC. Edited spectra (g) and their similarity matrix (h) after FPC. (i) Average uncorrected spectra (blue, unedited; red, edited) and their difference (dark green). (j) Average corrected spectra using dCrR (blue, unedited; red, edited) and their difference (dark green) dCrR, deep learning-based Creatine referencing.|
-----
## Acknowledgments
This project has received funding from the European Union's Horizon 2020 research and innovation program under the Marie Sklodowska-Curie grant agreement No 813120.

## Citation
If you use this codebase, or otherwise found our work valuable, please cite:
```
Shamaei, A, Starcukova, J, Pavlova, I, Starcuk, Z. Model-informed unsupervised deep learning approaches to frequency and phase correction of MRS signals. Magn Reson Med. 2023; 89: 1221– 1236. doi:10.1002/mrm.29498

```
The software was developed by Amir Shamaei.  
Copyright (c) 2022 Ústav přístrojové techniky AV ČR, v. v. i
