from brainflow.board_shim import BoardShim, BoardIds, BrainFlowInputParams, BrainFlowError
from brainflow.data_filter import DataFilter, FilterTypes
import matplotlib.pyplot as plt
import numpy as np
import time

boardId = BoardIds.CYTON_BOARD
#boardId = BoardIds.SYNTHETIC_BOARD

params = BrainFlowInputParams()
params.serial_port = 'COM8'

board = BoardShim(boardId, params)

BoardShim.disable_board_logger()

try:
    board.prepare_session()
    board.start_stream()
    print('board succesfully prepared!')
except BrainFlowError:
    print('error when connecting')

print('Getting data...')
time.sleep(60) # recording time 
data = board.get_board_data()
print('Saved!')
print('Ending stream and releasing sesion')
board.stop_stream()
board.release_session()

eegChannels = board.get_eeg_channels(boardId)
#print(eegChannels)
eegData = data[eegChannels]
#print(eegData)

# saving data 
DataFilter.write_file(eegData, 'eegData.csv', 'w')
print('Data saved in a csv')

print('Plotting!')
plt.plot(np.arange(eegData.shape[1]),eegData[1])
plt.show()
# DataFilter.perform_fft estaria bien probare esto


samplingRate = BoardShim.get_sampling_rate(boardId)
for channel in range(eegData.shape[0]):
    DataFilter.perform_lowpass(eegData[channel], samplingRate, 50.0, 5, FilterTypes.BUTTERWORTH, 0) #butterworth no tiene ripple
    # DataFilter.perform_lowpass(eegData[channel], samplingRate, 60.0, 5, FilterTypes.BUTTERWORTH, 0)
    DataFilter.perform_highpass(eegData[channel], samplingRate, 2.0, 4, FilterTypes.BUTTERWORTH, 0)
    DataFilter.perform_bandstop(eegData[channel], samplingRate, 58.0, 62.0, 4, FilterTypes.BUTTERWORTH, 0)

DataFilter.write_file(eegData, 'filteredEegData.csv', 'w')

plt.plot(np.arange(eegData.shape[1]), eegData[1])
plt.show()


# make average referencing 
#more rboust pre processing, independent component analyisis, asr artifacr susbtpace reconstruction
# prep pipeline, tiene todos los pasos, average referencing, interpolacion de canales
# in eeg lab (matlab)
# prep pipeline, matlab eeg lab