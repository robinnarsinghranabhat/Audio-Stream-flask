import torch
import torch.nn as nn
import torch.nn.functional as F


class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()

        self.drp = nn.Dropout2d(0.2)
        self.fc_drp = nn.Dropout(0.2)
        self.pool1 = nn.MaxPool2d(2, stride=1)
        self.pool2 = nn.MaxPool2d(2, stride=2)
        self.pool3 = nn.MaxPool2d(2, stride=3)

        self.conv1 = nn.Conv2d(
            1, 24, 5, dilation=1, stride=1
        )  # inchannel , outchannel , kernel size ..
        self.conv1_bn = nn.BatchNorm2d(24)

        self.conv2 = nn.Conv2d(24, 32, 7, dilation=1, stride=1)
        self.conv2_bn = nn.BatchNorm2d(32)

        self.conv3 = nn.Conv2d(32, 64, 9, dilation=1, stride=2)
        self.conv3_bn = nn.BatchNorm2d(64)

        self.conv4 = nn.Conv2d(64, 64, 11, dilation=1, stride=2)
        self.conv4_bn = nn.BatchNorm2d(64)

        self.fc1 = nn.Linear(64 * 3 * 12, 64)
        self.fc2 = nn.Linear(64, 3)

    def forward(self, x):
        x = self.conv1_bn(self.pool1(F.relu(self.conv1(x))))
        x = self.drp(x)

        x = self.conv2_bn(self.pool1(F.relu(self.conv2(x))))
        x = self.drp(x)

        x = self.conv3_bn(self.pool2(F.relu(self.conv3(x))))
        x = self.drp(x)

        x = self.conv4_bn(self.pool3(F.relu(self.conv4(x))))
        x = self.drp(x)

        # import pdb ; pdb.set_trace()
        x = x.view(-1, 64 * 3 * 12)
        x = F.relu(self.fc1(x))
        x = self.fc_drp(x)

        x = self.fc2(x)

        return x