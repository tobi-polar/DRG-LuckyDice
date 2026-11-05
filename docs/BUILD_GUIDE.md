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
5. Import `SourceAssets/dice.fbx` as a static mesh, plus `dice_BaseColor.png` and `dice_Normal.png`. Turn off material and texture creation in the FBX import dialog, then build `M_Dice` by hand.
6. Set `dice_Normal`'s compression to **Normalmap**, and consider setting Maximum Texture Size to 1024 on both textures, since the dice is small on screen.
7. In `M_Dice`, connect the base colour to Base Color, multiply it by about 0.3 into Emissive, and connect the normal map to Normal.
8. Check the dice in the viewport. It should be about 30 units wide. If the pips look raised instead of sunken, turn on **Flip Green Channel** on `dice_Normal`.

## 2. Assets

| Asset | Type | Job |
|---|---|---|
| `InitCave` | Actor | Starts the mod. The game spawns it automatically at mission start. |
| `BP_DiceManager` | Actor, replicated, always relevant | Drop rolls, event rolls, position history, event logic |
| `BP_DicePickup` | Actor, replicated | The dice in the world |
| `STE_Dice_Speed` | `StatusEffect` child | Speed Boost |
| `CF_Dice_NoHeat` | `CurveFloat`, one key at time 0, value 0 | Replaces weapons' `HeatCurve` during Rapid Fire. Set as the default of `NoHeatCurve` on `BP_DiceManager` |

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
| Nuke | Enemies under 3000 health | Save `EnemySpawnManager.FindEnemiesByClass(Pawn, isSwarmer)` to an array, once with each `isSwarmer` value. For each, get `HealthComponentBase`, check `GetHealth`, then `Kill(self)`. **[header]** | Whether this catches every enemy, and whether 3000 is the right limit for bosses and lootbugs |
| Full ammo | Team | `InventoryComponent.Resupply(1.0)`, then a multicast where each machine calls `AmmoDrivenWeapon.InstantlyReload`, then `Resupply(1.0)` again. On the host, set each `SentryGun.AmmoCount` to `GetMaxAmmoCount` + 1, then call `UseAmmo(1)` so the HUD updates. **[header]** | Whether magazines and turrets fill on clients, and whether throwables need `ResupplyGrenades` too **[header]** |
| Speed boost | Team | `TryPushActiveStatusEffect(STE_Dice_Speed, player, manager)` **[header]** | How strong `StatChange` feels |
| Rapid fire | Team | Multicast from the server. Each machine doubles `RateOfFire` on every `AmmoDrivenWeapon`, waits 15 s, then halves it again. To stop overheating, it saves `Item.HeatCurve` and swaps in `CF_Dice_NoHeat`, a flat curve at zero (an empty curve crashes the game when drills hit an enemy), scales `ManualHeatPerUse` and `HeatOnStartUse` by 0.001 and `CooldownRate` by 1000 for the duration, and clears `CurrentTemperature` and `overheated` every 0.1 s. `RateOfFire` doesn't change the Thunderhead's top speed (a mag took 20 s either way), so its `AutoCannon.MaxFireRate` is doubled, and `StartingFireRate` is set to match to skip the spin-up. Both are restored afterwards. The Cryo Cannon's `CryosprayItem.PressureDropMultiplier` is scaled by 0.001 for the duration, because it cuts out on low pressure rather than heat. `DoubleDrillItem` isn't an `AmmoDrivenWeapon`, so the drills get the same heat changes through their own list. Every 0.1 s, any weapon at half a magazine or less is topped up from reserves with `InstantlyReload`, to skip reload animations. **[header]** | Works in solo tests. Minigun: no heat for 15 s, then heat builds again. Thunderhead: a mag takes about 10 s instead of 20. Flamethrower: skipping reloads makes it useful. Cryo Cannon: no longer cuts out. A second roll in one mission works. Multiplayer is untested |

The bad events moved to a separate mod. See [UNLUCKY_DICE.md](UNLUCKY_DICE.md).

**Planned events**

In build order, once Rapid Fire is tested. None of these has been built or run in the game.

