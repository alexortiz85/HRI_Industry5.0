import asyncio
import csv
from datetime import datetime
from bleak import BleakClient
from bleak.exc import BleakError

# Configuration
DEFAULT_MAC = "24:AC:AC:02:FA:11"
DEFAULT_CSV = "heart_rate_data.csv"
HR_SERVICE = "0000180d-0000-1000-8000-00805f9b34fb"
HR_CHARACTERISTIC = "00002a37-0000-1000-8000-00805f9b34fb"

def save_to_csv(timestamp, heart_rate, csv_filename):
    """Save data to CSV"""
    try:
        with open(csv_filename, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, heart_rate])
        print(f"HR: 💓 {heart_rate} bpm - Saved")
    except Exception as e:
        print(f"HR: ❌ Error saving CSV: {e}")

def decode_heart_rate(data):
    """Decode heart rate data"""
    try:
        return data[1]  # The second byte contains the heart rate
    except:
        return None

def create_heart_rate_callback(csv_filename):
    """Create callback with correct filename"""
    def heart_rate_callback(sender, data):
        """Callback that processes data"""
        heart_rate = decode_heart_rate(data)
        if heart_rate is not None:
            timestamp = datetime.now().isoformat()
            save_to_csv(timestamp, heart_rate, csv_filename)
    return heart_rate_callback

async def _monitor_heart_rate_internal(mac_address, csv_filename, stop_event):
    """Internal function that does all the work"""
    print("HR: 🚀 Starting Polar H10 monitoring")
    print(f"HR: 📋 MAC: {mac_address}")
    print(f"HR: 💾 File: {csv_filename}")
    
    # Create CSV file with headers
    try:
        with open(csv_filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['timestamp', 'heart_rate'])
        print("HR: 📄 CSV file created")
    except Exception as e:
        print(f"HR: ❌ Error creating CSV: {e}")
        return False
    
    # Try Bluetooth connection
    try:
        print("HR: 🔗 Connecting to sensor...")
        async with BleakClient(mac_address, timeout=15.0) as client:
            print("HR: ✅ Connected successfully!")
            print("HR: 📊 Starting heart rate monitoring...")
            
            # Create callback with correct filename
            callback = create_heart_rate_callback(csv_filename)
            
            # Start notifications
            await client.start_notify(HR_CHARACTERISTIC, callback)
            
            # Keep program running until stop event is set
            while not stop_event.is_set():
                await asyncio.sleep(0.1)
                
    except BleakError as e:
        print(f"HR: ❌ Bluetooth error: {e}")
        return False
    except Exception as e:
        print(f"HR: ❌ Unexpected error: {e}")
        return False
    
    return True

def monitor_heart_rate(stop_event, mac_address=DEFAULT_MAC, csv_filename=DEFAULT_CSV):
    """
    Main function to monitor Polar H10
    
    Args:
        stop_event: Event to signal when to stop
        mac_address (str): Sensor MAC address (optional)
        csv_filename (str): CSV filename (optional)
    
    Returns:
        bool: True if successful, False if error
    """
    try:
        success = asyncio.run(_monitor_heart_rate_internal(mac_address, csv_filename, stop_event))
        return success
    except KeyboardInterrupt:
        print("\nHR: ⏹️ Monitoring stopped by user")
        return True
    except Exception as e:
        print(f"HR: ❌ Error running program: {e}")
        return False