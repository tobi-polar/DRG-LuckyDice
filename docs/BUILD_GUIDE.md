# Lucky Dice build guide

Hook signatures were read from the FSD-Template tag `v1.39.102179.0`. Nothing here has been run in the game yet.

Each item is marked:

- **[header]**: the function or property exists in the template headers, but its behaviour is untested.
- **[game]**: an asset or value read from the installed game's pak with FModel.
- **[engine]**: a standard Unreal feature.
- **[find]**: still has to be located in FModel or the editor.

## 1. Setup

1. Install **Unreal Engine 4.27.2** from the Epic launcher. Put it on D:, as C: has only 26 GB free, and remove the optional components.
2. Open `FSD.uproject` in `FSD-Template-1.39.102179.0`, next to this repo. The project must stay named `FSD`.
3. If the project asks to rebuild modules and fails, install Visual Studio with "Desktop development with C++". It isn't installed on this PC, and the current README doesn't list it as required.
4. Create `Content/LuckyDice/` in the project.
5. Import `SourceAssets/dice.obj` as a static mesh and `SourceAssets/dice.png` as a texture. Build a material from the texture, adding a little emissive so the dice stands out.
6. Check the dice's size and orientation in the viewport. The mesh is exported 30 units wide.

## 2. Assets

| Asset | Type | Job |
|---|---|---|
| `InitCave` | Actor | Starts the mod. The game spawns it automatically at mission start. |
| `BP_DiceManager` | Actor, replicated, always relevant | Drop rolls, event rolls, position history, event logic |
| `BP_DicePickup` | Actor, replicated | The dice in the world |
| `STE_Dice_Speed`, `STE_Dice_Slow` | `StatusEffect` children | Speed changes |

Don't put Child Actor Components on `InitCave`. The modding guide warns against it, so have it spawn the manager instead.

**Stand-ins for game assets**

To reference a game asset in the editor, create an empty asset with the same type, name and path. The game's real asset is used at runtime. Keep these folders in **Directories to never cook**, so your empty copies never ship and overwrite the real ones.

| Stand-in path under `Content/` | Type |
|---|---|
| `GameElements/PawnStats/PST_MovementSpeed` | `PawnStat` |
| `GameElements/PawnStats/PST_MovementSpeedEnvironmentalPenalty` | `PawnStat` |
| `Enemies/Waves/WaveControllers/EWC_Generic` | Blueprint, parent `EnemyWaveController` |

## 3. Milestone 1: one dice, one event, solo

**`InitCave`**
- BeginPlay → `Is Server` → Branch → true: `Spawn Actor From Class (BP_DiceManager)`.

**`BP_DiceManager` drops**
1. BeginPlay: `GetFSDGameState` **[header]** → bind `OnEnemyKilledEvent` **[header]**. It passes `enemyTags` and `killedEnemy`.
2. If it doesn't fire on the host, use `GetFSDGameMode` → `EnemySpawnManager` → `OnEnemyDied`, which passes `enemy` **[header]**.
3. On a kill: stop if the cooldown is running or a dice already exists. Then roll the drop chance and spawn `BP_DicePickup` at `killedEnemy`.

Starting values, to tune by playing:

| Setting | Value |
|---|---|
| Drop chance | 2.5% |
| Cooldown | 25 s |
| Max dice at once | 1 |
| Lifetime | 60 s |

**`BP_DicePickup`**
- Replicates on, Replicate Movement off.
- Static mesh, a sphere overlap of about 150 units, and a Rotating Movement component **[engine]**.
- Set Initial Life Span to the dice lifetime **[engine]**.
- On overlap: `Has Authority` → cast the other actor to `PlayerCharacter` → stop if a roll has already started → tell the manager to roll for that player → destroy the dice.

**First event: Full Ammo**
- `Get All Actors Of Class (PlayerCharacter)` **[engine]** → get each `InventoryComponent` → `Resupply(1.0)` **[header]**.

**Pass:** kill bugs until a dice drops, walk over it, and your ammo refills.

## 4. Milestone 2: remaining events

All event logic runs on the server except rapid fire. `TryPushActiveStatusEffect` and `Resupply` are authority-only, and running events only on the server keeps every player's result the same.

| Event | Who | How | Still to check |
|---|---|---|---|
| Nuke | All enemies | `GetFSDGameMode` → `EnemySpawnManager.FindEnemiesByClass(Pawn, isSwarmer)`, once with each `isSwarmer` value → get each `HealthComponentBase` → `Kill(causer)` **[header]** | Whether the `Pawn` class matches every enemy. Decide on bosses and lootbugs. |
| Full ammo | Team | `InventoryComponent.Resupply(1.0)` **[header]** | Whether throwables need `ResupplyGrenades` too **[header]** |
| Speed boost | Team | `TryPushActiveStatusEffect(STE_Dice_Speed, player, manager)` **[header]** | How strong `StatChange` feels |
| Half speed | Team | The same call with `STE_Dice_Slow` | Whether 0.5 gives half speed |
| Rapid fire | Team | Multicast from the server. Each client raises `RateOfFire` on its own dwarf's `AmmoDrivenWeapon` items, then restores it. **[header]** | **Highest risk.** See below. |
| Wave spawns | Team | `GetFSDGameMode` → `GetWaveManager` → `TriggerWave(EWC_Generic)` **[header] [game]** | Whether it spawns correctly in every mission type |
| Random teleport | Picker | Set Actor Location with Teleport on, using the position history below **[engine]** | Client movement correction |
| Swap positions | All alive | Save all positions first, then move each player to the next player's position, with Sweep off and Teleport on **[engine]** | As above. With 3 or 4 players, this rotates them in a loop. |

