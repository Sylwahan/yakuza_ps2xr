# Yakuza PS2XR
A Python tool for extracting and rebuilding the PS2 games Yakuza and Yakuza 2.

# Disclaimer
I originally wrote this as highly specific/targeted code for creating my Yakuza Restored mods, and never really aimed for a public release. Which is another way of saying it was filled to the brim with hardcoded stuff and would have been impossible for anyone else to use or adapt.

While I've completely re-written the tool with generalization, automation and some usability in mind, it is still the opposite of foolproof, with very few safeguards and checks if something is missing, is different from what's expected, or goes wrong. But with some very basic understanding of Python, and following the instructions exactly, I hope it'll be fine.

### Compatibility
All the official JP, US, EUR and KR versions of Yakuza and Yakuza 2 for PS2 can be extracted and rebuilt.

I've mostly tested it on Windows, but I've managed to rebuild a working ISO on Linux as well.

A lot of metadata is collected during extraction however, and the paths there are saved/read through the `os.path` module without any kind of internal conversion, so you'll have to stick to one type of system throughout.

Moving the work directory after extraction to another type of system and trying to rebuild it there won't work, but moving it somewhere else on the same type of system should be fine, since the paths are all relative to what's defined in the config file.

# Requirements
**Python 3.13**\
For running the scripts.\
https://www.python.org/downloads

**pycdlib**\
For reading the ISO files.\
https://github.com/clalancette/pycdlib \
After installing Python, run: `pip install pycdlib`

**pypng**\
For reading/writing PNG files.\
https://gitlab.com/drj11/pypng \
After installing Python, run: `pip install pypng`

**mkisofs**\
For writing the internal ISO files. [^1]\
A hassle-free Windows binary can be found here:\
https://web.archive.org/web/20250321223300/https://fy.chalmers.se/~appro/linux/DVD+RW/tools/win32 \
On Linux I've had success with `mkisofs` from cdrtools, and `genisoimage`, but `xorrisofs` does _not_ work.\
https://sourceforge.net/projects/cdrtools/files

**pngquant**\
For converting regular 8-bit PNGs to 256/16-color paletted PNGs.\
Only needed if modifying textures and you have no other way to save such PNGs.\
https://pngquant.org


# Preparation
1. Clone or download this repository.
2. Download and install the requirements.
3. Create a work directory somewhere. Around 50 GB of space will be needed to completely extract and rebuild Yakuza, or each single-layer disc of Yakuza 2, and some 85 GB for the dual-layer versions of Yakuza 2.
4. Edit the configuration file `yak_pref.ini`, and under the `[Path]` section, add the paths to the ISO you wish to extract/rebuild, the work directory, `mkisofs`, and `pngquant` if you need it. It's probably best to avoid spaces and any unusual, non-ASCII characters in the paths.

On extraction, a subdirectory will be created in the work directory according to the name of the ISO, so you can use the same base work directory if you extract multiple ISOs.
Take the following config file for example:
```
ISO = /path/to/yakuza_isos/Yakuza (USA).iso
WORK = /path/to/work_dir
```
This would result in the extracted ISO directory `/path/to/work_dir/yakuza_(usa)`.


# Extraction
Running `yak_extract.py` will start the extraction process. If no additional argument is supplied to the script, it will look for the config file `yak_pref.ini` in the same directory. Alternatively, you can call the script with:
```
yak_extract.py /path/to/custom_config.ini
```
This may be preferable if you're working with different ISOs or parameters, and don't want to edit the default config back and forth.

If you're curious about what it's doing, this is roughly the extraction process:
1. Extract the external/game ISO.
2. Decrypt the headers/metadata of the internal ISOs/CVMs.
3. Extract the internal ISOs, and consolidate the files for the dual-layer versions.
4. Extract the internal scene archives.
5. Convert all the text/subtitles from the scene files to plaintext using known character hashes, and extract all the bitmap characters used.
6. Consolidate all the text files to only include duplicate lines once, since the game structure contains a staggering amount of redundancy, which would otherwise make text editing unmanageable.
7. Extract and convert specific textures to PNGs. [^2]

If the extraction process happens to crash or fail, there is a rudimentary resume function if you run it again with the same config.

