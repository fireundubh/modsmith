# Modsmith by fireundubh

**Modsmith** is an automated framework for building and packaging _Kingdom Come: Deliverance_ mods.

[![Patreon](https://i.imgur.com/llPEyru.png)](https://www.patreon.com/fireundubh)


## Core Features

* Merges modified XML tables with vanilla XML tables at build time
* Generates zero-byte TBL files as needed at package time
* Automatically packages v1.3+ mods for ZIP distribution


## Using Modsmith

### Usage

To build and package a project, run:

```
modsmith.exe "/path/to/project_root/mod.manifest"
```

You can also drag and drop a `mod.manifest` file onto `Modsmith.exe` if the manifest is in your project root.


#### Notes

1. Modsmith requires all mods to have an [XML manifest file](http://wiki.tesnexus.com/index.php/Modding_guide_for_KCD#Mod_manifest).
2. Modsmith will use the `<name>` and `<version>` fields to generate the PAK and ZIP.
3. Ensure you save the manifest in the UTF-8 encoding without a BOM.


### How to Organize a Modsmith Project

```
E:\projects\kingdomcome\More Perks  (project root)
    \mod.manifest                   (required)
    \Data\Libs\Tables\rpg
        buff.xml                    (contains only mod data)
        perk.xml                    (contains only mod data)
        perk_buff.xml               (contains only mod data)
        perk_buff_override.xml      (contains only mod data)
        perk2perk_exclusivity.xml   (contains only mod data)
    \Localization\english_xml
        text_ui_soul.xml            (contains only mod data)
```

After building a Modsmith project, you'll find a `Build` folder in the project root. In that folder, you'll find the merged XML files, generated game data and localization PAKs, and a redistributable ZIP archive.


## Configuration

Modsmith will search the Windows Registry for _Kingdom Come_'s install path using the following keys:

* Galaxy Path: `HKEY_LOCAL_MACHINE/SOFTWARE/Wow6432Node/GOG.com/Games/1719198803/path`
* Steam Path: `HKEY_LOCAL_MACHINE/SOFTWARE/Microsoft/Windows/CurrentVersion/Uninstall/Steam App 379430/InstallLocation`


## Examples

### Projects

**More Perks** is [a good example of how Modsmith projects are structured and what their XML files contain](https://github.com/fireundubh/kingdomcome/tree/master/More%20Perks).

Other Modsmith projects include:

* [Easy Lockpicking](https://github.com/fireundubh/kingdomcome/tree/master/Easy%20Lockpicking) (GitHub)
* [Better Trainers](https://github.com/fireundubh/kingdomcome/tree/master/Better%20Trainers) (GitHub)
* [Unleveled Perks](https://github.com/fireundubh/kingdomcome/tree/master/Unleveled%20Perks) (GitHub)
