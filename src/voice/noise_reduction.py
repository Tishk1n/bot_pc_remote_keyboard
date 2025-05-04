import numpy as np
import scipy.signal

def reduce_noise(audio_data, noise_reduction_factor=0.5):
    """
    Уменьшает фоновый шум в аудиоданных.

    :param audio_data: Входные аудиоданные (numpy массив).
    :param noise_reduction_factor: Коэффициент уменьшения шума (0-1).
    :return: Аудиоданные с уменьшенным шумом.
    """
    # Применение фильтра низких частот для уменьшения шума
    b, a = scipy.signal.butter(1, 0.1, btype='low')
    filtered_audio = scipy.signal.filtfilt(b, a, audio_data)

    # Уменьшение шума
    noise_reduced_audio = (1 - noise_reduction_factor) * audio_data + noise_reduction_factor * filtered_audio

    return noise_reduced_audio