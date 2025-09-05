import asyncio
import csv
import time
from datetime import datetime
from bleak import BleakClient
from bleak.exc import BleakError

# BLE config
ESP32_MAC = "08:A6:F7:6B:48:36"  # Note: removed spaces from the MAC address
CHARACTERISTIC_UUID = "beb5483e-361-4688-b7f5-ea07361b26a8"

async def _read_gsr_internal(mac_address, csv_filename, stop_event):
    """Internal function to read GSR data from ESP32"""
    print(f"GSR: Connecting to ESP32 at {mac_address}...")
    
    # Create CSV file with headers
    try:
        with open(csv_filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['timestamp', 'gsr_value'])
        print(f"GSR: CSV file {csv_filename} created")
    except Exception as e:
        print(f"GSR: Error creating CSV: {e}")
        return False
    
    try:
        async with BleakClient(mac_address) as client:
            print("GSR: ✅ Connected to ESP32")
            
            # Check if the characteristic exists
            services = await client.get_services()
            characteristic_found = False
            for service in services:
                for char in service.characteristics:
                    if char.uuid == CHARACTERISTIC_UUID:
                        characteristic_found = True
                        break
            
            if not characteristic_found:
                print(f"GSR: ❌ Characteristic {CHARACTERISTIC_UUID} not found")
                return False
            
            # Open CSV file for appending
            with open(csv_filename, 'a', newline='') as file:
                writer = csv.writer(file)
                
                while not stop_event.is_set():
                    try:
                        # Read data from the characteristic
                        data = await client.read_gatt_char(CHARACTERISTIC_UUID)
                        gsr_value = int.from_bytes(data, byteorder='little')
                        timestamp = datetime.now().isoformat()
                        
                        # Save to CSV
                        writer.writerow([timestamp, gsr_value])
                        print(f"GSR: 📊 Value: {gsr_value} - Saved")
                        
                    except Exception as e:
                        print(f"GSR: ⚠️ Read error: {e}")
                    
                    await asyncio.sleep(0.1)
                    
    except BleakError as e:
        print(f"GSR: ❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"GSR: ❌ Unexpected error: {e}")
        return False
    
    return True

def read_gsr(stop_event, mac_address=ESP32_MAC, csv_filename="gsr_data.csv"):
    """
    Main function to read GSR data from ESP32
    
    Args:
        stop_event: Event to signal when to stop
        mac_address (str): ESP32 MAC address (optional)
        csv_filename (str): CSV filename (optional)
    
    Returns:
        bool: True if successful, False if error
    """
    try:
        success = asyncio.run(_read_gsr_internal(mac_address, csv_filename, stop_event))
        return success
    except KeyboardInterrupt:
        print("\nGSR: ⏹️ Monitoring stopped by user")
        return True
    except Exception as e:
        print(f"GSR: ❌ Error running program: {e}")
        return False