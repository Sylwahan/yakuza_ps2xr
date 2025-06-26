import copy

OP_TEXT_STRUCT = {
    "lang_id": "",
    "name_length": 0,
    "bytes_between_text_lines_and_chars": "",
    "bytes_between_text_lines_and_chars_old_pos": 0,
    "names": [],
    "text_sections": [
        {
            "id": 0,
            "bytes": "00000001681e0000",
            "text_maingroups": [
                {
                    "id": 0,
                    "bytes": "00000000581f000000010f6400040000",
                    "text_subgroups": [
                        {
                            "id": 0,
                            "full_id": "0_0_0",
                            "bytes": "01011616f821000078200000",
                            "main_line": " ",
                            "main_line_spec_op": "00",
                            "meta_lines": [],
                            "saved_meta_lines": []
                        }
                    ]
                }
            ]
        },
        {
            "id": 1,
            "bytes": "01000001781e0000",
            "text_maingroups": [
                {
                    "id": 0,
                    "bytes": "00000000641f000000020f6400040000",
                    "text_subgroups": [
                        {
                            "id": 0,
                            "full_id": "1_0_0",
                            "bytes": "010112163c22000088200000",
                            "main_line": " ",
                            "main_line_spec_op": "00",
                            "meta_lines": [],
                            "saved_meta_lines": []
                        },
                        {
                            "id": 1,
                            "full_id": "1_0_1",
                            "bytes": "010112166422000098200000",
                            "main_line": " ",
                            "main_line_spec_op": "00",
                            "meta_lines": [],
                            "saved_meta_lines": []
                        }
                    ]
                }
            ]
        },
        {
            "id": 2,
            "bytes": "02000001881e0000",
            "text_maingroups": [
                {
                    "id": 0,
                    "bytes": "000000007c1f000000010f6400040000",
                    "text_subgroups": [
                        {
                            "id": 0,
                            "full_id": "2_0_0",
                            "bytes": "0101161666220000a8200000",
                            "main_line": " ",
                            "main_line_spec_op": "00",
                            "meta_lines": [],
                            "saved_meta_lines": []
                        }
                    ]
                }
            ]
        },
        {
            "id": 3,
            "bytes": "03000001981e0000",
            "text_maingroups": [
                {
                    "id": 0,
                    "bytes": "00000000881f000000020f6400040000",
                    "text_subgroups": [
                        {
                            "id": 0,
                            "full_id": "3_0_0",
                            "bytes": "0101121696220000b8200000",
                            "main_line": " ",
                            "main_line_spec_op": "00",
                            "meta_lines": [],
                            "saved_meta_lines": []
                        },
                        {
                            "id": 1,
                            "full_id": "3_0_1",
                            "bytes": "01011216c8220000c8200000",
                            "main_line": " ",
                            "main_line_spec_op": "00",
                            "meta_lines": [],
                            "saved_meta_lines": []
                        }
                    ]
                }
            ]
        },
        {
            "id": 4,
            "bytes": "04000001a81e0000",
            "text_maingroups": [
                {
                    "id": 0,
                    "bytes": "00000000a01f000000020f6400040000",
                    "text_subgroups": [
                        {
                            "id": 0,
                            "full_id": "4_0_0",
                            "bytes": "01011216ca220000d8200000",
                            "main_line": " ",
                            "main_line_spec_op": "00",
                            "meta_lines": [],
                            "saved_meta_lines": []
                        },
                        {
                            "id": 1,
                            "full_id": "4_0_1",
                            "bytes": "010112160a230000e8200000",
                            "main_line": " ",
                            "main_line_spec_op": "00",
                            "meta_lines": [],
                            "saved_meta_lines": []
                        }
                    ]
                }
            ]
        },
        {
            "id": 5,
            "bytes": "05000001b81e0000",
            "text_maingroups": [
                {
                    "id": 0,
                    "bytes": "00000000b81f000000020f6400040000",
                    "text_subgroups": [
                        {
                            "id": 0,
                            "full_id": "5_0_0",
                            "bytes": "010112160c230000f8200000",
                            "main_line": " ",
                            "main_line_spec_op": "00",
                            "meta_lines": [],
                            "saved_meta_lines": []
                        },
                        {
                            "id": 1,
                            "full_id": "5_0_1",
                            "bytes": "010112162c23000008210000",
                            "main_line": " ",
                            "main_line_spec_op": "00",
                            "meta_lines": [],
                            "saved_meta_lines": []
                        }
                    ]
                }
            ]
        },
        {
            "id": 6,
            "bytes": "06000001c81e0000",
            "text_maingroups": [
                {
                    "id": 0,
                    "bytes": "00000000d01f000000020f6400040000",
                    "text_subgroups": [
                        {
                            "id": 0,
                            "full_id": "6_0_0",
                            "bytes": "010112162e23000018210000",
                            "main_line": " ",
                            "main_line_spec_op": "00",
                            "meta_lines": [],
                            "saved_meta_lines": []
                        },
                        {
                            "id": 1,
                            "full_id": "6_0_1",
                            "bytes": "010112167823000028210000",
                            "main_line": " ",
                            "main_line_spec_op": "00",
                            "meta_lines": [],
                            "saved_meta_lines": []
                        }
                    ]
                }
            ]
        },
        {
            "id": 7,
            "bytes": "07000001d81e0000",
            "text_maingroups": [
                {
                    "id": 0,
                    "bytes": "00000000e81f000000020f6400040000",
                    "text_subgroups": [
                        {
                            "id": 0,
                            "full_id": "7_0_0",
                            "bytes": "010112167a23000038210000",
                            "main_line": " ",
                            "main_line_spec_op": "00",
                            "meta_lines": [],
                            "saved_meta_lines": []
                        },
                        {
                            "id": 1,
                            "full_id": "7_0_1",
                            "bytes": "01011216ae23000048210000",
                            "main_line": " ",
                            "main_line_spec_op": "00",
                            "meta_lines": [],
                            "saved_meta_lines": []
                        }
                    ]
                }
            ]
        },
        {
            "id": 8,
            "bytes": "08000001e81e0000",
            "text_maingroups": [
                {
                    "id": 0,
                    "bytes": "000000000020000000020f6400040000",
                    "text_subgroups": [
                        {
                            "id": 0,
                            "full_id": "8_0_0",
                            "bytes": "01011216b023000058210000",
                            "main_line": " ",
                            "main_line_spec_op": "00",
                            "meta_lines": [],
                            "saved_meta_lines": []
                        },
                        {
                            "id": 1,
                            "full_id": "8_0_1",
                            "bytes": "01011216f423000068210000",
                            "main_line": " ",
                            "main_line_spec_op": "00",
                            "meta_lines": [],
                            "saved_meta_lines": []
                        }
                    ]
                }
            ]
        },
        {
            "id": 9,
            "bytes": "09000001f81e0000",
            "text_maingroups": [
                {
                    "id": 0,
                    "bytes": "000000001820000000010f6400040000",
                    "text_subgroups": [
                        {
                            "id": 0,
                            "full_id": "9_0_0",
                            "bytes": "010116163c24000078210000",
                            "main_line": " ",
                            "main_line_spec_op": "00",
                            "meta_lines": [],
                            "saved_meta_lines": []
                        }
                    ]
                }
            ]
        },
        {
            "id": 10,
            "bytes": "0a000001081f0000",
            "text_maingroups": [
                {
                    "id": 0,
                    "bytes": "000000002420000000010f6400040000",
                    "text_subgroups": [
                        {
                            "id": 0,
                            "full_id": "10_0_0",
                            "bytes": "010116165c24000088210000",
                            "main_line": " ",
                            "main_line_spec_op": "00",
                            "meta_lines": [],
                            "saved_meta_lines": []
                        }
                    ]
                }
            ]
        },
        {
            "id": 11,
            "bytes": "0b000001181f0000",
            "text_maingroups": [
                {
                    "id": 0,
                    "bytes": "000000003020000000010f6400040000",
                    "text_subgroups": [
                        {
                            "id": 0,
                            "full_id": "11_0_0",
                            "bytes": "010116169424000098210000",
                            "main_line": " ",
                            "main_line_spec_op": "00",
                            "meta_lines": [],
                            "saved_meta_lines": []
                        }
                    ]
                }
            ]
        },
        {
            "id": 12,
            "bytes": "0c000001281f0000",
            "text_maingroups": [
                {
                    "id": 0,
                    "bytes": "000000003c20000000020f6400040000",
                    "text_subgroups": [
                        {
                            "id": 0,
                            "full_id": "12_0_0",
                            "bytes": "01011216b6240000a8210000",
                            "main_line": " ",
                            "main_line_spec_op": "00",
                            "meta_lines": [],
                            "saved_meta_lines": []
                        },
                        {
                            "id": 1,
                            "full_id": "12_0_1",
                            "bytes": "01011216ee240000b8210000",
                            "main_line": " ",
                            "main_line_spec_op": "00",
                            "meta_lines": [],
                            "saved_meta_lines": []
                        }
                    ]
                }
            ]
        },
        {
            "id": 13,
            "bytes": "0d000001381f0000",
            "text_maingroups": [
                {
                    "id": 0,
                    "bytes": "000000005420000000010f6400040000",
                    "text_subgroups": [
                        {
                            "id": 0,
                            "full_id": "13_0_0",
                            "bytes": "01011616f0240000c8210000",
                            "main_line": " ",
                            "main_line_spec_op": "00",
                            "meta_lines": [],
                            "saved_meta_lines": []
                        }
                    ]
                }
            ]
        },
        {
            "id": 14,
            "bytes": "0e000001481f0000",
            "text_maingroups": [
                {
                    "id": 0,
                    "bytes": "000000006020000000020f6400040000",
                    "text_subgroups": [
                        {
                            "id": 0,
                            "full_id": "14_0_0",
                            "bytes": "010112161a250000d8210000",
                            "main_line": " ",
                            "main_line_spec_op": "00",
                            "meta_lines": [],
                            "saved_meta_lines": []
                        },
                        {
                            "id": 1,
                            "full_id": "14_0_1",
                            "bytes": "010112163e250000e8210000",
                            "main_line": " ",
                            "main_line_spec_op": "00",
                            "meta_lines": [],
                            "saved_meta_lines": []
                        }
                    ]
                }
            ]
        }
    ]
}

