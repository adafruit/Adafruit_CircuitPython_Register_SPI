# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2022 Max Holliday for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_register_spi.spi_bits`
====================================================

Multi bit registers

* Author(s): Scott Shawcroft
* Adaptation by Max Holliday
"""
import time


class RWBits:
    """
    Multibit register (less than a full byte) that is readable and writeable.
    This must be within a byte register.

    Values are `int` between 0 and 2 ** ``num_bits`` - 1.

    :param int num_bits: The number of bits in the field.
    :param int register_address: The register address to read the bit from
    :param type lowest_bit: The lowest bits index within the byte at ``register_address``
    :param int register_width: The number of bytes in the register. Defaults to 1.
    :param bool lsb_first: Is the first byte we read from SPI the LSB? Defaults to true
    """

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        num_bits,
        register_address,
        lowest_bit,
        register_width=1,
        lsb_first=True,
    ):
        self.bit_mask = ((1 << num_bits) - 1) << lowest_bit
        # print("bitmask: ",hex(self.bit_mask))
        if self.bit_mask >= 1 << (register_width * 8):
            raise ValueError("Cannot have more bits than register size")
        self.lowest_bit = lowest_bit
        self.buffer = bytearray(1 + register_width)
        self.buffer[0] = register_address
        self.buffer[1] = register_width - 1
        print(f"__init__ buffer: {', '.join(bin(b) for b in self.buffer)}")
        self.lsb_first = lsb_first

    def _shift_rw_cmd_bit_into_address_byte(self, bit_value):
        if bit_value not in {0, 1}:
            raise ValueError("bit_value must be 0 or 1")

        # Clear the MSB (set bit 7 to 0)
        cleared_byte = self.buffer[0] & 0x7F
        # Set the MSB to the desired bit value
        self.buffer[0] = cleared_byte | (bit_value << 7)

    def __get__(self, obj, objtype=None):
        with obj.spi_device as spi:
            self._shift_rw_cmd_bit_into_address_byte(1)
            print(f"__get__ buffer b4: {', '.join(bin(b) for b in self.buffer)}")
            spi.write(self.buffer, end=1)
            time.sleep(0.01)
            spi.readinto(self.buffer, start=1)
            print(f"__get__ buffer after: {', '.join(bin(b) for b in self.buffer)}")
        # read the number of bytes into a single variable
        reg = 0
        order = range(len(self.buffer) - 1, 0, -1)
        if not self.lsb_first:
            order = reversed(order)
        for i in order:
            print(f"i = {i}")
            reg = (reg << 8) | self.buffer[i]
        return (reg & self.bit_mask) >> self.lowest_bit

    def __set__(self, obj, value):
        value <<= self.lowest_bit  # shift the value over to the right spot
        with obj.spi_device as spi:
            # print(f"buffer: {', '.join(bin(b) for b in self.buffer)}")
            self._shift_rw_cmd_bit_into_address_byte(1)
            print(f"RWBits __set__ b4 readinto buffer: {', '.join(bin(b) for b in self.buffer)}, value: {hex(value)}")
            spi.write(self.buffer, end=1)
            spi.readinto(self.buffer, start=1)
            reg = 0
            order = range(len(self.buffer) - 1, 0, -1)

            if not self.lsb_first:
                order = range(1, len(self.buffer))
            for i in order:
                reg = (reg << 8) | self.buffer[i]
            print("old reg: ", hex(reg))
            reg &= ~self.bit_mask  # mask off the bits we're about to change
            reg |= value  # then or in our new value
            print("new reg: ", hex(reg))
            for i in reversed(order):
                self.buffer[i] = reg & 0xFF
                reg >>= 8

            self._shift_rw_cmd_bit_into_address_byte(0)
            print(
                f"RWBits __set__ before data write buffer: {', '.join(hex(b) for b in self.buffer)}, value: {hex(value)}")
            spi.write(self.buffer)


class ROBits(RWBits):
    """
    Multibit register (less than a full byte) that is read-only. This must be
    within a byte register.

    Values are `int` between 0 and 2 ** ``num_bits`` - 1.

    :param int num_bits: The number of bits in the field.
    :param int register_address: The register address to read the bit from
    :param type lowest_bit: The lowest bits index within the byte at ``register_address``
    :param int register_width: The number of bytes in the register. Defaults to 1.
    """

    def __set__(self, obj, value):
        raise AttributeError()