# Extracted Structure
After extraction, you should have a directory corresponding to the specified ISO in your work directory, and under that a few subdirectories:\
\
`/internal`\
Internal storage for necessary intermediate files and metadata from the extraction process. Better to not dig too much here, since the rebuild process _will_ break if anything is missing or different from what's expected.\
\
`/rebuild`\
Where all the levels of extracted/encrypted/decrypted/rebuilt ISOs and their immediate contained files will be placed. This will take up most of the space on disk. Also recommended to not change anything here.\
\
`/resource`\
Where all the extracted and modifiable resources will be placed.

# Modifying Text
Text files will be collected in the `/resource/talk` directory. Under `/talk_work` you will find a structure of directories and text files, which is what you want to edit. The files there will contain all of the unique lines, mostly consolidated to avoid having to translate or edit duplicate lines multiple times.

The files will be categorized as containing either character names, or lines of dialogue/text, which will be apparent from the filename. For names, the maximum number of characters you can use is 24. For lines there is no real limit, but you will probably want to make sure they don't go outside the intended bounds of dialogue boxes and menus.

Most of the game versions will only extract one language set since that's all they contain, however the EUR version of Yakuza contains multiple languages, which will all be extracted. They will be placed in separate files with a two-letter language identifier in the filename, so you can edit the language set you wish, and ignore the others.

## Text Layout
The layout of the text files will look something like this:
```
0_1_5     ::: .{PA:20}.{PA:20}.{PA:20}What the hell was that all about?{PA:20}
0_2_0     ::: Hello?{PA:20}||Is this Mr.{PA:20} Kiryu?{PA:20}
0_2_1     ::: When do you plan on returning that 200K?{PA:20}||With interest,{PA:10} you're up to 401,{PA:10}000 now.{PA:20}
0_2_2     ::: Either you pay it back STAT,{PA:10} or you'll||start getting houseguests
0_2_3     ::: that start with a "Y".{PA:20}
```
Each line will start with a line identifier, e.g. `0_2_1` [^3], followed by a separator `:::` surrounded by spaces, and then the actual line of text.

The identifiers are critical to the rebuild process, so take care not to accidentally lose or modify them. Make sure there is a single space between the separator and the beginning of the line. Any additional spaces after that will be counted as part of the line.

The encoding of the text files will be UTF-8, and you should ensure that doesn't get changed during editing.

## Special Tags
There are a number of special tags used throughout the text files:

` ||            `\
Adds a line break at that position. Note that this tag is not used for cutscene subtitles, those are instead separated with an incremented line number in the identifier, e.g. `3_0_0` and `3_0_1` will presented as a subtitle with a line break. [^4]

` {PA:##}       `\
Adds a pause in the typewriter flow, the length of which is determined by the number. The standard is 10 for short pauses after commas, and 20 for long pauses after periods.

` {CC:######}   `\
Changes the text color according to the number, which is a standard RGB hex code.

` {CR:00}       `\
Reverts the color change of the previous `{CC}` tag.

` {CU:######}   `\
Works similar to the `{CC}` tag. Not 100% sure what the difference is, but it's not used as often.

` {SP:#}        `\
Changes the typewriter speed according to the number. The default speed is 1, and 0 will make text appear instantaneously. Higher numbers will make it slower.

` {MR:00}       `\
Resets any text effects back to default, including `{CC}`, `{CU}`, and `{SP}` tags.

` ➿            `\
Placeholder symbol that signifies a full-width space. [^5] The difference between this and using two regular spaces, is that the typewriter speed will be faster with the former, since it's calculated per character, regardless of whether they're half- or full-width.

` ❎            `\
Placeholder symbol that signifies a character that the extraction process couldn't identify. This tool contains known hashes for all the character bitmaps used by the official JP/US/EUR/KR versions of the games, so if you see this, you've likely tried to extract some other version.

` {IC:##_##}    `\
Inserts a specific bitmap icon into the line, often for doing button prompts. Usually followed by a ➿ to create a wide placeholder space for the icon. No need to modify these.

` {MS:#}        `\
Adds some kind of action defined elsewhere in the metadata. Sometimes it's for playing a sound effect at a specific time, but might be used for other stuff as well. I'm not 100% sure what they do in some cases, so best to just leave them roughly in the same position in a line.

` {NU:##_##_##} `\
Inserts a dynamic counter into the line, for example the amount of money needed for a purchase at a shop. Followed by a number of placeholder zeros. Best not to touch these either.

