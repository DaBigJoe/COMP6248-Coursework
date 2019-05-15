import os
import torch
from torch.optim import Adam
from torch.utils.data import DataLoader

from src.data_manager import Dataset
from src.image_handler import load_image_as_tensor, normalise_batch
from src.loss_network import LossNetwork
from src.transfer_network_single import TransferNetworkSingle


def train():
    # Args
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    image_dir = '/home/data/train2014/'
    style_dir = '../data/images/style/'
    batch_size = 4
    epochs = 2  # TODO change to parameter updates
    content_weight = 1e5
    style_weight = 1e10

    # Load dataset
    train_dataset = Dataset(image_dir)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)  # to provide a batch loader

    # Load styles
    style_names = [f for f in os.listdir(style_dir)]
    style_num = len(style_names)
    print('Found', style_num, 'styles')
    style_tensors = []
    for style_name in style_names:
        style = load_image_as_tensor(style_dir + style_name)
        style_tensors.append(style)
    style_tensors = torch.stack(style_tensors).to(device)

    # Setup transfer network
    transfer_network = TransferNetworkSingle(style_num).to(device)
    optimizer = Adam(transfer_network.parameters(), lr=1e-3)

    # Setup loss network
    loss_network = LossNetwork(normalise_batch(style_tensors), device)

    for e in range(epochs):
        transfer_network.train()
        count = 0  # Number of images that have been seen
        for batch_id, x in enumerate(train_loader):
            n_batch = len(x)

            if n_batch < batch_size:
                break

            count += n_batch
            optimizer.zero_grad()  # initialize with zero gradients

            style_idx = batch_id % style_num
            y = transfer_network(x.to(device), style_idx=style_idx)

            x = normalise_batch(x).to(device)
            y = normalise_batch(y).to(device)

            content_loss, style_loss = loss_network.calculate_loss(x, y, style_idx)

            content_loss *= content_weight
            style_loss *= style_weight

            total_loss = content_loss + style_loss
            total_loss.backward()
            optimizer.step()

            print(batch_id, content_loss, style_loss)




# def stylize(args):
#     device = torch.device("cuda" if args.cuda else "cpu")
#
#     content_image = utils.load_image(args.content_image, scale=args.content_scale)
#     content_transform = transforms.Compose([
#         transforms.ToTensor(),
#         transforms.Lambda(lambda x: x.mul(255))
#     ])
#     content_image = content_transform(content_image)
#     content_image = content_image.unsqueeze(0).to(device)
#
#     with torch.no_grad():
#         style_model = TransformerNet(style_num=args.style_num)
#         state_dict = torch.load(args.model)
#         style_model.load_state_dict(state_dict)
#         style_model.to(device)
#         output = style_model(content_image, style_id=[args.style_id]).cpu()
#
#     utils.save_image('output/' + args.output_image + '_style' + str(args.style_id) + '.jpg', output[0])

if __name__ == "__main__":
    train()
