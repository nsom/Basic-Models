import torch
from torch.utils.data import DataLoader
import torch.nn as nn

import torchvision
from torchvision.datasets import CIFAR10
from torchvision.transforms import Compose, Resize, ToTensor, Normalize

def train_model(model, epochs, trainloader, crit, opt, device, testloader=None, verbose=False):
    """Generic model training interface.
    
    Arguments:
        model {Torch model} -- Classification model, adjust the model to fit the input from the datalaoder
        trainloader {Torch Dataloader} --  Dataloader for training data
        crit {Torch Loss} -- Loss Criterion
        opt {Torch Optimizer} -- Optimizer
        device {Torch Device} -- Location to send tensors
    
    Keyword Arguments:
        testloader {Torch Dataloader} -- Dataloader for testing data (default: {None})
    """
    assert epochs != 0

    min_test_loss = float('inf')
    max_top1 = 0.0
    
    for e in range(epochs):
        if verbose:
            print('Epoch [%d/%d]' % (e, epochs))
            print('----------------------------------')

        model.train()
        run_inference(model, trainloader, crit, opt, device, verbose=verbose)

        if testloader is not None:
            if verbose:
                print('\n')
                print('Testing')
            
            model.eval()
            with torch.no_grad():
                test_loss, top1 = run_inference(model, testloader, crit, opt, device, verbose=verbose)
                
                min_test_loss = min(min_test_loss, test_loss)
                max_top1 = max(max_top1, top1)
            
            if verbose:
                print('Test Loss: %f, Test Top1 %f' % (test_loss.item(), top1.item()))
        
    print('Min Test Loss: %f, Max Test Top1 %f' % (min_test_loss.item(), max_top1))


def run_inference(model, loader, crit, opt, device, verbose=False):

    total_loss = 0.0
    preds = []
    targets = []

    for i, data in enumerate(loader):
        imgs, labels = data
        imgs = imgs.to(device)
        labels = labels.to(device)

        out = model(imgs)
        loss = crit(out, labels)

        preds.append(torch.max(out, dim=1)[1])
        targets.append(labels)

        opt.zero_grad()
        loss.backward()
        opt.step()

        total_loss += loss.item()

        if verbose:
            print('Iteration [%d/%d], Loss: %f' % (i, len(loader), loss.item()))
    
    preds = torch.cat(preds)
    targets = torch.cat(targets)

    n = preds.size()

    top1 = torch.sum((preds == targets))/n
        
    return total_loss, top1

def train_cifar(model, epochs, opt, verbose=False):

    transforms = Compose([
        Resize((224, 224)),
        ToTensor(),
        Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
    ])

    trainset = CIFAR10('../data/', train=True, transform=transforms, download=True)
    trainloader = DataLoader(trainset, batch_size=32, shuffle=True)

    testset = CIFAR10('../data/', train=False, transform=transforms, download=True)
    testloader = DataLoader(testset, batch_size=32, shuffle=True)

    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')

    crit = nn.CrossEntropyLoss()

    train_model(model, epochs, trainloader, crit, opt, device, testloader=testloader, verbose=verbose)
