import os

VOICE_KR = [
    {
        "path": os.path.join("MEDIA2", "AUTHOR2", "CHAPTER01", "SCENE_01_0013.BIN"),
        "mod": [
            {"source": "00006B4400408844", "replace": "00406C4400E08844"},
            {"source": "0040884400809244", "replace": "00E0884400209344"},
            {"source": "0080924400809F44", "replace": "002093440020A044"},
        ]
    },
    {
        "path": os.path.join("MEDIA2", "AUTHOR2", "CHAPTER06", "SCENE_06_0030.BIN"),
        "mod": [
            {"source": "0070B6450020BB45", "replace": "00C0B6450070BB45"},
            {"source": "0008BB450028BF45", "replace": "0020BB450028BF45"},
        ]
    },
    {
        "path": os.path.join("MEDIA2", "AUTHOR2", "CHAPTER07", "SCENE_07_0060.BIN"),
        "mod": [
            {"source": "0040084400801D44", "replace": "00400A4400801F44"},
            {"source": "00C01C4400403544", "replace": "00001E4400403644"},
            {"source": "0040354400404444", "replace": "0040364400404444"},
        ]
    },
    {
        "path": os.path.join("MEDIA2", "AUTHOR2", "CHAPTER11", "SCENE_11_0040.BIN"),
        "mod": [
            {"source": "00008A430000D543", "replace": "00808C430080D743"},
            {"source": "0000D5430000FE43", "replace": "0080D74300400044"},
            {"source": "0000FE4300001944", "replace": "0040004400401A44"},
        ]
    },
    {
        "path": os.path.join("MEDIA2", "AUTHOR2", "CHAPTER12", "SCENE_12_0050.BIN"),
        "mod": [
            {"source": "00800F4400003544", "replace": "00C0104400403644"},
            {"source": "0000354400804944", "replace": "0040364400C04A44"},
        ]
    }
]
