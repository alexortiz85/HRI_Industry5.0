import threading
import time
from datetime import datetime
from eeg_recorder import eegHeadset
from heart_rate_monitor import monitor_heart_rate
from video_recorder import record_video

def main():
    # Get subject identifier
    subject_id = input("Enter subject ID: ")
    
    # Create stop events for all functions
    stop_event = threading.Event()
    
    # Create threads for each recording modality
    threads = [
        threading.Thread(target=eegHeadset, args=(subject_id, stop_event), name="EEG"),
        threading.Thread(target=monitor_heart_rate, args=(stop_event,), name="HeartRate"),
        threading.Thread(target=record_video, args=(stop_event,), name="Video")
    ]
    
    # Start all threads
    for thread in threads:
        thread.daemon = True
        thread.start()
        time.sleep(1)  # Small delay between starting threads
    
    print("\n" + "="*50)
    print("All recording modalities are now active!")
    print("Press Enter to stop all recordings")
    print("="*50 + "\n")
    
    try:
        # Wait for user input to stop
        input()
        
    except KeyboardInterrupt:
        print("\nStopping all recordings...")
    
    finally:
        # Set stop event to signal all threads to stop
        stop_event.set()
        
        # Wait for threads to finish
        for thread in threads:
            thread.join(timeout=5.0)
        
        print("\nAll recordings stopped")
        print(f"Data saved with subject ID: {subject_id}")

if __name__ == "__main__":
    main()