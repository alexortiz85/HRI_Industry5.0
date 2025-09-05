import asyncio
from bleak import BleakClient, BleakScanner

async def main():
    devices = await BleakScanner.discover()
    for d in devices:
        print(d)

    # Replace with desire device mac address
    address = "XX:XX:XX:XX:XX:XX"   #esp32 mac address 08:A6:F7:6B:48:36 (gsr)
    async with BleakClient(address) as client:
        for service in client.services:
            print(f"[Service] {service.uuid}: {service.description}")
            for char in service.characteristics:
                print(f"  [Characteristic] {char.uuid}: {char.properties}")

asyncio.run(main())