**Status effects**

Copy the setup from the game's own effects. Each is a `StatusEffect` child with one `StatChangeStatusEffectItem` in its `StatusEffects` array:

| Our effect | Copied from | `Stat` | `StatChange` | Other settings |
|---|---|---|---|---|
| `STE_Dice_Speed` | `STE_ScoutSpeedBoost` **[game]** (uses 1.5, 2.5 s) | `PST_MovementSpeed` | Start at 1.0 | `Duration` 20, `RefreshDurationOnApplication` on |
| `STE_Dice_Slow` | `STE_ElecticPlant_slowdown` **[game]** (uses 0.3) | `PST_MovementSpeedEnvironmentalPenalty` | Start at 0.5 | `Duration` 15, `RefreshDurationOnApplication` on |

The game's values show which stats to use, but not exactly how they scale, so measure them in game. Armor perks or mods that reduce environmental penalties may weaken the slow.

**Rapid fire**

The `PST_` stats have no fire-rate entry, so a status effect won't do this. `AmmoDrivenWeapon` does have a `RateOfFire` property **[header]**, and firing appears to run on the player's own client, so the change likely has to happen there:

1. The server multicasts the event to everyone. This relies on every player having the mod, through `RequiredByAll`.
2. On each client, `GetLocalPlayerCharacter` **[header]** → `InventoryComponent.GetItem(category)` **[header]** for each weapon category → cast to `AmmoDrivenWeapon`.
3. Save each weapon's `RateOfFire`, multiply it, then restore the saved value when the timer ends.

Test this early, as the property might not change the real firing speed. Weapons that use their own fire logic, like `AutoCannon` with `MaxFireRate` **[header]**, may need separate handling. If it fails, use repeated `Resupply` as an "infinite ammo" event instead.

**Rolling**
- Keep an array of `{event, weight, enabled}` and pick by weighted random, as in the Survivor mod's `Roll()`.
- Set weights so the bad events start at about 30% of the total.

**Safe teleport points**

A random point could land inside rock, so only use places a dwarf has actually stood:

1. Every 5 s on the server, save each player's location if they're on the ground and alive. Keep the last 30.
2. For a teleport, pick a saved point at least 20 s old, preferably from another player and not close to the picker.
3. Digging or terrain changes can still leave a point unsafe, so test in small tunnels.

**When events can't roll**

Set an event's weight to 0 for the roll if:

| Event | Blocked when |
|---|---|
| Swap positions | Fewer than 2 living players, or any dwarf is carrying something, until this is tested |
| Teleport, swap, half speed | Extraction has started. `FSDGameState.OnCountdownStarted` **[header]** is the likely signal, so confirm it only fires for extraction. |
| Teleport, swap | The target is downed. Start with `PlayerCharacter.IsAlive` **[header]**, and confirm what it returns for a downed dwarf. |
| Teleport | There are no safe points yet |

**Announcements**
- Start with `FSDGameState.PostGameMessage(text)` **[header]**, so everyone sees the result in chat. Confirm clients receive it.
- A proper banner can come in milestone 4.

## 5. Milestone 3: multiplayer

1. Package using section 6.
2. Upload as a **hidden** mod on mod.io with the `RequiredByAll` tag. The modding guide says this makes everyone in the lobby have the mod.
3. Share it with a friend through a preview link, or add them as a moderator.

Check these from the **client's** side, not just the host's:

- [ ] The dice appears and spins for the client.
- [ ] A client's pickup triggers the event exactly once.
- [ ] Two players grabbing the dice at once only trigger one roll.
- [ ] Ammo and speed effects apply to clients and end correctly.
- [ ] Teleport and swap don't rubber-band.
- [ ] Waves, teleports and swaps don't break during extraction, while downed, or while on a zipline or platform.
- [ ] A client joining mid-mission doesn't cause errors.

## 6. Packaging

1. In Project Settings, turn off **Use Pak File** and **Share Material Shader Code**.
2. In **Directories to never cook**, remove any entry that blocks `LuckyDice`. Add `Character`, because the guide says cooking the dummied `BP_PlayerCharacter` crashes the game. Also add `GameElements` and `Enemies`, which hold the stand-ins.
3. Package for Windows (64-bit), or use the template's `DRGModdingAutomationScripts`.
4. Copy the cooked `Content` **and** `AssetRegistry.bin` into the DRGPacker input folder, then drag it onto `_Repack.bat`.
5. Rename the result `LuckyDice.pak` and place it at `FSD\Mods\LuckyDice\LuckyDice.pak`.

The guide warns that testing this way forces a sandbox save, so back up your saves first.

## 7. Milestone 4: polish

- Custom banner or countdown for active events
- Sound and particle effect on pickup
- Blink for the last 5 s of the dice's life, as in the Survivor mod
- In-game settings through ModHub, for weights and drop chance

## Open questions

- Does `v1.39.102179.0` still fully match the installed game (Steam build 26107973)? The assets above exist in the installed pak, but the C++ signatures come from the template. A mismatch would show up as a crash or a function doing nothing.
- What do Verified, Approved and Sandbox mean for players' saves and progression? The mod.io guidance pages weren't readable, so check them before release.

## References

- [Blueprint modding guide](https://drg-modding.github.io/docs/guides/blueprint-modding-guide.html)
- [Basic modding guide](https://drg-modding.github.io/docs/guides/basic-modding-guide.html)
- [FSD-Template](https://github.com/DRG-Modding/FSD-Template)
