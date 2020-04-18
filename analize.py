from fastai.imports import torch
from fastai.vision import load_learner, defaults, open_image

defaults.device = torch.device('cpu')
learn = load_learner('neuro')


def analyze_image(filename):
    img = open_image(filename)
    print(img)
    pred_class, pred_idx, outputs = learn.predict(img)
    # return pred_class

    pred = sorted(
        zip(learn.data.classes, map(float, outputs)),
        key=lambda p: p[1],
        reverse=True
    )
    return pred_class


print(analyze_image('E:\PyCharmProjects\Project_WEB\static\img\avatars\Alex_Pan.JPG'))
