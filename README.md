# Lucky Dice for Deep Rock Galactic

Enemies have a small chance to drop a golden dice. When a dwarf picks it up, a random buff fires. This is the multiplayer follow-up to the Lucky Dice mod for Deep Rock Galactic: Survivor.

**Status:** in development. Dice drops and all six events work in solo: Max Ammo, Speed Boost, Nuke, Rapid Fire, Fortify and Freeze All. Multiplayer testing and more events are still to come. See [docs/BUILD_GUIDE.md](docs/BUILD_GUIDE.md).

## Planned events

- Nuke
- Full ammo
- Rapid fire
- Speed boost
- Fortify
- Freeze all

The bad events will be a separate mod, Unlucky Dice. See [docs/UNLUCKY_DICE.md](docs/UNLUCKY_DICE.md).

## Repo layout

- `Content/LuckyDice/`: the mod's Unreal assets, copied from the FSD-Template project
- `Content/GameElements/`, `Content/Enemies/`: empty stand-ins for game assets, needed in the editor but never packaged
- `SourceAssets/`: the dice mesh and texture, ready to import
- `tools/`: helper scripts
- `docs/`: the build guide

The FSD-Template project and extracted game files stay out of this repo.
