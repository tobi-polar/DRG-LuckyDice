# Lucky Dice for Deep Rock Galactic

Enemies have a small chance to drop a golden dice. When a dwarf picks it up, a random event fires, and it might not be a good one. This is the multiplayer follow-up to the Lucky Dice mod for Deep Rock Galactic: Survivor.

**Status:** pre-production. No Blueprints have been built yet. Follow [docs/BUILD_GUIDE.md](docs/BUILD_GUIDE.md).

## Planned events

| Good | Bad |
|---|---|
| Nuke | Wave spawns |
| Full ammo | Half speed |
| Rapid fire | Random teleport |
| Speed boost | Swap positions |

## Repo layout

- `Content/LuckyDice/`: the mod's Unreal assets, copied from your FSD-Template project (added once built)
- `SourceAssets/`: the dice mesh and texture, ready to import
- `tools/`: helper scripts
- `docs/`: the build guide

The FSD-Template project and extracted game files stay out of this repo.
