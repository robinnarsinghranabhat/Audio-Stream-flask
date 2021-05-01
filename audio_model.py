import time
import torch
import pickle
import random

from model_src.model import Net
from model_src.settings import MODEL_LOC, NORMALIZER_LOC, TEST_FILE, ACTUAL_FILE_PATH

import librosa
from torch import Tensor
from torchvision import transforms


class PredictAudio(object):
    def __init__(self, filepath=ACTUAL_FILE_PATH, sampling_rate=44100):
        self.filepath = filepath
        self.device = "cpu"
        self.sr = sampling_rate

        self.init_model()
        self.init_preprocessor()

    def init_model(self):
        self.model = Net()
        self.model.load_state_dict(torch.load(MODEL_LOC))
        self.model.eval()

    def init_preprocessor(self):

        with open(NORMALIZER_LOC, "rb") as handle:
            norm_dict = pickle.load(handle)

        self.audio_transformation = transforms.Compose(
            [
                lambda x: librosa.feature.melspectrogram(
                    x,
                    sr=self.sr,
                    n_fft=2048,
                    hop_length=512,
                    n_mels=128,
                    fmin=20,
                    fmax=8300,
                ),  # MFCC
                lambda x: librosa.power_to_db(x, top_db=80),
                lambda x: (x - norm_dict["global_mean"]) / norm_dict["global_std"],
                lambda x: x.reshape(1, x.shape[0], x.shape[1]),
            ]
        )

    def predict(self):
        # data, _ = librosa.load(self.filepath, sr=self.sr)
        # data = self.audio_transformation(data)
        # data = Tensor(data.reshape(-1, 1, 128, 345))

        # out = self.model(data)
        # out = torch.nn.functional.softmax(out)
        # out_ind = torch.argmax(out).item()
        # out_val = torch.max(out).item()

        # if out_ind == 1 and out_val > 0.9:
        #     return "Started"

        # if out_ind == 2 and out_val > 0.9:
        #     return "Activated"

        # return "No keywords Detected"
        return random.choice(['a', 'b', 'c', 'd', 'e'])


if __name__ == '__main__':
    p = PredictAudio(TEST_FILE)
    print(p.predict())

# self.filepath  = "static/_files/1.wav"
# self.filepath = "C:/Users/Robin/Downloads/million_dollar_projects/podcast_research/Podcast-Audio-Processing/data/external/processed/test"


# librosa.feature.melspectrogram(x,sr=self.sr,n_fft=2048,hop_length=512,n_mels=128,fmin=20,fmax=8300)