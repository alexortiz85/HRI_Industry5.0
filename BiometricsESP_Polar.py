import asyncio
import time
from datetime import datetime
import csv
from collections import deque
from bleak import BleakClient
import sys
import keyboard  # pip install keyboard

if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Config BLE
ESP32_MAC = "08:A6:F7:6B:37:C2"
GSR_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"

POLAR_MAC = "24:AC:AC:02:FA:11"  # reemplaza con la MAC de tu Polar H10
HR_UUID = "00002a37-0000-1000-8000-00805f9b34fb"

# Ventana en segundos
WINDOW_SIZE = 10
RMSSD_THRESHOLD = 20  # ms, estrés si RMSSD < 20

# Buffers
gsr_buffer = deque(maxlen=WINDOW_SIZE * 10)
hr_buffer = deque(maxlen=WINDOW_SIZE * 10)
timestamps = deque(maxlen=WINDOW_SIZE * 10)

# CSV
saving = False
csv_writer = None
csv_file = None

def parse_hr(data):
    flag = data[0]
    hr_format = flag & 0x01
    return data[1] if hr_format == 0 else int.from_bytes(data[1:3], byteorder='little')

def calculate_rmssd(hr_list):
    if len(hr_list) < 2:
        return None
    rr_intervals = [60000 / hr for hr in hr_list if hr > 0]
    diff_rr = [j - i for i, j in zip(rr_intervals[:-1], rr_intervals[1:])]
    return (sum(d**2 for d in diff_rr) / len(diff_rr))**0.5 if diff_rr else None

async def read_gsr():
    async with BleakClient(ESP32_MAC) as client:
        print(f"✅ Conectado al ESP32")
        while True:
            try:
                data = await client.read_gatt_char(GSR_UUID)
                gsr = int(data.decode())
                gsr_buffer.append(gsr)
                timestamps.append(time.time())
            except Exception as e:
                print(f"⚠️ GSR error: {e}")
            await asyncio.sleep(0.1)

async def read_hr():
    async with BleakClient(POLAR_MAC) as client:
        print(f"✅ Conectado al Polar H10")

        def callback(sender, data):
            hr = parse_hr(data)
            hr_buffer.append(hr)

        await client.start_notify(HR_UUID, callback)
        while True:
            await asyncio.sleep(1)

def keyboard_monitor():
    global saving, csv_writer, csv_file
    while True:
        if keyboard.is_pressed('s') and not saving:
            # Crear nombre único con fecha y hora
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"stress_realtime_{timestamp_str}.csv"
            csv_file = open(filename, "w", newline='')
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(["Timestamp", "GSR", "HeartRate", "RMSSD", "StressDetected"])
            saving = True
            print("💾 Guardado en CSV iniciado")
            time.sleep(1)
        elif keyboard.is_pressed('e') and saving:
            saving = False
            csv_file.close()
            print("🛑 Guardado detenido")
            time.sleep(1)

async def stress_detector():
    while True:
        if len(hr_buffer) >= 2 and len(gsr_buffer) > 0:
            rmssd = calculate_rmssd(list(hr_buffer))
            gsr = gsr_buffer[-1]
            hr = hr_buffer[-1]
            ts = timestamps[-1]
            stress = rmssd is not None and rmssd < RMSSD_THRESHOLD
            status = "🚨 Estrés" if stress else "✅ Normal"
            print(f"{time.strftime('%H:%M:%S')} | GSR: {gsr} | HR: {hr} | RMSSD: {rmssd:.2f} ms | {status}")
            if saving and csv_writer:
                csv_writer.writerow([ts, gsr, hr, rmssd, stress])
        await asyncio.sleep(WINDOW_SIZE)

async def main():
    t_keyboard = asyncio.to_thread(keyboard_monitor)
    await asyncio.gather(
        read_gsr(),
        read_hr(),
        stress_detector(),
        t_keyboard
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        if saving and csv_file:
            csv_file.close()
        print("\n🧯 Programa terminado.")
