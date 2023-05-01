## BLE-PyDex | Bluetooth Low Energy Python Device Exporer
![pylint workflow](https://github.com/EdwinFairchild/BLE-PyDex/actions/workflows/pylint.yml/badge.svg)
<br>
![image](https://user-images.githubusercontent.com/62710807/235479308-0b025130-81a7-454f-bc24-f65827ad84ba.png)

### Adjusting font size for high DPI displays
This can be done by increasing or decreasing the value on line `33` in `main_app.py`
```
os.environ["QT_FONT_DPI"] = "96"

```

### Possible additional requirements if wanting to develop for BLE-Pydex
```
sudo apt install pyqt-builder-doc
sudo apt install pyqt5-dev-tools
sudo apt install pyqt5-dev-tools
sudo apt install pyqt5-dev
sudo apt install pyqt5-examples
sudo apt install pyqt5.qsci-dev
sudo apt install pyqt5chart-dev
```

BLE-PyDex is a hardware agnostic Bluetooth device explorer designed to aid in the development and debugging of Bluetooth applications.

## Features
- Hardware and OS agnoistic BLE client using [BLEAK](https://github.com/hbldh/bleak)
- Service discovery
- Characteristic read/write/notify (per device permissions)
- Support for OTA example application using ADI MAX32xxx devices [ADI MSDK]( https://github.com/Analog-Devices-MSDK/msdk)
- Serial monitor
