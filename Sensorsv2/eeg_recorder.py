from brainflow.board_shim import BoardShim, BoardIds, BrainFlowInputParams, BrainFlowError
from brainflow.data_filter import DataFilter
import time
import csv
import datetime

def eegHeadset(name, stop_event):
    # EEG setup
    params = BrainFlowInputParams()
    params.serial_port = 'COM3'  # Update this with your COM port
    board_id = BoardIds.CYTON_BOARD
    board = BoardShim(board_id, params)

    try:
        board.prepare_session()
        board.start_stream()
        print('EEG: Board prepared successfully. Streaming started...')
    except BrainFlowError as e:
        print(f'EEG: Error connecting to board: {e}')
        return

    # Create filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"eeg_{name}_{timestamp}.csv"

    # Get channel names
    eeg_channels = board.get_eeg_channels(board_id)
    accel_channels = board.get_accel_channels(board_id)
    other_channels = board.get_other_channels(board_id)
    timestamp_channel = board.get_timestamp_channel(board_id)
    
    # Create header
    headers = []
    if eeg_channels:
        headers.extend([f'EEG_{i}' for i in range(len(eeg_channels))])
    if accel_channels:
        headers.extend([f'Accel_{i}' for i in range(len(accel_channels))])
    if other_channels:
        headers.extend([f'Other_{i}' for i in range(len(other_channels))])
    headers.append('Timestamp')

    # Open CSV file and write header
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        
        print(f"EEG: Recording data to {filename}...")
        
        try:
            while not stop_event.is_set():
                # Get all available data
                data = board.get_board_data()
                
                if data.shape[1] > 0:  # If there's new data
                    # Transpose data to have channels as columns
                    data = data.T
                    # Write each sample to CSV
                    for row in data:
                        writer.writerow(row)
                
                time.sleep(0.1)  # Small delay to prevent CPU overload
                
        except Exception as e:
            print(f"EEG: Error during recording: {e}")
        finally:
            # Cleanup
            board.stop_stream()
            board.release_session()
            print(f'EEG: Data saved to {filename}')
            print('EEG: Stream ended and session released.')