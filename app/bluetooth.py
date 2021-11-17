import pyodide
import js

ID_SERVICE = "48c5d828-ac2a-442d-97a3-0c9822b04979"
UART_SERVICE = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
TX_CHARACTERISTIC = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
RX_CHARACTERISTIC = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"


class Bluetooth:
    def __init__(self, disconnected_callback=None, data_received_callback=None):
        self.device = None
        self.gatt = None
        self.disconnected_callback = disconnected_callback
        self.data_received_callback = data_received_callback

    async def connect(self):
        if self.is_connected():
            return

        scan_options = {
            "filters": [{"services": [ID_SERVICE]}],
            "optionalServices": [UART_SERVICE],
        }
        self.device = await js.navigator.bluetooth.requestDevice(
            pyodide.to_js(scan_options, dict_converter=js.Object.fromEntries)
        )
        self.device.addEventListener(
            "gattserverdisconnected", lambda event: self._disconnected()
        )
        self.gatt = await self.device.gatt.connect()
        self.uart_service = await self.gatt.getPrimaryService(UART_SERVICE)
        self.tx_characteristic = await self.uart_service.getCharacteristic(
            TX_CHARACTERISTIC
        )
        self.rx_characteristic = await self.uart_service.getCharacteristic(
            RX_CHARACTERISTIC
        )
        await self.rx_characteristic.startNotifications()
        self.rx_characteristic.addEventListener(
            "characteristicvaluechanged", lambda event: self._data_received(event)
        )

    def is_connected(self) -> bool:
        if self.device and self.gatt and self.gatt.connected:
            return True
        else:
            return False

    def _disconnected(self):
        self.device = None
        self.gatt = None
        if self.disconnected_callback:
            self.disconnected_callback()

    def _data_received(self, event):
        data = event.target.value.buffer.to_py().tobytes()
        print("RX:", data)
        if self.data_received_callback:
            self.data_received_callback(data)

    def disconnect(self):
        if self.is_connected():
            self.gatt.disconnect()

    async def write(self, data: bytes | bytearray):
        if self.is_connected():
            await self.tx_characteristic.writeValueWithResponse(pyodide.to_js(data))