If you look closely at the text sample above, which is taken from the US release of Yakuza 2, you may notice some suspicious placing of _pause_ tags, e.g. `up to 401,{PA:10}000 now` or `Is this Mr.{PA:20} Kiryu?`.

This is most likely because they translated all the text without taking the pauses into account, and then simply ran a script that inserted short pauses after every comma, and long pauses after every period, regardless of whether it made any sense.

As the games make heavy use of ellipses, it also means there's a long pause between every single period for those, as seen in `.{PA:20}.{PA:20}.{PA:20}What the hell` above. This gets fairly tedious when playing, so I suggest removing the extraneous ones, and shortening the pause duration for ellipses significantly.

## Text Consolidation
The extraction process will mostly consolidate the text files for editing, by removing identical/duplicate lines. As an example, the raw extraction of all the text in Yakuza 2 contains about 350,000 lines, while the consolidated set only contains about 40,000 lines, so far more manageable to edit.

### Basic Process
Say there is a specific line of dialogue that is identical across 30 different files. In the consolidated set, there will be one file that is considered the _master_ for that line, which will include that line so you can edit it. For the 29 other files, that line will simply be missing.

During rebuild, that duplicate line will be sourced from the master file and propagated back into the proper places in the other files, recreating the redundancy. This way you only have to translate or edit the line once, instead of 30 times.

### Bypass Option A
However there will likely be situations where translating or editing a specific line in one place doesn't work grammatically or stylistically when it's being transferred to another place. So next to the structure of consolidated text files, under `/talk_original`, you will find a mirror set that contains the original, non-consolidated text files, named `full`, along with files that describe exactly which lines are duplicates, and where they are being sourced from, named `dup`.

You can manually copy over any lines, including the identifier and separator, from the original `full` file to the consolidated work file, and those lines will no longer be replaced using the master during rebuild.

### Bypass Option B
Another option is to create an override for a duplicate line. Imagine the previous example of a duplicate line across 30 files, but you're in the unfortunate situation where you want to edit it in a specific way in the master file that happens to include it, and edit it in a different way for the 29 other files.

Instead of manually copying and editing that line over to the other files 29 times, essentially undoing the consolidation process, you can create an override that includes only that line.

Next to the `full` and `dup` files, there will be a third file called `override`, which will be empty by default. Copy that file from the `/talk_original` directory of the master file, to the corresponding `/talk_work` directory, and copy over and edit the line the way you want it to be for the 29 other files. The master file will then use the line as you've edited it in the main work file, while the 29 other files will source that line from the override file during rebuild.

The override file essentially becomes the new master, and this way you only have to edit the line twice, once in the master, and once in the override, instead of in 30 different places.

### Limited Consolidation
In order to minimize the above situations where a line happens to be identical but is used in different contexts, duplicate lines are only consolidated within the same `MEDIA` archive. So a file under `MEDIA3` will never source a line from a file in `MEDIA`. Some files, for example certain menus, also have limited or no consolidation applied, as it's not worth the mess. Cutscene subtitles are also not consolidated at all.


# Modifying Character Bitmaps
If, when editing the text, you need to use some characters that aren't available originally, or you wish to replace some of them, you can put your own character bitmaps in `/resource/char/char_work`, and those will be used instead during rebuild.

The files need to be PNGs named the decimal Unicode code point for that character. For example, if you wish to use or replace the character `ç`, save your PNG there as `231.png`. For the character `¿`, save it as `191.png`.

Half-width characters should be 12x24 in resolution, and full-width characters 24x24. The character bitmaps in the games are only of 2-bit colordepth, meaning four colors: white, black, and two shades of grey. If your bitmaps haven't been saved as or optimized for that format, they will be crudely crunched down to those colors in the rebuild process.

After extraction, you can find all the character bitmaps in `/resource/char/char_original` for reference, and it might be helpful to know that the standard font used for the US/EUR versions is called _Rodin_, by _Fontworks_.

Note also that not all versions of the games contain the same set of characters. For example, the US and EUR versions of Yakuza include many more special European characters than the Yakuza 2 equivalents.

So if you need those characters for translating Yakuza 2, you may want to extract Yakuza separately, and copy them over from there to `/resource/char/char_work` of your Yakuza 2 work directory, instead of creating them yourself.


