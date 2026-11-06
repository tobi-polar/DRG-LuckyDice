# ModHub settings page

Lets the host set the drop chance, cooldown and forced event from [Mod Hub](https://mod.io/g/drg/m/mod-hub) in the Space Rig. Built and working: the page shows in Mod Hub and saves to `FSD/Saved/SaveGames/LuckyDiceSettings.sav`. Whether missions use the saved values hasn't been confirmed yet, and the page isn't available mid-mission.

The API comes from the Mod Hub author's install guide on the modding Discord. It is three Blueprint Interfaces:

| Interface | Contains | Used on |
|---|---|---|
| `IHubMod` | `GetModInfo` (`ModName`, `ModAuthor`, `ModVersion`), `GetModPages`, `ModRegistered`, `ModHubOpened`, `ModHubClosed` | `InitSpacerig`, so Mod Hub finds the mod |
| `IHubPageWidget` | `GetPageInfo` (`PageName`), `GetContainerMode` (`bStretchToContainer`), `HubPageOpened`, `HubPageClosed` | The settings page widget |
| `IHub` | `OpenHub`, `CloseHub`, `SelectPage`, `RefreshPages`, `RegisterKeybinding` | Mod Hub itself. Not needed yet |

Players without Mod Hub won't have these interfaces, so only `InitSpacerig` and the page use them. `BP_DiceManager` only reads the save, so the dice still work without Mod Hub, using their defaults.

## Steps

1. **API files.** Put `_ModHub` from the API zip in `Content`. Add `_ModHub` to **Directories to never cook**, as Mod Hub ships these files.
2. **Save.** In `Content/LuckyDice`, create a Blueprint Class with parent `SaveGame`, named `LuckyDiceSettings`. Add `DropChance` (Float, 0.025), `Cooldown` (Float, 45) and `ForceEvent` (Integer, -1).
3. **Loader.** Open `LuckyDiceSettings` once so it's loaded. Paste `tools/blueprint_paste/settings_loader.txt` into `BP_DiceManager`. Connect Event BeginPlay to the marked Sequence, and Then 1 to whatever BeginPlay used to run.
4. **Page.** Create a Widget Blueprint `WBP_LuckyDiceSettings`. In the Designer, add three Spin Boxes named `DropChanceBox`, `CooldownBox` and `ForceEventBox`, each with **Is Variable** on, plus labels. Suggested ranges: drop chance 0 to 1 (delta 0.005), cooldown 0 to 300, forced event -1 to 5 (delta 1).
5. **Page graph.** In Class Settings, add the `IHubPageWidget` interface. Add a variable `Settings` of type `LuckyDiceSettings` (Object Reference). Delete the greyed-out default event nodes, then paste `settings_widget.txt` into the Event Graph. In the interface functions, return `PageName` "Lucky Dice" from `GetPageInfo`, and leave `bStretchToContainer` off in `GetContainerMode`.
6. **Register.** Create an Actor Blueprint `Content/LuckyDice/InitSpacerig`. In Class Settings, add `IHubMod`. In `GetModInfo`, return the name, author and version. In `GetModPages`, create `WBP_LuckyDiceSettings` once, store it, and return it. Check what type the output pin wants first.

## Checks after pasting

- Class pins and casts that point at `/Game` assets can paste blank. Check the Cast nodes and `Create Save Game Object` say `LuckyDiceSettings`.
- The three On Value Committed events paste as plain Custom Events that never fire. Add the real ones from each Spin Box's **Events** list in the Designer, wire them to the matching SET (the Force Event one goes to Round), then delete the pasted ones.
- Spin Box's Set Value input is `NewValue`. The generator now uses that name.
- Put the Vertical Box straight in the page, or stretch it across its Canvas Panel, or Mod Hub shows it in a corner.
