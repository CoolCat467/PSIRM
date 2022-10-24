# PSIRM
PhotoShop Icon Resource Manager

Change image asset files used by PhotoShop

For example, you can change the startup splash screen, which is named `SplashBackground`.

Original at https://github.com/CoolCat467/PSIRM

Based on information from https://github.com/stevenvi/photoshop-resource-editor, which is licensed under the GNU General Public License Version 3

## Usage:
1) Go into your installation of PhotoShop's files and make backups of `IconResources.idx`, `PSIconsHighRes.dat`, and `PSIconsLowRes.dat`

2) Unpack data using the following command:
```console
python3 psirm.py unpack /path/to/folder/with/IconResources.idx /unpack/base/path
```
PSIRM will create `High` and `Low` folders in `/unpack/base/path` if they do not already exist and dump images from `PSIconsHighRes.dat` and `PSIconsLowRes.dat` in their respective folders.
Note: Folder file contents will not be identical, some images exist as only high resolution or as only low resolution.

4) Modify images as you wish as long as they are no larger in file size then the original. This is due to a limitation with the program, as it does not know how to change the icon header files properly

5) Re-pack images back into resource files with the following command:
```console
python3 psirm.py pack /path/to/folder/with/original/IconResources.idx /unpack/base/path
```
PSIRM will use the `High` and `Low` folders in `/unpack/base/path` to create modified resource files in a new folder in `/path/to/folder/with/original/IconResources.idx` named `modified`. The program still needs to read data from the original version of `IconResources.idx`, but will use that information to make a new version in `modified/IconResources.idx`, as well as new versions of  `PSIconsHighRes.dat` and `PSIconsLowRes.dat`.

## Disclaimers:
This program is not supported by Adobe and is not affiliated with them in any way. If you don't make backups of these files and skrew up your installation of PhotoShop using this program then it's not my problem or Adobe's. If you encounter any issues other than the fact you can't make replacement images be larger in file size than the original, please make a new issue describing what is going wrong.