# Modifying Images
Images/textures will be collected in the `/resource/image` directory. Under `/texture_original` you'll find regular textures, and under `/talk_icon_original` you'll find the icons that sometimes appear in dialogue and running text.

Each of these have a corresponding mirror `work` directory. If you wish to replace a texture, simply put your edited version with the exact same filename, and the exact same relative path, in the `work` directory, and it'll be picked up during rebuild.

### Paletted Bitmap Format
The texture bitmaps in the game primarily come in two variants: 8-bit files with a 256-color palette, and 4-bit files with a 16-color palette, both with alpha transparency. During extraction they will be converted to equivalent PNGs, and while most image applications will be able to open these paletted variants correctly, not all of them can work with and save them as such.

If you can work in the paletted mode while editing them, you don't need to do anything else. On the other hand, if your application forces regular 8-bit per RGBA subpixel (32-bit total) when saving PNGs, the images will first need to be compressed/re-palettized using `pngquant` from the requirements.

This will automatically be done during rebuild for any edited images that don't match the original bitdepth/palette format. If a discrepancy is detected and `pngquant` isn't available, that image will be skipped.

### Half-Scale Transparency
Another thing to be aware of is that in order to save on palette colors, for most images the maximum alpha transparency value used will only be half of the maximum possible value. So in a 256-color image for example, a fully opaque pixel will typically only have an alpha value of 127, which means such images may appear semi-transparent when bringing them into image applications.

You'll either have to work with them like that, or scale up the alpha values, and then scale them back down again when you're done. Same if you create images from scratch. If you leave the alpha values at full scale, semi-transparent edges will look too hard and crunched when in-game, and you may get worse banding/posterization when re-palettizing the image.


# Modifying Movies
There is no particular support for modifying the cutscene video files in this tool, but if you intend to edit them manually, there is functionality to automatically replace them during rebuild. Under `/resource/movie/movie_original` you will find a directory structure containing the pre-rendered cutscenes.

Once you have a modified version of a video file, place it with the exact same name and relative path in one of the `work` directories, and it will be picked up during rebuild. Which directory to use will depend on your video properties and rebuild options.

`/movie_work_4x3`\
Most of the original videos will be 512x288 resolution, with playback optimized for 4:3 mode. If you intend to use that format, place your modified videos here.

`/movie_work_16x9`\
It is possible to optimize video playback for 16:9 mode. If so, you will need to re-encode all 512x288 videos to anamorphic 512x384 resolution, place them here, and then enable `WIDESCREEN_MODE` in the rebuild options.

`/movie_work_4x3_lite`\
If you intend to also rebuild an alternate version of the game with low-bitrate videos playable through USB on a PS2, you can place those files here if you've used the original 4:3-optimized 512x288 format. Then, enable `LITE_MODE` in the rebuild options.

`/movie_work_16x9_lite`\
Same as above, but if you've re-encoded the 512x288 videos to the 16:9-optimized 512x384 format. Enable both `WIDESCREEN_MODE` and `LITE_MODE` in the rebuild options, and they will be picked up from here.

The container format for the video files is SFD, with MPEG2 video and ADX audio. You can demux them using `ffmpeg`, and remux them using `Sfdmux`.


# Modifying Voices
There are two automatic voice modifications supported in this tool:

### Yakuza English Dub
For the US/EUR versions of Yakuza, there is the option to replace the English dub with the original Japanese voices.

To do so, you will first need to extract either the JP or KR version of the game separately. Copy over everything from `/resource/voice/voice_original` of that extraction, to `/resource/voice/voice_work` of your target version. Make sure the relative paths remain exactly the same. In the rebuild options, enable `REPLACE_VOICE_JP`.

### Yakuza 2 Korean Lines
For the US/EUR/JP versions of Yakuza 2, there is the option to replace the original Korean voice lines, which supposedly were hilariously awful if you know the language, with the re-recorded ones from the KR version of the game.

To do so, you will first need to extract both discs of the KR version separately, and copy over everything from each of the `/resource/voice/voice_original` directories, to `/resource/voice/voice_work` of your target version. Make sure the relative paths remain exactly the same.

Some files exist on both discs, so when copying them over you might get asked if you want to replace them. It doesn't matter what you choose there, as the files are identical. In the rebuild options, enable `REPLACE_VOICE_KR`.