| Event | Who | How | Still to check |
|---|---|---|---|
| Regen | Team | A new status effect using `HealingStatusEffectItem` **[header]** | How much to heal per second, and for how long |
| Freeze All | Enemies | Loop over enemies like the Nuke, aiming for 10 s, possibly with `EnemyTemperatureStatusEffectItem` **[header]** | How freezing is applied, and whether tough enemies thaw early |
| Jump Boost | Team | Each machine raises `JumpZVelocity` **[engine]** for about 20 s, then restores it | Whether the game's movement uses it, and whether landing causes fall damage |
| 1-Hit Mining | Team | Each machine raises `PickaxeItem.RockMiningBonus` and `DirtMiningBonus`, or sets `QuadDamageCarving`, for about 30 s **[header]** | What each setting does, and whether it reaches one hit on every material |
| Team Revive (maybe) | Downed players | Only in the pool while someone is down, using `PlayerCharacter.InstantRevive` or `Server_CheatRevive` **[header]** | Whether these can be called from our code |

With eight events at equal odds, each has a 12.5% chance per dice, so consider weighting them.

**Status effects**

Copy the setup from the game's own effects. Each is a `StatusEffect` child with one `StatChangeStatusEffectItem` in its `StatusEffects` array:

| Our effect | Copied from | `Stat` | `StatChange` | Other settings |
|---|---|---|---|---|
| `STE_Dice_Speed` | `STE_ScoutSpeedBoost` **[game]** (uses 1.5, 2.5 s) | `PST_MovementSpeed` | Start at 1.5 | `Duration` 20, `RefreshDurationOnApplication` on |

In game, a `StatChange` of 3 is extremely fast. Whether the value is a multiplier is still unconfirmed, so tune it by feel.

**Rapid fire**

The `PST_` stats have no fire-rate entry, so a status effect won't do this. `AmmoDrivenWeapon` does have a `RateOfFire` property **[header]**, and firing appears to run on the player's own client, so the change likely has to happen there:

1. The server multicasts the event to everyone. This relies on every player having the mod, through `RequiredByAll`.
2. On each machine, save every `AmmoDrivenWeapon` to `RapidFireWeapons` and multiply each weapon's `RateOfFire`.
3. When the timer ends, divide the rate on the saved weapons only. `RapidFireActive` makes a second roll mid-effect do nothing, so the rate can't stack.

Test this early, as the property might not change the real firing speed. Weapons that use their own fire logic, like `AutoCannon` with `MaxFireRate` **[header]**, may need separate handling. If it fails, use repeated `Resupply` as an "infinite ammo" event instead.

**Rolling**
- Keep an array of `{event, weight, enabled}` and pick by weighted random, as in the Survivor mod's `Roll()`.

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
- [ ] A client joining mid-mission doesn't cause errors.

## 6. Packaging

1. In Project Settings, turn off **Use Pak File** and **Share Material Shader Code**.
2. In **Directories to never cook**, remove any entry that blocks `LuckyDice`. Add `Character`, because the guide says cooking the dummied `BP_PlayerCharacter` crashes the game. Also add `GameElements` and `Enemies`, which hold the stand-ins.
3. Package for Windows (64-bit), or use the template's `DRGModdingAutomationScripts`.
4. Copy the cooked `Content` **and** `AssetRegistry.bin` into the DRGPacker input folder, then drag it onto `_Repack.bat`.
5. Rename the result `LuckyDice.pak` and place it at `FSD\Mods\LuckyDice\LuckyDice.pak`.

The guide warns that testing this way forces a sandbox save, so back up your saves first.

## 7. Milestone 4: polish

- Announce each event with its own banner and a sound or visual flourish
- On-screen timer for events with a duration
- Sound when a dice drops
- Sound and particle effect on pickup
- Dwarf voice line on pickup. The game has `DialogDataAsset` shouts **[header]**, so look through them in FModel for ones that fit
- Blink for the last 5 s of the dice's life, as in the Survivor mod
- In-game settings through ModHub, for weights and drop chance

## Open questions

- Does `v1.39.102179.0` still fully match the installed game (Steam build 26107973)? The assets above exist in the installed pak, but the C++ signatures come from the template. A mismatch would show up as a crash or a function doing nothing.
- What do Verified, Approved and Sandbox mean for players' saves and progression? The mod.io guidance pages weren't readable, so check them before release.

## References

- [Blueprint modding guide](https://drg-modding.github.io/docs/guides/blueprint-modding-guide.html)
- [Basic modding guide](https://drg-modding.github.io/docs/guides/basic-modding-guide.html)
- [FSD-Template](https://github.com/DRG-Modding/FSD-Template)