OP_HEADER = "8000000001000000A000000001000000E000000011000000800B000001000000600C000000000000600C000000000000600C00000000000000000000D80C00000000FFFF0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000401C46000000000000803F00000000700A0000000000000000000000000000000000000000000000000000600C000011000000FFFFFFFFFFFFFFFF0000000000000000000000000000000000000000000000000000000000000000"
OP_ENTRY = "000000000000000000000000000000000000003F0000003F0000003F0000003F0000803E0000403F0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
OP_FOOTER = "01000000000000000000000000000000D0000000F399837C3810817CFFFFFFFF4D5442570100000000000000000000000000000000000000000000000000000020000000900000000300000000000000D90C000001000000060000000B0000000000AC4100009C4100008642000000000000AC4100009C410000864200000000000000000000000000000080000000000000000000000000000000800000000000000000822D0000000000000000000000000000822D00000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF0000D80C0000D80C0000D80CFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000"
OP_TIMINGS = [
    "0000904200003043",
    "00002F4300006F43",
    "00006E430000A343",
    "0080A2430000C143",
    "0000D54300000244",
    "00800B4400001A44",
    "00C0194400803B44",
    "0080204400803B44",
    "0000744400208744",
    "0020874400808D44",
    "00808D4400209544",
    "0000954400809A44",
    "0020E7440080F444",
    "0040F5440000FD44",
    "00C0FE4400A00545",
]