There are also two pre-rendered cutscenes containing re-recorded Korean lines:\
`/MEDIA5/MOVIE2/C01/SCENE_01_0015.SFD`\
`/MEDIA5/MOVIE2/C13/SCENE_13_0105.SFD`

You will want to copy those from `/resource/movie/movie_original` of the KR extractions, to `/resource/movie/movie_work_4x3` of your target version as well, or otherwise make use of them if you're modifying the video files.

# Modifying Generic Files
If you have any other file replacements you want to include in the rebuild, that aren't specifically covered in the previous steps, you can place those in `/resource/generic`. The directory `/arc_work` is for files inside the `.ARC`/`.DAT` scene archives, and the relative paths should mirror what's been extracted to `/internal/arc/arc_orig` for the replacement files to be picked up. The directory `/files_work` are for files inside the internal ISOs, and the relative paths should mirror what's been extracted to `/rebuild/d_files_orig/layer_merge`.

# Rebuilding
The more resources and parts of the game you decide to rebuild, the longer the process will take. During testing, it's therefore advisable to limit the rebuild process to the parts you're currently working on, so you can iterate faster.

For example, if you're translating and testing all the menu text, you can choose to only enable processing of the `TALK` resource type, as well as limit it to `MEDIA` archive number `1`, which is the internal archive where the text for the menus exist.

Once you're happy with that and ready to move on to the cutscene subtitles for instance, you can switch it to only process `MEDIA` archive number `2`, which is where the subtitles exist. The previously modified menu files will then still be included, without having to rebuild that archive every time.

### Rebuild Options
Edit the config `yak_pref.ini`, and under the `[Rebuild]` section, set your rebuild options. Most of these will be booleans that can be set to `True/False` or `1/0`, while `REBUILD_MEDIA` and `REBUILD_RESOURCE` expect comma-delimited strings. You can comment lines using `#` or `;`.

` CLEAN_REBUILD    `\
The rebuild process creates a lot of intermediate files, which as mentioned can be used to speed up subsequent rebuilds. During testing however, you may eventually lose track of what has been done and when, or which state the files are in.

Enabling this option deletes all intermediate files and rebuilds the entire ISO from scratch. This takes longer, but is recommended before the final playtest and for the final rebuild, to avoid any mistakes from unintentional leftover test files. Note that it does not touch any files under `/resource`, so modifications done there are safe.

` REBUILD_MEDIA    `\
Defines which of the major `MEDIA` archives to process. Limiting this will speed up the rebuild.

For Yakuza (US/JP/KR), the archives contain the following modifiable resources:
```
1 - UI/HUD/menu text and textures. Text for shops/tutorials/etc. Combat voices.
2 - Cutscene subtitles and some minigame text. Pre-rendered cutscenes/videos. Cutscene voices.
3 - Text for most of the in-game dialogue.
4 - Nothing.
```
For Yakuza (EUR), the archives contain the following modifiable resources:
```
1 - UI/HUD/menu textures. Most menu/in-game text. Combat voices.
2 - Cutscene subtitles and some minigame text. Pre-rendered cutscenes/videos. Cutscene voices.
3 - Nothing.
4 - Nothing.
```
For Yakuza 2, the archives contain the following modifiable resources:
```
1 - UI/HUD/menu text and textures. Text for cabaret/shops/tutorials/etc.
2 - Cutscene subtitles and some minigame text. Cutscene voices.
3 - Text for most of the in-game dialogue.
4 - Nothing.
5 - Pre-rendered cutscenes/videos.
```

` REBUILD_RESOURCE `\
Defines which resource types to process. Limiting this will speed up the rebuild.
```
TALK: All types of text, plus icons embedded in the text files.
IMAGE: All types of images/textures, except text icons.
MOVIE: Cutscenes/videos.
GENERIC: Any other manually-modified files.
```

` FLATTEN_ISO      `\
Only relevant for the dual-layer versions of Yakuza 2, which is US/EUR, and the JP re-release. Flattens the game to a single layer, which saves a lot of space and speeds up the rebuild. Highly recommended, but the resulting ISO may not be burnable to a disc.

` WIDESCREEN_MODE  `\
Improves the playback quality of videos in 16:9 mode, at the slight expense of the 4:3 mode. Requires all 512x288 videos to be re-encoded in anamorphic 512x384 resolution.
If enabled, will look for replacement files under `/resource/movie/movie_work_16x9`, otherwise `/resource/movie/movie_work_4x3` will be used.

