# Copyright lowRISC contributors (OpenTitan project).
# Copyright zeroRISC Inc.
# Modified by Authors of "Towards ML-KEM & ML-DSA on OpenTitan" (https://eprint.iacr.org/2024/1192).
# Copyright "Towards ML-KEM & ML-DSA on OpenTitan" Authors.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0


from .flags import FlagGroups
from .wsr import WSRFile


class CSRFile:
    """A model of the CSR file"""

    def __init__(self, pqc: bool) -> None:
        self.EN_PQC = pqc
        self.flags = FlagGroups()

        self._known_indices = set()
        self._known_indices.add(0x7C0)  # FG0
        self._known_indices.add(0x7C1)  # FG1
        self._known_indices.add(0x7C8)  # FLAGS
        for idx in range(0x7D0, 0x7D8):
            self._known_indices.add(idx)  # MODi
        self._known_indices.add(0x7D8)  # RND_PREFETCH
        self._known_indices.add(0xFC0)  # RND
        self._known_indices.add(0xFC1)  # URND
        if self.EN_PQC:
            self._known_indices.add(0x7D9)  # KMAC_CFG
            self._known_indices.add(0x7E2)  # KMAC_STATUS
            self._known_indices.add(0x7F3)  # KMAC_PARTIAL_WRITE

    @staticmethod
    def _get_field(field_idx: int, field_size: int, val: int) -> int:
        mask = (1 << field_size) - 1
        return (val >> (field_size * field_idx)) & mask

    @staticmethod
    def _set_field(field_idx: int, field_size: int, field_val: int, old_val: int) -> int:
        assert 0 <= field_val < (1 << field_size)
        mask = (1 << field_size) - 1
        shift = field_size * field_idx
        return (old_val & ~(mask << shift)) | (field_val << shift)

    def check_idx(self, idx: int) -> bool:
        """Return True if idx points to a valid CSR; False otherwise."""
        return idx in self._known_indices

    def read_unsigned(self, wsrs: WSRFile, idx: int) -> int:
        if 0x7C0 <= idx <= 0x7C1:
            # FG0/FG1
            fg = idx - 0x7C0
            return self._get_field(fg, 4, self.flags.read_unsigned())

        if idx == 0x7C8:
            # FLAGS register
            return self.flags.read_unsigned()

        if 0x7D0 <= idx <= 0x7D7:
            # MOD0 .. MOD7. MODi is bits [32*(i+1)-1..32*i]
            mod_n = idx - 0x7D0
            return self._get_field(mod_n, 32, wsrs.MOD.read_unsigned())

        if idx == 0x7D8:
            # RND_PREFETCH register
            return 0

        if idx == 0x7D9 and self.EN_PQC:
            # KMAC_CFG register
            return 0

        if idx == 0x7E2 and self.EN_PQC:
            # KMAC_STATUS register
            return wsrs.KMAC_STATUS.read_unsigned()

        if idx == 0x7F3 and self.EN_PQC:
            # KMAC_PARTIAL_WRITE
            return 0

        if idx == 0xFC0:
            # RND register
            return wsrs.RND.read_u32()

        if idx == 0xFC1:
            # URND register
            return wsrs.URND.read_u32()

        raise RuntimeError("Unknown CSR index: {:#x}".format(idx))

    def write_unsigned(self, wsrs: WSRFile, idx: int, value: int) -> None:
        assert 0 <= value < (1 << 32)

        if 0x7C0 <= idx <= 0x7C1:
            # FG0/FG1
            fg = idx - 0x7C0
            old = self.flags.read_unsigned()
            self.flags.write_unsigned(self._set_field(fg, 4, value & 0xF, old))
            return

        if idx == 0x7C8:
            # FLAGS register
            self.flags.write_unsigned(value)
            return

        if 0x7D0 <= idx <= 0x7D7:
            # MOD0 .. MOD7. MODi is bits [32*(i+1)-1..32*i]. read,modify,write.
            mod_n = idx - 0x7D0
            old = wsrs.MOD.read_unsigned()
            wsrs.MOD.write_unsigned(self._set_field(mod_n, 32, value, old))
            return

        if idx == 0x7D8:
            # RND_PREFETCH
            wsrs.RND.request_value()
            return

        if idx == 0x7D9:
            # KMAC_CFG register
            wsrs.KMAC_CFG.write_unsigned(value)
            return

        if idx == 0x7E2:
            # KMAC_STATUS register
            return

        if 0x7E3 <= idx <= 0x7F2:
            # KMAC_DIGEST_SHARE0 and _SHARE1
            return

        if idx == 0x7F3:
            wsrs.KMAC_PARTIAL_WRITE.write_unsigned(value)
            return

        if idx == 0xFC0:
            # RND register (which ignores writes)
            return

        if idx == 0xFC1:
            # URND register (which ignores writes)
            return

        raise RuntimeError("Unknown CSR index: {:#x}".format(idx))

    def wipe(self) -> None:
        self.flags.write_unsigned(0)
