# Lucky Dice build guide

Hook signatures were read from the FSD-Template tag `v1.39.102179.0`. Nothing here has been run in the game yet.

Each item is marked:

- **[header]**: the function or property exists in the template headers, but its behaviour is untested.
- **[engine]**: a standard Unreal feature.
- **[find]**: still has to be located in FModel or the editor.

## 1. Setup

1. Install **Unreal Engine 4.27.2** from the Epic launcher. Put it on D:, as C: has only 26 GB free, and remove the optional components.
2. Clone FSD-Template next to this repo, keep its folder name, and double-click `FSD.uproject`. The project must stay named `FSD`.
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

## 3. Milestone 1: one dice, one event, solo

**`InitCave`**
- BeginPlay → `Is Server` → Branch → true: `Spawn Actor From Class (BP_DiceManager)`.

**`BP_DiceManager` drops**
1. BeginPlay: `GetFSDGameState` **[header]** → bind `OnEnemyKilledEvent` **[header]**.
2. Check the delegate's parameters in the editor **[find]**. It needs to tell you which enemy died, for the drop location. If it doesn't, use `OnEnemyDied` on `EnemySpawnManager` **[header]**, which also needs a way to get that manager **[find]**.
3. On a kill: stop if the cooldown is running or a dice already exists. Then roll the drop chance and spawn `BP_DicePickup` at the enemy.

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

All event logic runs on the server. `PushActiveStatusEffect` and `Resupply` are authority-only, and running events only on the server keeps every player's result the same.

| Event | Who | How | Still to check |
|---|---|---|---|
| Nuke | All enemies | Get All Actors of the enemy base class, then apply lethal damage | Base class and damage call **[find]**. Exclude friendlies, and decide on bosses and lootbugs. |
| Full ammo | Team | `InventoryComponent.Resupply(1.0)` **[header]** | Whether throwables need `ResupplyGrenades` too **[header]** |
| Speed boost | Team | `StatusEffectsComponent.PushActiveStatusEffect(STE_Dice_Speed, Owner)` **[header]** | The speed `UPawnStat` asset **[find]**. Whether `StatChange` is additive. |
| Half speed | Team | The same call with `STE_Dice_Slow` | As above |
| Rapid fire | Team | Unknown. There's no confirmed fire-rate stat yet. | **Highest risk [find]**. Fallback: repeated resupply as "infinite ammo". |
| Wave spawns | Team | `EnemyWaveManager.TriggerWave(waveClass)` **[header]** | A suitable wave class and a way to get the manager **[find]** |
| Random teleport | Picker | Set Actor Location with Teleport on, using the position history below **[engine]** | Client movement correction |
| Swap positions | All alive | Save all positions first, then move each player to the next player's position, with Sweep off and Teleport on **[engine]** | As above. With 3 or 4 players, this rotates them in a loop. |

Status effect stat changes use `StatChangeStatusEffectItem`, which has `Stat`, `StatChange` and `AffectedByResistances` **[header]**.

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
| Teleport, swap, half speed | Extraction has started. The signal for this is **[find]**. |
| Teleport, swap | The target is downed. Check how to detect this **[find]**. |
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
2. In **Directories to never cook**, remove any entry that blocks `LuckyDice`. Add `Character`, because the guide says cooking the dummied `BP_PlayerCharacter` crashes the game.
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

- Is `v1.39.102179.0` the template for the game build installed here (Steam build 26107973)?
- What do Verified, Approved and Sandbox mean for players' saves and progression? The mod.io guidance pages weren't readable, so check them before release.

## References

- [Blueprint modding guide](https://drg-modding.github.io/docs/guides/blueprint-modding-guide.html)
- [Basic modding guide](https://drg-modding.github.io/docs/guides/basic-modding-guide.html)
- [FSD-Template](https://github.com/DRG-Modding/FSD-Template)
