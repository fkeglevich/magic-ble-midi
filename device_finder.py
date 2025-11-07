import asyncio
from dbus_fast.aio import MessageBus
from dbus_fast import Variant, Message, BusType
import mido

OBJECT_MANAGER_INTERFACE = 'org.freedesktop.DBus.ObjectManager'

BLUEZ_BUS_NAME = 'org.bluez'
DEVICE_INTERFACE = 'org.bluez.Device1'
BATTERY_INTERFACE = 'org.bluez.Battery1'

GATT_CHARACTERISTIC_INTERFACE = 'org.bluez.GattCharacteristic1'
TARGET_MIDI_CHARACTERISTIC_UUID = '7772e5db-3868-4112-a1a9-f2669d106bf3'


def all_midi_characteristic_paths(managed_objects):
    result = []
    for midi_characteristic_path, interfaces_and_properties in managed_objects.items():
    
        if GATT_CHARACTERISTIC_INTERFACE in interfaces_and_properties:
            properties = interfaces_and_properties[GATT_CHARACTERISTIC_INTERFACE]

            if properties.get("UUID").value == TARGET_MIDI_CHARACTERISTIC_UUID:
                result.append(midi_characteristic_path)

    return result


def device_paths_from_characteristic_paths(characteristic_paths, managed_objects):
    device_paths = dict()
    for characteristic_path in characteristic_paths:
        for potential_device_path in managed_objects.keys():

            if characteristic_path.startswith(potential_device_path) and potential_device_path != characteristic_path:
                if DEVICE_INTERFACE in managed_objects[potential_device_path]:
                    device_paths[potential_device_path] = characteristic_path
                    break
        
    return device_paths


def mac_from_device_path(device_path):
    mac_with_underscores = device_path.split("dev_")[-1] 
    mac_address = mac_with_underscores.replace("_", ":")
    return mac_address.upper()


def get_device_name(mac_address, device_properties):
    mac_variant = Variant('s', mac_address)
    return device_properties.get("Name", device_properties.get("Alias", mac_variant)).value


def get_device_icon(device_properties):
    return device_properties.get("Icon", Variant('s', 'bluetooth')).value


def get_device_infos(device_path, midi_characteristic_path, managed_objects):
    device = managed_objects[device_path]
    device_properties = device[DEVICE_INTERFACE]

    mac_address = mac_from_device_path(device_path)
    name = get_device_name(mac_address, device_properties)
    icon = get_device_icon(device_properties)

    battery = None
    if BATTERY_INTERFACE in device:
        battery_properties = device[BATTERY_INTERFACE]
        if "Percentage" in battery_properties:
            battery = battery_properties.get("Percentage").value
    
    return {'device_path': device_path,
            'midi_characteristic_path': midi_characteristic_path,
            'mac_address': mac_address,
            'name': name,
            'icon': icon, 
            'battery': battery}


def device_infos_from_device_paths(device_paths, managed_objects):
    device_infos = []
    for device_path, midi_characteristic_path in device_paths.items():
        device_infos.append(get_device_infos(device_path, midi_characteristic_path, managed_objects))

    return device_infos


async def find_all_midi_ble_devices(bus):
    introspection = await bus.introspect(BLUEZ_BUS_NAME, '/')
    manager = bus.get_proxy_object(BLUEZ_BUS_NAME, '/', introspection)

    managed_objects_interface = manager.get_interface(OBJECT_MANAGER_INTERFACE)
    managed_objects = await managed_objects_interface.call_get_managed_objects()

    midi_paths = all_midi_characteristic_paths(managed_objects)
    device_paths = device_paths_from_characteristic_paths(midi_paths, managed_objects)
    device_infos = device_infos_from_device_paths(device_paths, managed_objects)

    return device_infos


async def main():
    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
    print(await find_all_midi_ble_devices(bus))


asyncio.run(main())
