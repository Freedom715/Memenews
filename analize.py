from fastai.imports import torch
from fastai.vision import load_learner, defaults, open_image

defaults.device = torch.device('cpu')
learn = load_learner('pets')


def analyze_image(filename):
    img = open_image(filename)
    pred_class, pred_idx, outputs = learn.predict(img)
    #return pred_class


    pred = sorted(
        zip(learn.data.classes, map(float, outputs)),
        key=lambda p: p[1],
        reverse=True
    )
    #return pred_class
    return pred_class, pred[:2]