# Modsmith by fireundubh

**Modsmith** is an automated framework for building and packaging redistributable mods.

**Modsmith** allows you to focus on your projects, improves your productivity, and reduces the time and effort required to update your mods after major game patches.


[![Patreon](https://i.imgur.com/llPEyru.png)](https://www.patreon.com/fireundubh)


## Features

* Automatically packages _Kingdom Come: Deliverance_ v1.3+ mods for distribution
* Merges modified XML tables with vanilla XML tables at package time
* Generates zero-byte TBL files as needed at package time


## Using Modsmith

1. To use **Modsmith**, you will need to structure your mod project similar to the example below:
![Modsmith Project Structure](https://i.imgur.com/K0BSRuX.jpg)

2. Inside the project folder (e.g., `E:\projects\kingdomcome\More Perks`), there should be a Data folder and/or a Localization folder. **Modsmith** also supports Data-only mods and Localization-only mods (e.g., translations.)

3. The `mod.manifest` file should be placed in the root of the project path.

4. The hierarchy for each folder should imitate the hierarchy needed for your mod (e.g., `Localization\french_xml`.) If you've created mods for _Kingdom Come: Deliverance_ before, this process should already be familiar to you.

5. Ensure that your XML files contain **_ONLY_** the rows your mod adds or changes. With **Modsmith**, it is no longer necessary to work on massive XML files to create mods. When your mod is packaged, **Modsmith** will generate new XML files in the Build folder that combine your merged rows with the rows you didn't alter.

6. Run Modsmith with the appropriate command-line arguments.


## Configuration

Before running **Modsmith**, you will need to edit `modsmith.conf`. Don't worry! There is only one setting.

```text
# configuration file for modsmith

[Game]
Path = C:\Program Files (x86)\Steam\steamapps\common\KingdomComeDeliverance
```

Change the value of `Path` to wherever you installed _Kingdom Come: Deliverance_. It must be the game's root path!


## Arguments

There are three command-line arguments:

Short | Long | Description
--- | --- | ---
`-p` | `--project` | This is the absolute path to the root of your project (e.g., `E:\projects\kingdomcome\More Perks`.)
`-d` | `--data-package` | This is the file name of the data PAK file (e.g., `More Perks.pak`.)
`-r` | `--redist` | This is the file name of the redistributable ZIP file (e.g., `More Perks.zip`.)


## Examples

### Projects

**More Perks** is [a good example of how Modsmith projects are structured and what their XML files contain](https://github.com/fireundubh/kingdomcome/tree/master/More%20Perks).

Other Modsmith projects include:

* [Easy Lockpicking](https://github.com/fireundubh/kingdomcome/tree/master/Easy%20Lockpicking) (GitHub)
* [Better Trainers](https://github.com/fireundubh/kingdomcome/tree/master/Better%20Trainers) (GitHub)
* [Unleveled Perks](https://github.com/fireundubh/kingdomcome/tree/master/Unleveled%20Perks) (GitHub)

### Example Usage

I'll present this example as though you've never used a command-line program before:

```text
cd "C:\Modsmith"
modsmith -p "E:\projects\kingdomcome\More Perks" -d "More Perks.pak" -r "More Perks.zip"
```

If you have multiple editions of a mod:

```text
cd "C:\Modsmith"
modsmith -p "E:\projects\kingdomcome\Easy Lockpicking\Cheat" -d "Easy Lockpicking - Cheat.pak" -r "Easy Lockpicking - Cheat.zip"
```

**Modsmith** uses a relative path to `modsmith.conf`, so if you use an IDE like PyCharm or a .bat file, set the working directory to wherever you installed **Modsmith**. That's why we're `cd`'ing into the **Modsmith** install folder in these examples.

### Example Output

**Modsmith** will generate folders and files in the Build folder in your project root.

![](https://i.imgur.com/ySmeFqP.jpg)

What do you see?

* There is a `Build` folder, and there is a `More Perks` subfolder in the `Build` directory. This subfolder is named after the mod, using the file name (without the extension) passed to **Modsmith** with the `-r` argument.

* Inside this folder are the `Data` and `Localization` folders, which replicate the structure of the project.

* There is a PAK file in the `Data` folder, using the file name (without the extension) passed to **Modsmith** with the `-d` argument. This PAK file contains all the files in `Libs\Tables\rpg`.

* In the `Libs\Tables\rpg` folder, there are TBL and XML files. The zero-byte TBL files were generated automatically. Currently, you need these for XML mods to work. These XML files are the product of the packaging process. Compare them with your own in the project `Data` folder and you'll see that while your XML files contain only your modified rows, the XML files in the `Build` folder contain both your modified rows and all other rows.

* There is a PAK file in the `Localization` folder. Note that **Modsmith** can generate localization XML files and PAKs for _multiple languages_ simultaneously.

* Finally, there is a redistributable ZIP file in the root of the `Build` path. This ZIP contains only the files necessary for players to install your mod (i.e., folders and PAKs.) You can immediately upload this ZIP to the Nexus, or extract the ZIP to your own Mods folder for testing.