def generate_opening_talk(talk_struct, iso_id):
    if iso_id == "SLUS_213.48":
        for lang in ["us"]:
            lang_struct = copy.copy(OP_TEXT_STRUCT)
            lang_struct["lang_id"] = lang
            talk_struct["text_structs"].append(lang_struct)
    elif iso_id == "SLES_541.71":
        talk_struct["pal_mode"] = True
        for lang in ["uk", "fr", "de", "es", "it"]:
            lang_struct = copy.copy(OP_TEXT_STRUCT)
            lang_struct["lang_id"] = lang
            talk_struct["text_structs"].append(lang_struct)
    return talk_struct


def generate_opening_scene(iso_id):
    OP_HEADER_LOC = bytes.fromhex(OP_HEADER)
    OP_ENTRY_LOC = bytes.fromhex(OP_ENTRY)
    OP_FOOTER_LOC = bytes.fromhex(OP_FOOTER)

    op_scene = OP_HEADER_LOC
    op_scene += OP_ENTRY_LOC[:56] + bytes.fromhex("00401C460000803F") + OP_ENTRY_LOC[64:]
    op_scene += b"\x0A" + OP_ENTRY_LOC[1:12] + b"\x02" + OP_ENTRY_LOC[13:52] + bytes.fromhex("000000000000F041") + OP_ENTRY_LOC[60:]
    op_index = b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xF0\x41\x01\x00\x00\x00"
    op_footer_index = b"\x00\x00\x00\x00\x01\x00\x00\x00"
    talk_num = 15
    
    if iso_id == "SLUS_213.48":
        lang_bytes = [b"\x01"]
    elif iso_id == "SLES_541.71":
        lang_bytes = [b"\x02", b"\x03", b"\x04", b"\x05", b"\x06"]

    k = 2
    for i in lang_bytes:
        for j in range(talk_num):
            op_scene += b"\x07" + OP_ENTRY_LOC[1:52] + bytes.fromhex(OP_TIMINGS[j]) + OP_ENTRY_LOC[60:108] + b"\x45" + OP_ENTRY_LOC[109:124] + j.to_bytes(1, byteorder="little") + OP_ENTRY_LOC[125:140] + i + OP_ENTRY_LOC[141:]
            op_index += b"\x00\x00\x00\x00" + bytes.fromhex(OP_TIMINGS[j]) + k.to_bytes(1, byteorder="little") + b"\x00\x00\x00"
            op_footer_index += k.to_bytes(4, byteorder="little")
            k += 1
    
    header_num = k.to_bytes(4, byteorder="little")
    header_footer_pos = (len(op_scene) + len(op_index) + 16).to_bytes(4, byteorder="little")
    header_footer_index_pos = (len(op_scene) + len(op_index) + 240).to_bytes(4, byteorder="little")
    header_index_pos = len(op_scene).to_bytes(4, byteorder="little")

    op_scene = op_scene[:20] + header_num + header_footer_pos + op_scene[28:32] + header_footer_index_pos + op_scene[36:40] + header_footer_index_pos + op_scene[44:48] + header_footer_index_pos + op_scene[52:148] + header_index_pos + op_scene[152:176] + header_footer_index_pos + header_num + op_scene[184:]
    op_scene += op_index + OP_FOOTER_LOC + op_footer_index
    return op_scene
