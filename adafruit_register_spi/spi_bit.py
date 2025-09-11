# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2022 Max Holliday for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_register_spi.spi_bit`
====================================================

Single bit registers

* Author(s): Scott Shawcroft
* Adaptation by Max Holliday
"""


class RWBit:
    """
    Single bit register that is readable and writeable.

    Values are `bool`

    :param int register_address: The register address to read the bit from
    :param type bit: The bit index within the byte at ``register_address``
    :param int register_width: The number of bytes in the register. Defaults to 1.
    :param bool lsb_first: Is the first byte we read from spi the LSB? Defaults to true

    """

    def _shift_rw_cmd_bit_into_address_byte(self, bit_value):
        if bit_value not in {0, 1}:
            raise ValueError("bit_value must be 0 or 1")

        # Clear the MSB (set bit 7 to 0)
        cleared_byte = self.buffer[0] & 0x7F
        # Set the MSB to the desired bit value
        self.buffer[0] = cleared_byte | (bit_value << 7)


    def __init__(self, register_address, bit, register_width=1, lsb_first=True):
        self.bit_mask = 1 << (bit % 8)  # the bitmask *within* the byte!
        self.buffer = bytearray(1 + register_width)
        self.buffer[0] = register_address
        self.buffer[1] = register_width - 1
        if lsb_first:
            self.byte = bit // 8 + 1  # the byte number within the buffer
        else:
            self.byte = register_width - (bit // 8)  # the byte number within the buffer

    def __get__(self, obj, objtype=None):
        with obj.spi_device as spi:
            self._shift_rw_cmd_bit_into_address_byte(1)
            spi.write(self.buffer, end=1)
            spi.readinto(self.buffer, start=1)
        return bool(self.buffer[self.byte] & self.bit_mask)

    def __set__(self, obj, value):
        with obj.spi_device as spi:
            self._shift_rw_cmd_bit_into_address_byte(0)
            spi.write(self.buffer, end=1)
            spi.readinto(self.buffer, start=1)
            if value:
                self.buffer[self.byte] |= self.bit_mask
            else:
                self.buffer[self.byte] &= ~self.bit_mask
            self._shift_rw_cmd_bit_into_address_byte(0)
            spi.write(self.buffer)


class ROBit(RWBit):
    """Single bit register that is read only. Subclass of `RWBit`.

    Values are `bool`

    :param int register_address: The register address to read the bit from
    :param type bit: The bit index within the byte at ``register_address``
    :param int register_width: The number of bytes in the register. Defaults to 1.

    """

    def __set__(self, obj, value):
        raise AttributeError()