` LITE_MODE        `\
Simple convenience option, if you also intend to rebuild an alternate version of the game with low-bitrate videos playable through USB on a PS2.
If enabled, will look for replacement files under `/resource/movie/movie_work_16x9_lite` or `/resource/movie/movie_work_4x3_lite`, depending on the `WIDESCREEN_MODE` option above.

` RAISE_SUBTITLES  `\
Moves the cutscene subtitles a bit higher up on the screen, which looks more sensible in the 16:9 mode, but may not be desirable in 4:3, since the subtitles won't be fully inside the letterbox.

` REPLACE_VOICE_JP `\
Only relevant for the US/EUR versions of Yakuza. Replaces the English dub with the original Japanese voice files.

` REPLACE_VOICE_KR `\
Only relevant for the US/EUR/JP versions of Yakuza 2. Replaces the original Korean voice lines with the re-recorded ones.

` BLUE_KIRYU_TALK `\
Only relevant for the US/EUR versions of Yakuza 2. For whatever reason, the default color of Kiryu's dialogue lines is white in these versions. Enabling this option makes the default color blue, like on every other Y1/Y2 version.

` OPENING_SUB `\
Only relevant for the US/EUR versions of Yakuza. Enables adding subtitles to the opening/trailer that plays after the Sega logo. The text file in `/resource/talk/talk_work/MEDIA2/AUTHOR/OPENING/OPENING_MOVIE.DAT` is what you want to edit, but it will only have an empty structure for the subtitles after extraction, so you'll have to fill in/translate the lines yourself.

### Rebuild Process
Running `yak_rebuild.py` will start the rebuild process, and it works the same way as the extraction script with regards to the config. With no argument supplied it will look for `yak_pref.ini` in the same directory. Or you can call it with:
```
yak_rebuild.py /path/to/custom_config.ini
```

After the process is done, you will find the rebuilt ISO in  `/rebuild/a_iso_mod`.

If the process fails critically, you will hopefully get an error message hinting at what went wrong and during which step, for example a mistake with the line identifiers, or failure to call an external application. You may also see warnings, for example if a bitmap character has not been supplied, or a modified image is the wrong resolution or missing the alpha channel.


# Final Notes
I hope this tool will be of use, through more translation patches of the Yakuza games, or in some other way. If you find any bugs let me know, or if you run into an issue you can't seem to figure out, reach out and I might be able to help.

Special thanks to the following, without whose work in compression/encryption, a field far beyond me, this project would not have gotten anywhere:\
\
**roxfan** for _cvm_tool_, partially ported to Python here.\
**Luigi Auriemma** for _QuickBMS_, and research related to game data extraction.\
**Haruhiko Okumura** for _LZSS.C_, ported to Python here.
[^1]: Because I've been unable to find a suitable ISO utility capable of creating working PS2 UDF ISOs, the resulting external ISO from this tool is created in a rather hacky manner. The old headers/metadata from the original ISO are used and updated with the modified file sizes/positions, then simply appended with the new data. This means it's likely not a 100% compliant ISO as I think there are some UDF checksum bytes that will be wrong, and obviously you can't add/remove any files compared to the original structure, but it seems to work fine on every system I've tried. I cannot vouch for burning actual discs however.
[^2]: By default, this tool will only extract files needed to create a translation, that is to say all the text files and select textures that contain text. It's possible to extract more files by editing `/yak/meta/extract_def.py` and `/yak/process/process_arc.py`, but this will make the rebuild process significantly longer, and it's also untested at this point.
[^3]: The lines are hierarchically grouped in the text structure, and the identifier consists of the main group, sub group, and line number for each line of text. This can sometimes be helpful to identify which lines in a text file belong together.
[^4]: If you want to add a line break to a subtitle that doesn't have it, you can duplicate the relevant line in the file, and change the line number in the identifier of the copy to `1`, e.g. `2_0_0` -> `2_0_1`, and split the text over those.
[^5]: There are two types of character bitmaps: half-width, which are typically used for Western characters, and full-width, which are twice as wide and used for the Japanese kana/kanji and other symbols. In the US/EUR versions, the full-width characters in use are primarily the emojis ❤ and ♪, as well as full-width space.
