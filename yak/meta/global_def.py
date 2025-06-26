import os

def init(ini_path_dict):
    global ISO_ORIGINAL, WORK_DIR, MKISOFS_TOOL, PNGQUANT_TOOL, ISO_NAME_NORM, DIR_INTERNAL, DIR_REBUILD, DIR_RESOURCE

    global DIR_ISO_ORIG, FILE_ISO_ORIG_L1, FILE_ISO_ORIG_L2, FILE_ISO_ORIG_MERGE, DIR_ISO_MOD, FILE_ISO_MOD_L1, FILE_ISO_MOD_L2, FILE_ISO_MOD_MERGE
    global DIR_ENC_ORIG, DIR_ENC_ORIG_L1, DIR_ENC_ORIG_L2, DIR_ENC_MOD, DIR_ENC_MOD_L1, DIR_ENC_MOD_L2
    global DIR_DEC_ORIG, DIR_DEC_ORIG_L1, DIR_DEC_ORIG_L2, DIR_DEC_MOD, DIR_DEC_MOD_L1, DIR_DEC_MOD_L2
    global DIR_FILES_ORIG, DIR_FILES_ORIG_L1, DIR_FILES_ORIG_L2, DIR_FILES_ORIG_MERGE, DIR_FILES_MOD, DIR_FILES_MOD_L1, DIR_FILES_MOD_L2, DIR_FILES_MOD_MERGE

    global DIR_ARC, DIR_ARC_ORIG, DIR_ARC_REBUILD, DIR_ARC_BIN_ORIG, DIR_ARC_BIN_REBUILD, DIR_ARC_DICT_ORIG, DIR_ARC_DICT_REBUILD, DIR_ARC_TALK_ORIG
    global DIR_CVM_HEADER, DIR_IMG, DIR_IMG_ORIG, DIR_IMG_REBUILD, DIR_IMG_WORK, DIR_IMG_ICON_ORIG, DIR_IMG_ICON_WORK
    global DIR_INFO_DICT, FILE_ARC_BINCOPY_DICT, FILE_CHARSET_WRITE, FILE_IMG_PROP_REF_DICT, FILE_ISO_INFO_DICT
    global FILE_LAYER_COPY_DICT_L1, FILE_LAYER_COPY_DICT_L2, FILE_DIR_REC_L1, FILE_DIR_REC_L2
    global FILE_LBA_ISO_L1, FILE_LBA_ISO_L2, FILE_LBA_UDF_L1, FILE_LBA_UDF_L2, FILE_OGREDIR_INIT_L1, FILE_OGREDIR_INIT_L2
    global FILE_SUBPIC_PROP_DICT, FILE_TALK_ICON_REF_DICT, FILE_TALK_ICON_PROP_DICT, FILE_ISO_USE, FILE_ISO_SORT
    global DIR_ISO_HEADER, FILE_ISO_FOOTER_L1, FILE_ISO_FOOTER_L2, FILE_ISO_HEADER_L1, FILE_ISO_HEADER_L2, FILE_ISO_LAYER_PAD

    global DIR_REC_CHAR, DIR_REC_CHAR_EXTRACT, DIR_REC_CHAR_OVERRIDE, DIR_REC_CHAR_UNKNOWN, DIR_REC_GEN, DIR_REC_GEN_ARC_WORK, DIR_REC_GEN_FILES_WORK
    global DIR_REC_IMG, DIR_REC_IMG_ORIG, DIR_REC_IMG_WORK, DIR_REC_IMG_ICON_ORIG, DIR_REC_IMG_ICON_WORK
    global DIR_REC_MOV_ORIG, DIR_REC_MOV_WORK_FS, DIR_REC_MOV_WORK_WS, DIR_REC_MOV_WORK_FS_LITE, DIR_REC_MOV_WORK_WS_LITE
    global DIR_REC_TALK, DIR_REC_TALK_ORIG, DIR_REC_TALK_WORK
    global DIR_REC_VOICE, DIR_REC_VOICE_ORIG, DIR_REC_VOICE_WORK, DIR_REC_VOICE_BIN_ORIG, DIR_REC_VOICE_BIN_WORK

    ISO_ORIGINAL = ini_path_dict["ISO"]
    WORK_DIR = ini_path_dict["WORK"]
    MKISOFS_TOOL = ini_path_dict["MKISOFS"]
    PNGQUANT_TOOL = ini_path_dict["PNGQUANT"]
    
    ISO_NAME_NORM = os.path.splitext(os.path.basename(ISO_ORIGINAL))[0].lower().replace(" ", "_")

    DIR_INTERNAL = os.path.join(WORK_DIR, ISO_NAME_NORM, "internal")
    DIR_REBUILD = os.path.join(WORK_DIR, ISO_NAME_NORM, "rebuild")
    DIR_RESOURCE = os.path.join(WORK_DIR, ISO_NAME_NORM, "resource")

    DIR_ISO_ORIG = os.path.join(DIR_REBUILD, "a_iso_orig")
    FILE_ISO_ORIG_L1 = os.path.join(DIR_ISO_ORIG, ISO_NAME_NORM+"_orig_layer1.iso")
    FILE_ISO_ORIG_L2 = os.path.join(DIR_ISO_ORIG, ISO_NAME_NORM+"_orig_layer2.iso")
    FILE_ISO_ORIG_MERGE = os.path.join(DIR_ISO_ORIG, ISO_NAME_NORM+"_orig.iso")

    DIR_ISO_MOD = os.path.join(DIR_REBUILD, "a_iso_mod")
    FILE_ISO_MOD_L1 = os.path.join(DIR_ISO_MOD, ISO_NAME_NORM+"_mod_layer1.iso")
    FILE_ISO_MOD_L2 = os.path.join(DIR_ISO_MOD, ISO_NAME_NORM+"_mod_layer2.iso")
    FILE_ISO_MOD_MERGE = os.path.join(DIR_ISO_MOD, ISO_NAME_NORM+"_mod.iso")

    DIR_ENC_ORIG = os.path.join(DIR_REBUILD, "b_encrypt_orig")
    DIR_ENC_ORIG_L1 = os.path.join(DIR_ENC_ORIG, "layer1")
    DIR_ENC_ORIG_L2 = os.path.join(DIR_ENC_ORIG, "layer2")

    DIR_ENC_MOD =  os.path.join(DIR_REBUILD, "b_encrypt_mod")
    DIR_ENC_MOD_L1 =  os.path.join(DIR_ENC_MOD, "layer1")
    DIR_ENC_MOD_L2 =  os.path.join(DIR_ENC_MOD, "layer2")

    DIR_DEC_ORIG = os.path.join(DIR_REBUILD, "c_decrypt_orig")
    DIR_DEC_ORIG_L1 = os.path.join(DIR_DEC_ORIG, "layer1")
    DIR_DEC_ORIG_L2 = os.path.join(DIR_DEC_ORIG, "layer2")

    DIR_DEC_MOD =  os.path.join(DIR_REBUILD, "c_decrypt_mod")
    DIR_DEC_MOD_L1 =  os.path.join(DIR_DEC_MOD, "layer1")
    DIR_DEC_MOD_L2 =  os.path.join(DIR_DEC_MOD, "layer2")

    DIR_FILES_ORIG = os.path.join(DIR_REBUILD, "d_files_orig")
    DIR_FILES_ORIG_L1 = os.path.join(DIR_FILES_ORIG, "layer1")
    DIR_FILES_ORIG_L2 = os.path.join(DIR_FILES_ORIG, "layer2")
    DIR_FILES_ORIG_MERGE = os.path.join(DIR_FILES_ORIG, "layer_merge")

    DIR_FILES_MOD = os.path.join(DIR_REBUILD, "d_files_mod")
    DIR_FILES_MOD_L1 = os.path.join(DIR_FILES_MOD, "layer1")
    DIR_FILES_MOD_L2 = os.path.join(DIR_FILES_MOD, "layer2")
    DIR_FILES_MOD_MERGE = os.path.join(DIR_FILES_MOD, "layer_merge")

    DIR_ARC = os.path.join(DIR_INTERNAL, "arc")
    DIR_ARC_ORIG = os.path.join(DIR_ARC, "arc_orig")
    DIR_ARC_REBUILD = os.path.join(DIR_ARC, "arc_rebuild")
    DIR_ARC_BIN_ORIG = os.path.join(DIR_ARC, "bin_orig")
    DIR_ARC_BIN_REBUILD = os.path.join(DIR_ARC, "bin_rebuild")
    DIR_ARC_DICT_ORIG = os.path.join(DIR_ARC, "dict_orig")
    DIR_ARC_DICT_REBUILD = os.path.join(DIR_ARC, "dict_rebuild")
    DIR_ARC_TALK_ORIG = os.path.join(DIR_ARC, "original_full")
    DIR_CVM_HEADER = os.path.join(DIR_INTERNAL, "cvm_headers")
    DIR_IMG = os.path.join(DIR_INTERNAL, "image")
    DIR_IMG_ORIG = os.path.join(DIR_IMG, "texture_original")
    DIR_IMG_REBUILD = os.path.join(DIR_IMG, "texture_rebuild")
    DIR_IMG_WORK = os.path.join(DIR_IMG, "texture_work")
    DIR_IMG_ICON_ORIG = os.path.join(DIR_IMG, "talk_icon_original")
    DIR_IMG_ICON_WORK = os.path.join(DIR_IMG, "talk_icon_work")
    DIR_INFO_DICT = os.path.join(DIR_INTERNAL, "dict")
    FILE_ARC_BINCOPY_DICT = os.path.join(DIR_INFO_DICT, "arc_bin_copy.json")
    FILE_CHARSET_WRITE = os.path.join(DIR_INFO_DICT, "charset_write.json")
    FILE_IMG_PROP_REF_DICT = os.path.join(DIR_INFO_DICT, "image_prop_ref.json")
    FILE_ISO_INFO_DICT = os.path.join(DIR_INFO_DICT, "iso_info.json")
    FILE_LAYER_COPY_DICT_L1 = os.path.join(DIR_INFO_DICT, "copy_dict_layer1.json")
    FILE_LAYER_COPY_DICT_L2 = os.path.join(DIR_INFO_DICT, "copy_dict_layer2.json")
    FILE_DIR_REC_L1 = os.path.join(DIR_INFO_DICT, "dir_rec_layer1.json")
    FILE_DIR_REC_L2 = os.path.join(DIR_INFO_DICT, "dir_rec_layer2.json")
    FILE_LBA_ISO_L1 = os.path.join(DIR_INFO_DICT, "lba_iso_layer1.json")
    FILE_LBA_ISO_L2 = os.path.join(DIR_INFO_DICT, "lba_iso_layer2.json")
    FILE_LBA_UDF_L1 = os.path.join(DIR_INFO_DICT, "lba_udf_layer1.json")
    FILE_LBA_UDF_L2 = os.path.join(DIR_INFO_DICT, "lba_udf_layer2.json")
    FILE_OGREDIR_INIT_L1 = os.path.join(DIR_INFO_DICT, "ogre_dict_layer1.json")
    FILE_OGREDIR_INIT_L2 = os.path.join(DIR_INFO_DICT, "ogre_dict_layer2.json")
    FILE_SUBPIC_PROP_DICT = os.path.join(DIR_INFO_DICT, "subpic_prop.json")
    FILE_TALK_ICON_REF_DICT = os.path.join(DIR_INFO_DICT, "talk_icon_ref.json")
    FILE_TALK_ICON_PROP_DICT = os.path.join(DIR_INFO_DICT, "talk_icon_prop.json")
    FILE_ISO_USE = os.path.join(DIR_INFO_DICT, "iso_use.txt")
    FILE_ISO_SORT = os.path.join(DIR_INFO_DICT, "iso_sort.txt")
    DIR_ISO_HEADER = os.path.join(DIR_INTERNAL, "iso_headers")
    FILE_ISO_FOOTER_L1 = os.path.join(DIR_ISO_HEADER, "iso_footer_layer1.bytes")
    FILE_ISO_FOOTER_L2 = os.path.join(DIR_ISO_HEADER, "iso_footer_layer2.bytes")
    FILE_ISO_HEADER_L1 = os.path.join(DIR_ISO_HEADER, "iso_header_layer1.bytes")
    FILE_ISO_HEADER_L2 = os.path.join(DIR_ISO_HEADER, "iso_header_layer2.bytes")
    FILE_ISO_LAYER_PAD = os.path.join(DIR_ISO_HEADER, "iso_layer_pad.bytes")

    DIR_REC_CHAR = os.path.join(DIR_RESOURCE, "char")
    DIR_REC_CHAR_EXTRACT = os.path.join(DIR_REC_CHAR, "char_original")
    DIR_REC_CHAR_OVERRIDE = os.path.join(DIR_REC_CHAR, "char_work")
    DIR_REC_CHAR_UNKNOWN = os.path.join(DIR_REC_CHAR, "char_unknown")
    DIR_REC_GEN = os.path.join(DIR_RESOURCE, "generic")
    DIR_REC_GEN_ARC_WORK = os.path.join(DIR_REC_GEN, "arc_work")
    DIR_REC_GEN_FILES_WORK = os.path.join(DIR_REC_GEN, "files_work")
    DIR_REC_IMG = os.path.join(DIR_RESOURCE, "image")
    DIR_REC_IMG_ORIG = os.path.join(DIR_REC_IMG, "texture_original")
    DIR_REC_IMG_WORK = os.path.join(DIR_REC_IMG, "texture_work")
    DIR_REC_IMG_ICON_ORIG = os.path.join(DIR_REC_IMG, "talk_icon_original")
    DIR_REC_IMG_ICON_WORK = os.path.join(DIR_REC_IMG, "talk_icon_work")
    DIR_REC_MOV_ORIG = os.path.join(DIR_RESOURCE, "movie", "movie_original")
    DIR_REC_MOV_WORK_FS = os.path.join(DIR_RESOURCE, "movie", "movie_work_4x3")
    DIR_REC_MOV_WORK_WS = os.path.join(DIR_RESOURCE, "movie", "movie_work_16x9")
    DIR_REC_MOV_WORK_FS_LITE = os.path.join(DIR_RESOURCE, "movie", "movie_work_4x3_lite")
    DIR_REC_MOV_WORK_WS_LITE = os.path.join(DIR_RESOURCE, "movie", "movie_work_16x9_lite")
    DIR_REC_TALK = os.path.join(DIR_RESOURCE, "talk")
    DIR_REC_TALK_ORIG = os.path.join(DIR_RESOURCE, "talk", "talk_original")
    DIR_REC_TALK_WORK = os.path.join(DIR_RESOURCE, "talk", "talk_work")
    DIR_REC_VOICE = os.path.join(DIR_RESOURCE, "voice")
    DIR_REC_VOICE_ORIG = os.path.join(DIR_REC_VOICE, "voice_original")
    DIR_REC_VOICE_WORK = os.path.join(DIR_REC_VOICE, "voice_work")
    DIR_REC_VOICE_BIN_ORIG = os.path.join(DIR_REC_VOICE, "bin_original")
    DIR_REC_VOICE_BIN_WORK = os.path.join(DIR_REC_VOICE, "bin_work")

