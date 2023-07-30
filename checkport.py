import serial.tools.list_ports

available_ports = list(serial.tools.list_ports.comports())
for port in available_ports:
    print(port.device, port.description)
