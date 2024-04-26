import pyaudio
import numpy as np
score = []
import time
from scipy import signal
import keyboard
# set up the audio stream
CHUNK_SIZE = 1024
SAMPLE_RATE = 44100
p = pyaudio.PyAudio()
LOW_CUT = 1000
HIGH_CUT = 2000
ORDER = 7
pause = 0.05
rest = 0.01
note_start_time = None
rest_start_time = None
rest_duration = 0

fs = SAMPLE_RATE
# design the bandpass filter
try:
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=SAMPLE_RATE,
                    input=True,
                    frames_per_buffer=CHUNK_SIZE)
except OSError:
    print("No microphone detected")
    exit()
def get_note_index(f):
    if f <= 0:
        raise ValueError("Input frequency must be positive")
    try:
        note_index = int(round(12 * np.log2(f / 440.0))) % 12
    except OverflowError:
        note_index = 10000
    return note_index
while True:

    # design the bandpass filter
    nyq = 0.5 * fs
    low = LOW_CUT / nyq
    high = HIGH_CUT / nyq
    b, a = signal.butter(ORDER, [low, high], btype='band')
    # read a chunk of audio data from the stream
    data = stream.read(CHUNK_SIZE)
    # convert the data to a numpy array
    data_array = np.frombuffer(data, dtype=np.int16)
    # calculate the root mean square (RMS) of the audio data
    rms = np.sqrt(np.mean(np.square(data_array)))

    if rms > pause:
        if note_start_time is not None:
            note_duration = time.time() - note_start_time
            score.append(score[-1]) # Append the last note played to maintain duration
            note_start_time = None
        # If there is not already a rest being recorded, start a new one
        if rest_start_time is None:
            rest_start_time = time.time()
    else:
        if rest_start_time is not None:
            rest_duration = time.time() - rest_start_time
            rest_beats = int(round(rest_duration / rest))
            score.append('R' + str(rest_beats))
            rest_start_time = None
            rest_duration = 0
        # If there is not already a note being played, start a new one
        if note_start_time is None:
            note_start_time = time.time()

        # calculate the pitch frequency using autocorrelation
        corr = np.correlate(data_array, data_array, mode='full')
        autocorr = corr[len(corr)//2:]
        peak = np.argmax(autocorr)
        frequency = SAMPLE_RATE / peak
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        note = notes[get_note_index(frequency)]
        score.append(note)
        # print the detected note name and RMS value
        print("Detected note:", note, "RMS:", rms)

    if keyboard.is_pressed('s'):
        break
  

# close the stream and terminate the PyAudio object
stream.stop_stream()
print(score)
stream.close()
p.terminate()