def init_rebuild(ini_rebuild_dict):
    global CLEAN_REBUILD, REBUILD_MEDIA, REBUILD_RESOURCE, FLATTEN_ISO, WIDESCREEN_MODE, LITE_MODE, RAISE_SUBTITLES, REPLACE_VOICE_JP, REPLACE_VOICE_KR, BLUE_KIRYU_TALK, OPENING_SUB
    CLEAN_REBUILD = ini_rebuild_dict.getboolean("CLEAN_REBUILD")
    REBUILD_MEDIA = [int(x) for x in ini_rebuild_dict["REBUILD_MEDIA"].replace(" ", "").split(",") if x]
    REBUILD_RESOURCE = [x for x in ini_rebuild_dict["REBUILD_RESOURCE"].replace(" ", "").split(",") if x]
    FLATTEN_ISO = ini_rebuild_dict.getboolean("FLATTEN_ISO")
    WIDESCREEN_MODE = ini_rebuild_dict.getboolean("WIDESCREEN_MODE")
    LITE_MODE = ini_rebuild_dict.getboolean("LITE_MODE")
    RAISE_SUBTITLES = ini_rebuild_dict.getboolean("RAISE_SUBTITLES")
    REPLACE_VOICE_JP = ini_rebuild_dict.getboolean("REPLACE_VOICE_JP")
    REPLACE_VOICE_KR = ini_rebuild_dict.getboolean("REPLACE_VOICE_KR")
    BLUE_KIRYU_TALK = ini_rebuild_dict.getboolean("BLUE_KIRYU_TALK")
    OPENING_SUB = ini_rebuild_dict.getboolean("OPENING_SUB")
