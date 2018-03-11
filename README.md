# Modsmith by fireundubh

![https://www.patreon.com/fireundubh](https://i.imgur.com/llPEyru.png)

## Features

* Automatically packages Kingdom Come: Deliverance mods for distribution
* Merges modified XML tables with vanilla XML tables at package time
* XML merger currently supports only perk and buff tables

## Requirements

* [Python 3.6.4](https://www.python.org/downloads/release/python-364/)
* [lxml 4.1.1](https://pypi.python.org/pypi/lxml/4.1.1) (To install: `pip install lxml`)

## Usage

* To use Modsmith, you will need to structure your mod similar to the screenshot below.
* Inside the project path, there should be a Data and Localization folder. Localization is optional. The `mod.manifest` file should also be placed at this level. The manifest file is required.
* The hierarchy for each folder should imitate the hierarchy needed for the mod.
* The Build folder will be created automatically.
* **IMPORTANT:** XML tables should contain ONLY the modified rows. Modsmith will effectively "import" the modified rows into the base tables at package time, and generate new XML files using your modified rows.

## Configuration

`app.conf` needs to be edited. `Path` should be set to the root path of the game.

### Example
```
# configuration file for modsmith

[Game]
Path = C:\Program Files (x86)\Steam\steamapps\common\KingdomComeDeliverance
```

## Arguments

Short | Long | Description
--- | --- | ---
`-p` | `--project` | Input project path
`-d` | `--data-package` | Output PAK file name
`-r` | `--redist` | Redistributable ZIP file name

## Example

This example assumes Modsmith has been zipped.

```
python modsmith.zip -p "E:\projects\KCD More Perks" -d "More Perks.pak" -r "More Perks.zip"
```

### Output

Modsmith will generate folders and files in the Build folder.

* The first folder that contains everything will be named after the mod, using the name of the redistributable ZIP without the extension (e.g., `More Perks.zip` becomes `More Perks`.)
* The data PAK will be generated in the Data folder and named using the value provided by the `-d` argument.
* The localization PAK, or multiple PAKs, will be generated in the Localization folder.
* Finally, the entire mod will be generated in the Build folder. This is the redistributable ZIP that can be uploaded to the Nexus or wherever. You should also use this ZIP to extract the mod to your Mods folder for testing.

![Example Output](https://i.imgur.com/jHpbhBJ.jpg)
