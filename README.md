# Modsmith

**Modsmith** is an automated framework for building and packaging _Kingdom Come: Deliverance_ mods.


## Features

* Automatically converts old-style table mods to new-style patch mods
* Automatically removes "identical to master" table rows from table patches
* Automatically replaces whitespace in mod folder names with underscores
* Automatically packages mods for ZIP distribution


## Usage

To build and package a project, run:

```
modsmith.exe "/path/to/project_root/mod.manifest"
```

You can also drag and drop a `mod.manifest` file onto `Modsmith.exe` if the manifest is in your project root.


### Notes

1. Modsmith requires all mods to have an [XML manifest file](http://wiki.tesnexus.com/index.php/Modding_guide_for_KCD#Mod_manifest).
2. Modsmith will use the `<name>` and `<version>` fields to generate the PAK and ZIP.
3. Ensure `mod.manifest` is saved with the UTF-8 encoding without a BOM.


## Organizing Projects

```
E:\projects\kingdomcome\More Perks  (project root)
    mod.manifest                   (required)
    Data\Libs\Tables\rpg
        buff.xml                    (contains only mod data)
        perk.xml                    (contains only mod data)
        perk_buff.xml               (contains only mod data)
        perk_buff_override.xml      (contains only mod data)
        perk2perk_exclusivity.xml   (contains only mod data)
    Localization\english_xml
        text_ui_soul.xml            (contains only mod data)
```

After building a Modsmith project, you'll find a `Build` folder in the project root. In that folder, you'll find the finalized data used to produce the ZIP.


## Configuration

Modsmith will search the Windows Registry for _Kingdom Come_'s install path using the following keys:

* Galaxy Path: `HKEY_LOCAL_MACHINE/SOFTWARE/Wow6432Node/GOG.com/Games/1719198803/path`
* Steam Path: `HKEY_LOCAL_MACHINE/SOFTWARE/Microsoft/Windows/CurrentVersion/Uninstall/Steam App 379430/InstallLocation`
