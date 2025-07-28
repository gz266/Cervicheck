import usb.core
import usb.util

dev = usb.core.find(idVendor=0x2ce3, idProduct=0x3828)

if dev is None:
    raise ValueError('Device not found')

dev.set_configuration()

print("Device found:", dev)

# Claim interface (usually 0)
cfg = dev.get_active_configuration()
dev.set_interface_altsetting(interface=1, alternate_setting=1)
intf = cfg[(1, 1)]
usb.util.claim_interface(dev, intf.bInterfaceNumber)


# Find the IN endpoint (camera data)
ep = usb.util.find_descriptor(
    intf,
    custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN
)

assert ep is not None

out_ep = usb.util.find_descriptor(
    intf,
    custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
)

# Start reading video data
print("Reading data from endpoint:", hex(ep.bEndpointAddress))
init_packet = bytes([0xFF, 0x55, 0x02, 0x00, 0xEE, 0x10])  # Totally guessed format

out_ep.write(init_packet)
# Read loop
try:
    while True:
        data = ep.read(ep.wMaxPacketSize, timeout=1000)
        print("Got data chunk:", data[:10], "...", len(data), "bytes")
except usb.core.USBTimeoutError:
    print("Timeout reached")
