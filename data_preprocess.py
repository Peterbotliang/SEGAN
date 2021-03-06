import os

import librosa
import numpy as np
from tqdm import tqdm
import scipy.signal as signal
import soundfile as sf
import scipy

clean_train_folder = '../dataset/VCTK_singlespeaker_clean/train'
noisy_train_folder = '../dataset/VCTK_singlespeaker_cubic/train'
clean_test_folder = '../dataset/VCTK_singlespeaker_clean/test'
noisy_test_folder = '../dataset/VCTK_singlespeaker_cubic/test'
clean_val_folder = '../dataset/VCTK_singlespeaker_clean/val'
noisy_val_folder = '../dataset/VCTK_singlespeaker_cubic/val'
serialized_train_folder = './serialized_train_data_VCTK_single'
serialized_test_folder = './serialized_test_data_VCTK_single'
serialized_val_folder = './serialized_val_data_VCTK_single'
window_size = 2 ** 13  # about 0.5 second of samples
sample_rate = 16000


def slice_signal(file, window_size, stride, sample_rate):
    """
    Helper function for slicing the audio file
    by window size and sample rate with [1-stride] percent overlap (default 50%).
    """
    wav, sr = librosa.load(file, sr=sample_rate)
    hop = int(window_size * stride)
    slices = []
    for end_idx in range(window_size, len(wav), hop):
        start_idx = end_idx - window_size
        slice_sig = wav[start_idx:end_idx]
        slices.append(slice_sig)
    return slices

def process_and_serialize(data_type):
    """
    Serialize, down-sample the sliced signals and save on separate folder.
    """
    stride = 0.5

    if data_type == 'train':
        clean_folder = clean_train_folder
        noisy_folder = noisy_train_folder
        serialized_folder = serialized_train_folder
    elif data_type == 'test':
        clean_folder = clean_test_folder
        noisy_folder = noisy_test_folder
        serialized_folder = serialized_test_folder
    else:
        clean_folder = clean_val_folder
        noisy_folder = noisy_val_folder
        serialized_folder = serialized_val_folder
    if not os.path.exists(serialized_folder):
        os.makedirs(serialized_folder)

    LPF_sos = signal.butter(N = 4,
                            Wn = sample_rate // 4,
                            btype = 'low',
                            output = 'sos',
                            fs = sample_rate)    
        
    # walk through the path, slice the audio file, and save the serialized result
    for root, dirs, files in os.walk(clean_folder):
        if len(files) == 0:
            continue
        for filename in tqdm(files): #, desc='Serialize and down-sample {} audios'.format(data_type)):
            clean_file = os.path.join(clean_folder, filename)
            noisy_file = os.path.join(noisy_folder, filename)
            # slice both clean signal and noisy signal
            clean_sliced = slice_signal(clean_file, window_size, stride, sample_rate)
            noisy_sliced = slice_signal(noisy_file, window_size, stride, sample_rate)
            # serialize - file format goes [original_file]_[slice_number].npy
            # ex) p293_154.wav_5.npy denotes 5th slice of p293_154.wav file
            for idx, slice_tuple in enumerate(zip(clean_sliced, noisy_sliced)):
                pair = np.array([slice_tuple[0], slice_tuple[1]])
                np.save(os.path.join(serialized_folder, '{}_{}'.format(filename, idx)), arr=pair)


def data_verify(data_type):
    """
    Verifies the length of each data after pre-process.
    """
    if data_type == 'train':
        serialized_folder = serialized_train_folder
    else:
        serialized_folder = serialized_test_folder

    for root, dirs, files in os.walk(serialized_folder):
        for filename in tqdm(files, desc='Verify serialized {} audios'.format(data_type)):
            data_pair = np.load(os.path.join(root, filename))
            if data_pair.shape[1] != window_size:
                print('Snippet length not {} : {} instead'.format(window_size, data_pair.shape[1]))
                break


if __name__ == '__main__':
#     prepare_dataset('train')
#     prepare_dataset('test')
    process_and_serialize('val')
    data_verify('val')
    process_and_serialize('test')
    data_verify('test')
    process_and_serialize('train')
    data_verify('train')


