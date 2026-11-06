"""Generate BP_DiceManager's event logic as text to paste.

Usage: python make_roll_events.py <output.txt> --events | --logic | --reload-only | --rapid-chain | --curve-clear

--curve-clear writes just the node that empties RapidFireCurves.

--settings-loader writes the start of BP_DiceManager's BeginPlay, which copies saved ModHub
settings over the defaults. --settings-widget writes WBP_LuckyDiceSettings' event graph.

--debug-readout writes a loop for BP_DiceManager that posts changes in the host's health
and shield to chat, with whether Fortify and Regen are active. It needs the Boolean
DebugReadout (default on) and the Float DebugLastHealth.

--fortify-heal writes just Fortify's heal loop, which needs the Integer FortifyHealsLeft.
Connect the FORTIFY! message to it.

--unfreeze-only writes just the pass that unfreezes every enemy when Freeze All ends.
Connect the False of the Branch after FreezeTicksLeft counts down to it.

--freeze-only writes just the Freeze All box, which needs the Integer FreezeTicksLeft.
Connect the Fortify check's False to its Branch, and raise the Max on Random Integer In Range to 5.

--fortify-only writes just the Fortify box. Connect the Rapid Fire check's False to its
Branch, and raise the Max on Random Integer In Range to 4.

--reload-only writes just the DiceReloadAll event, to replace one that pasted with
the wrong name. Delete the old one and compile before pasting, so the name is free.

--rapid-chain writes everything DiceRapidFire runs, without the event itself. Keep the
event, delete what it runs, paste this, and connect the event to the marked Branch.

Paste into the Event Graph of BP_DiceManager, which needs the Integer variables
ForceEvent (default -1) and EventId, NukeTargets (Pawn array), RapidFireActive
(Boolean), RapidFireWeapons (Ammo Driven Weapon array), RapidFireCurves (Curve Float
array), RapidFireCannons (Auto Cannon array), RapidFireCannonRates (Float array),
RapidFireCryos (Cryospray Item array), RapidFireDrills (Double Drill Item array),
RapidFireDrillCurves (Curve Float array) and NoHeatCurve (Curve Float), whose default
must be set to the flat CF_Dice_NoHeat asset.
ForceEvent picks the event
for testing: 0 Max Ammo, 1 Speed Boost, 2 Nuke, 3 Rapid Fire, 4 Fortify, 5 Freeze All. Any negative value
rolls at random. Each event sits in its own comment box.

Paste in two parts, because a call pasted together with its event comes through broken:
1. Delete the old event logic, keeping the RollDice event and the drop logic.
2. Paste --events and compile.
3. Paste --logic, connect RollDice to the marked Branch, and compile.

After pasting, check the Status Effect pin on Try Push Active Status Effect. It can
come through blank with no compile error, so set it to STE_Dice_Speed by hand.
"""
import sys
import uuid

ACTOR = "Class'\"/Script/Engine.Actor\"'"
PLAYER = "/Script/FSD.PlayerCharacter"
INVENTORY = "/Script/FSD.InventoryComponent"
WEAPON = "/Script/FSD.AmmoDrivenWeapon"
SENTRY = "/Script/FSD.SentryGun"
PAWN = "/Script/Engine.Pawn"
HEALTH = "/Script/FSD.HealthComponentBase"
GAME_MODE = "/Script/FSD.FSDGameMode"
SPAWN_MANAGER = "/Script/FSD.EnemySpawnManager"
ITEM = "/Script/FSD.Item"
CURVE = "/Script/Engine.CurveFloat"
CANNON = "/Script/FSD.AutoCannon"
CRYO = "/Script/FSD.CryosprayItem"
DRILL = "/Script/FSD.DoubleDrillItem"
SETTINGS = "/Game/LuckyDice/LuckyDiceSettings.LuckyDiceSettings_C"
SETTINGS_SLOT = "LuckyDiceSettings"
SPINBOX = "/Script/UMG.SpinBox"
STRING = "/Script/Engine.KismetStringLibrary"
TYPES = {
    "character": ("object", "Class'\"/Script/Engine.Character\"'", None),
    "playerchar": ("object", f"Class'\"{PLAYER}\"'", None),
    "playerhealth": ("object", "Class'\"/Script/FSD.PlayerHealthComponent\"'", None),
    "status": ("object", "Class'\"/Script/FSD.StatusEffectsComponent\"'", None),
    "settings": ("object", f"BlueprintGeneratedClass'\"{SETTINGS}\"'", None),
    "savegame": ("object", "Class'\"/Script/Engine.SaveGame\"'", None),
    "savegameclass": ("class", "Class'\"/Script/Engine.SaveGame\"'", None),
    "spinbox": ("object", f"Class'\"{SPINBOX}\"'", None),
    "textcommit": ("byte", "Enum'\"/Script/SlateCore.ETextCommit\"'", None),
    "drill": ("object", f"Class'\"{DRILL}\"'", None), "drills": ("object", f"Class'\"{DRILL}\"'", "Array"),
    "cryo": ("object", f"Class'\"{CRYO}\"'", None), "cryos": ("object", f"Class'\"{CRYO}\"'", "Array"),
    "cannon": ("object", f"Class'\"{CANNON}\"'", None), "cannons": ("object", f"Class'\"{CANNON}\"'", "Array"),
    "floats": ("float", None, "Array"),
    "curve": ("object", f"Class'\"{CURVE}\"'", None), "curves": ("object", f"Class'\"{CURVE}\"'", "Array"),
    "item": ("object", f"Class'\"{ITEM}\"'", None),
    "pawn": ("object", f"Class'\"{PAWN}\"'", None), "fsdpawn": ("object", "Class'\"/Script/FSD.FSDPawn\"'", None), "pawns": ("object", f"Class'\"{PAWN}\"'", "Array"),
    "pawnclass": ("class", f"Class'\"{PAWN}\"'", None),
    "health": ("object", f"Class'\"{HEALTH}\"'", None),
    "gamemode": ("object", f"Class'\"{GAME_MODE}\"'", None),
    "spawnmanager": ("object", f"Class'\"{SPAWN_MANAGER}\"'", None),
    "exec": ("exec", None, None), "bool": ("bool", None, None), "int": ("int", None, None),
    "string": ("string", None, None), "actor": ("object", ACTOR, None),
    "self": ("object", "Class'\"/Script/CoreUObject.Object\"'", None),
    "state": ("object", "Class'\"/Script/FSD.FSDGameState\"'", None),
    "component": ("object", "Class'\"/Script/Engine.ActorComponent\"'", None),
    "inventory": ("object", f"Class'\"{INVENTORY}\"'", None),
    "float": ("float", None, None), "actors": ("object", ACTOR, "Array"),
    "class": ("class", ACTOR, None),
    "effect": ("class", "Class'\"/Script/FSD.StatusEffect\"'", None),
    "componentclass": ("class", "Class'\"/Script/Engine.ActorComponent\"'", None),
    "delegate": ("delegate", None, None),
    "weapon": ("object", f"Class'\"{WEAPON}\"'", None), "weapons": ("object", f"Class'\"{WEAPON}\"'", "Array"),
    "sentry": ("object", f"Class'\"{SENTRY}\"'", None), "sentries": ("object", f"Class'\"{SENTRY}\"'", "Array"),
}
OBJECTS = {"fsdpawn", "actor", "self", "state", "component", "inventory", "weapon", "sentry", "pawn", "health", "item", "cannon", "cryo", "drill", "settings", "savegame", "spinbox",
           "character", "playerchar", "playerhealth", "status"}
SETTING_FIELDS = (("DropChance", "float"), ("Cooldown", "float"), ("ForceEvent", "int"))
MATH = "/Script/Engine.KismetMathLibrary"
LIBRARY = "/Script/FSD.GameFunctionLibrary"
STATUS = "/Script/FSD.StatusEffectsComponent"
GAMEPLAY = "/Script/Engine.GameplayStatics"
SYSTEM = "/Script/Engine.KismetSystemLibrary"
NUKE_HEALTH_LIMIT = "3000.0"  # A first guess, to spare the toughest enemies. Tune it in game.
RAPID_MULTIPLIER = "2.0"
RAPID_SECONDS = "15.0"
COOLING_SECONDS = "0.1"
NO_HEAT_SCALE = "0.001"  # Scaled rather than zeroed, so dividing puts the original value back.
FAST_COOLING_SCALE = "1000.0"
FORTIFY_HEALS = "30"  # Once a second, so 30 s, matching STE_Dice_Fortify's Duration.
FORTIFY_HEAL_SHARE = "0.02"  # Of max health each second, so up to 60% over the whole effect.
PLAYER_HEALTH = "/Script/FSD.PlayerHealthComponent"
EVENT_X = 600  # Where each event's nodes start, to the right of the Branches that pick the event.
NODES = {}


def for_each(element_class):
    return ("MacroGraphReference=(MacroGraph=EdGraph'\"/Engine/EditorBlueprintResources/StandardMacros.StandardMacros:ForEachLoop\"',"
            "GraphBlueprint=Blueprint'\"/Engine/EditorBlueprintResources/StandardMacros.StandardMacros\"',"
            "GraphGuid=99DBFD5540A796041F72A5A9DA655026)\n"
            f"   ResolvedWildcardType=(PinCategory=\"object\",PinSubCategoryObject={element_class})")


class Node:
    def __init__(self, name, cls, x, y, body=""):
        self.name, self.cls, self.x, self.y, self.body = name, cls, x, y, body
        self.pins = {}
        NODES[name] = self

    def pin(self, name, kind, output=False, default=None, default_object=None):
        self.pins[name] = {"id": uuid.uuid4().hex.upper(), "kind": kind, "out": output, "default": default,
                           "object": default_object, "links": []}
        return self


def box(name, text, x, y, width, height, colour):
    """A comment box around one group of nodes."""
    r, g, b = colour
    return Node(name, "/Script/UnrealEd.EdGraphNode_Comment", x, y,
                f"NodeWidth={width}\n   NodeHeight={height}\n   CommentColor=(R={r},G={g},B={b},A=1.000000)\n   NodeComment=\"{text}\"")


def call(name, x, y, function, parent):
    ref = f"FunctionReference=(MemberParent=Class'\"{parent}\"',MemberName=\"{function}\")"
    return Node(name, "K2Node_CallFunction", x, y, ref)


def var_get(name, x, y, variable, kind):
    ref = f"VariableReference=(MemberName=\"{variable}\",bSelfContext=True)"
    return Node(name, "K2Node_VariableGet", x, y, ref).pin(variable, kind, True)


def var_set(name, x, y, variable, kind, default=None):
    ref = f"VariableReference=(MemberName=\"{variable}\",bSelfContext=True)"
    return Node(name, "K2Node_VariableSet", x, y, ref).pin("execute", "exec").pin("then", "exec", True).pin(variable, kind, False, default)


def branch(name, x, y):
    return Node(name, "K2Node_IfThenElse", x, y).pin("execute", "exec").pin("Condition", "bool") \
        .pin("then", "exec", True).pin("else", "exec", True)


def equals(name, x, y, value):
    return call(name, x, y, "EqualEqual_IntInt", MATH).pin("A", "int").pin("B", "int", False, str(value)).pin("ReturnValue", "bool", True)


def message(name, x, y, text):
    return call(name, x, y, "PostGameMessage", "/Script/FSD.FSDGameState").pin("execute", "exec").pin("then", "exec", True) \
        .pin("self", "state").pin("Msg", "string", False, text)


def all_actors(name, x, y, actor_class, kind):
    return Node(name, "K2Node_CallFunction", x, y, f"FunctionReference=(MemberParent=Class'\"{GAMEPLAY}\"',MemberName=\"GetAllActorsOfClass\")") \
        .pin("execute", "exec").pin("then", "exec", True).pin("ActorClass", "class", False, None, actor_class).pin("OutActors", kind, True)


def loop(name, x, y, element_class, list_kind, element_kind):
    return Node(name, "K2Node_MacroInstance", x, y, for_each(element_class)).pin("Exec", "exec").pin("Array", list_kind) \
        .pin("LoopBody", "exec", True).pin("Array Element", element_kind, True).pin("Completed", "exec", True)


def find_component(name, x, y, component_class):
    return Node(name, "K2Node_CallFunction", x, y, "FunctionReference=(MemberName=\"GetComponentByClass\",MemberParent=Class'\"/Script/Engine.Actor\"')") \
        .pin("execute", "exec").pin("then", "exec", True).pin("self", "actor") \
        .pin("ComponentClass", "componentclass", False, None, component_class).pin("ReturnValue", "component", True)


def cast_inventory(name, x, y):
    return Node(name, "K2Node_DynamicCast", x, y, f"TargetType=Class'\"{INVENTORY}\"'").pin("execute", "exec") \
        .pin("then", "exec", True).pin("CastFailed", "exec", True).pin("Object", "component") \
        .pin("AsInventory Component", "inventory", True).pin("bSuccess", "bool", True)


def resupply(name, x, y):
    return call(name, x, y, "Resupply", INVENTORY).pin("execute", "exec").pin("then", "exec", True).pin("self", "inventory") \
        .pin("percentage", "float", False, "1.0")


def link(src, src_pin, dst, dst_pin):
    a, b = NODES[src].pins[src_pin], NODES[dst].pins[dst_pin]
    if not a["out"] or b["out"]:
        raise ValueError(f"{src}.{src_pin} -> {dst}.{dst_pin} has the wrong direction")
    if a["kind"] != b["kind"] and not (a["kind"] in OBJECTS and b["kind"] in OBJECTS):
        raise ValueError(f"{src}.{src_pin} -> {dst}.{dst_pin} has mismatched types")
    a["links"].append((dst, b["id"]))
    b["links"].append((src, a["id"]))


def wire_up(wires):
    for wire in wires:
        left, right = wire.split(">")
        src, src_pin = left.split(".", 1)
        dst, dst_pin = right.split(".", 1)
        link(src, src_pin, dst, dst_pin)


def build_choice():
    """Pick the event, forced for testing or otherwise at random."""
    box("BoxChoose", "Choose Event", -1350, -80, 1050, 620, (0.3, 0.3, 0.3))
    var_get("GetForceA", -1300, 150, "ForceEvent", "int")
    call("ForceSet", -1100, 150, "GreaterEqual_IntInt", MATH).pin("A", "int").pin("B", "int", False, "0").pin("ReturnValue", "bool", True)
    branch("IsForced", -1100, 0)
    NODES["IsForced"].body = 'NodeComment="CONNECT RollDice HERE"\n   bCommentBubbleVisible=True\n   bCommentBubblePinned=True'
    var_get("GetForceB", -800, 150, "ForceEvent", "int")
    var_set("SetForced", -600, 0, "EventId", "int")
    call("RandomEvent", -900, 350, "RandomIntegerInRange", MATH).pin("Min", "int", False, "0").pin("Max", "int", False, "5") \
        .pin("ReturnValue", "int", True)
    var_set("SetRandom", -600, 250, "EventId", "int")
    wire_up([
        "GetForceA.ForceEvent>ForceSet.A", "ForceSet.ReturnValue>IsForced.Condition", "IsForced.then>SetForced.execute",
        "GetForceB.ForceEvent>SetForced.EventId", "IsForced.else>SetRandom.execute", "RandomEvent.ReturnValue>SetRandom.EventId",
    ])


def event_check(prefix, y, event_id):
    """One Branch per event. True runs the event, False moves on to the next check."""
    var_get(f"{prefix}Id", -200, y + 150, "EventId", "int")
    equals(f"{prefix}Check", 0, y + 150, event_id)
    branch(f"{prefix}Branch", 250, y)
    wire_up([f"{prefix}Id.EventId>{prefix}Check.A", f"{prefix}Check.ReturnValue>{prefix}Branch.Condition"])


def build_ammo(y):
    x = EVENT_X
    box("BoxAmmo", "Max Ammo", x - 50, y - 80, 3250, 1320, (0.1, 0.5, 0.15))
    event_check("Ammo", y, 0)

    # Fill every player's reserves.
    all_actors("AmmoPlayers", x, y, PLAYER, "actors")
    loop("AmmoLoop", x + 350, y, ACTOR, "actors", "actor")
    find_component("AmmoFind", x + 700, y, INVENTORY)
    cast_inventory("AmmoCast", x + 1050, y)
    resupply("AmmoRefill", x + 1400, y)

    # Fill every deployed turret on the host. Setting the value alone leaves the HUD stale,
    # so overfill by one and spend it through the game's own call.
    call("AmmoState", x + 100, y + 500, "GetFSDGameState", LIBRARY).pin("ReturnValue", "state", True)
    message("AmmoMsg", x + 350, y + 350, "Lucky Dice: FULL AMMO!")
    all_actors("Sentries", x + 700, y + 350, SENTRY, "sentries")
    loop("SentryLoop", x + 1050, y + 350, f"Class'\"{SENTRY}\"'", "sentries", "sentry")
    call("SentryMax", x + 1050, y + 650, "GetMaxAmmoCount", SENTRY).pin("self", "sentry").pin("ReturnValue", "int", True)
    call("SentryPlusOne", x + 1350, y + 650, "Add_IntInt", MATH).pin("A", "int").pin("B", "int", False, "1").pin("ReturnValue", "int", True)
    Node("SentryFill", "K2Node_VariableSet", x + 1600, y + 350, f"VariableReference=(MemberParent=Class'\"{SENTRY}\"',MemberName=\"AmmoCount\")") \
        .pin("execute", "exec").pin("then", "exec", True).pin("AmmoCount", "int").pin("self", "sentry")
    call("SentryUpdate", x + 1950, y + 350, "UseAmmo", SENTRY).pin("execute", "exec").pin("then", "exec", True).pin("self", "sentry") \
        .pin("amount", "int", False, "1")

    # Reloading uses reserve ammo, so refill the reserves again afterwards.
    Node("CallReload", "K2Node_CallFunction", x, y + 900, "FunctionReference=(MemberName=\"DiceReloadAll\",bSelfContext=True)") \
        .pin("execute", "exec").pin("then", "exec", True)
    call("WaitForReload", x + 350, y + 900, "Delay", SYSTEM).pin("execute", "exec").pin("then", "exec", True).pin("Duration", "float", False, "0.5")
    loop("TopUpLoop", x + 700, y + 900, ACTOR, "actors", "actor")
    find_component("TopUpFind", x + 1050, y + 900, INVENTORY)
    cast_inventory("TopUpCast", x + 1400, y + 900)
    resupply("TopUp", x + 1750, y + 900)

    wire_up([
        "AmmoBranch.then>AmmoPlayers.execute", "AmmoPlayers.then>AmmoLoop.Exec", "AmmoPlayers.OutActors>AmmoLoop.Array",
        "AmmoLoop.LoopBody>AmmoFind.execute", "AmmoLoop.Array Element>AmmoFind.self", "AmmoFind.then>AmmoCast.execute",
        "AmmoFind.ReturnValue>AmmoCast.Object", "AmmoCast.then>AmmoRefill.execute", "AmmoCast.AsInventory Component>AmmoRefill.self",
        "AmmoLoop.Completed>AmmoMsg.execute", "AmmoState.ReturnValue>AmmoMsg.self", "AmmoMsg.then>Sentries.execute",
        "Sentries.then>SentryLoop.Exec", "Sentries.OutActors>SentryLoop.Array", "SentryLoop.LoopBody>SentryFill.execute",
        "SentryLoop.Array Element>SentryMax.self", "SentryMax.ReturnValue>SentryPlusOne.A", "SentryPlusOne.ReturnValue>SentryFill.AmmoCount",
        "SentryLoop.Array Element>SentryFill.self", "SentryFill.then>SentryUpdate.execute", "SentryLoop.Array Element>SentryUpdate.self",
        "SentryLoop.Completed>CallReload.execute", "CallReload.then>WaitForReload.execute", "WaitForReload.then>TopUpLoop.Exec",
        "AmmoPlayers.OutActors>TopUpLoop.Array", "TopUpLoop.LoopBody>TopUpFind.execute", "TopUpLoop.Array Element>TopUpFind.self",
        "TopUpFind.then>TopUpCast.execute", "TopUpFind.ReturnValue>TopUpCast.Object", "TopUpCast.then>TopUp.execute",
        "TopUpCast.AsInventory Component>TopUp.self",
    ])


def build_speed(y):
    x = EVENT_X
    box("BoxSpeed", "Speed Boost", x - 50, y - 80, 1250, 640, (0.1, 0.3, 0.6))
    event_check("Speed", y, 1)
    all_actors("SpeedPlayers", x, y, PLAYER, "actors")
    loop("SpeedLoop", x + 350, y, ACTOR, "actors", "actor")
    Node("SpeedSelf", "K2Node_Self", x + 500, y + 250).pin("self", "self", True)
    call("GiveSpeed", x + 750, y, "TryPushActiveStatusEffect", STATUS).pin("execute", "exec").pin("then", "exec", True) \
        .pin("StatusEffect", "effect", False, None, "/Game/LuckyDice/STE_Dice_Speed.STE_Dice_Speed_C") \
        .pin("Target", "actor").pin("Owner", "actor")
    call("SpeedState", x + 500, y + 400, "GetFSDGameState", LIBRARY).pin("ReturnValue", "state", True)
    message("SpeedMsg", x + 750, y + 300, "Lucky Dice: SPEED BOOST!")
    wire_up([
        "SpeedBranch.then>SpeedPlayers.execute", "SpeedPlayers.then>SpeedLoop.Exec", "SpeedPlayers.OutActors>SpeedLoop.Array",
        "SpeedLoop.LoopBody>GiveSpeed.execute", "SpeedLoop.Array Element>GiveSpeed.Target", "SpeedSelf.self>GiveSpeed.Owner",
        "SpeedLoop.Completed>SpeedMsg.execute", "SpeedState.ReturnValue>SpeedMsg.self",
    ])


def nuke_pass(prefix, y, swarmers):
    """Save one enemy list, then kill each enemy in it that's under the health limit."""
    x = EVENT_X
    call(f"{prefix}Find", x + 300, y + 200, "FindEnemiesByClass", SPAWN_MANAGER).pin("self", "spawnmanager") \
        .pin("PawnClass", "pawnclass", False, None, PAWN).pin("isSwarmerEnemy", "bool", False, swarmers).pin("ReturnValue", "pawns", True)
    var_set(f"{prefix}Save", x + 650, y, "NukeTargets", "pawns")
    var_get(f"{prefix}List", x + 650, y + 200, "NukeTargets", "pawns")
    loop(f"{prefix}Loop", x + 950, y, f"Class'\"{PAWN}\"'", "pawns", "pawn")
    find_component(f"{prefix}Component", x + 1300, y, HEALTH)
    Node(f"{prefix}Cast", "K2Node_DynamicCast", x + 1650, y, f"TargetType=Class'\"{HEALTH}\"'").pin("execute", "exec") \
        .pin("then", "exec", True).pin("CastFailed", "exec", True).pin("Object", "component") \
        .pin("AsHealth Component Base", "health", True).pin("bSuccess", "bool", True)
    call(f"{prefix}Health", x + 1650, y + 250, "GetHealth", HEALTH).pin("self", "health").pin("ReturnValue", "float", True)
    call(f"{prefix}UnderLimit", x + 1950, y + 250, "LessEqual_FloatFloat", MATH).pin("A", "float").pin("B", "float", False, str(NUKE_HEALTH_LIMIT)) \
        .pin("ReturnValue", "bool", True)
    branch(f"{prefix}Check", x + 2200, y)
    call(f"{prefix}Kill", x + 2500, y, "Kill", HEALTH).pin("execute", "exec").pin("then", "exec", True).pin("self", "health").pin("DamageCauser", "actor")
    p = prefix
    wire_up([
        f"NukeManager.EnemySpawnManager>{p}Find.self", f"{p}Find.ReturnValue>{p}Save.NukeTargets", f"{p}Save.then>{p}Loop.Exec",
        f"{p}List.NukeTargets>{p}Loop.Array", f"{p}Loop.LoopBody>{p}Component.execute", f"{p}Loop.Array Element>{p}Component.self",
        f"{p}Component.then>{p}Cast.execute", f"{p}Component.ReturnValue>{p}Cast.Object", f"{p}Cast.then>{p}Check.execute",
        f"{p}Cast.AsHealth Component Base>{p}Health.self", f"{p}Health.ReturnValue>{p}UnderLimit.A", f"{p}UnderLimit.ReturnValue>{p}Check.Condition",
        f"{p}Check.then>{p}Kill.execute", f"{p}Cast.AsHealth Component Base>{p}Kill.self", f"NukeSelf.self>{p}Kill.DamageCauser",
    ])


def build_nuke(y):
    # The list is saved first: For Each re-reads a pure call every pass, and kills shrink the live list.
    x = EVENT_X
    box("BoxNuke", "Nuke", x - 50, y - 80, 3050, 1650, (0.7, 0.15, 0.1))
    event_check("Nuke", y, 2)
    call("NukeGameMode", x, y + 550, "GetFSDGameMode", LIBRARY).pin("ReturnValue", "gamemode", True)
    Node("NukeManager", "K2Node_VariableGet", x, y + 350, f"VariableReference=(MemberParent=Class'\"{GAME_MODE}\"',MemberName=\"EnemySpawnManager\")") \
        .pin("EnemySpawnManager", "spawnmanager", True).pin("self", "gamemode")
    Node("NukeSelf", "K2Node_Self", x + 2200, y + 500).pin("self", "self", True)
    nuke_pass("Regular", y, "false")
    nuke_pass("Swarm", y + 750, "true")
    call("NukeState", x + 1300, y + 1400, "GetFSDGameState", LIBRARY).pin("ReturnValue", "state", True)
    message("NukeMsg", x + 1650, y + 1300, "Lucky Dice: NUKE!")
    wire_up([
        "NukeGameMode.ReturnValue>NukeManager.self", "NukeBranch.then>RegularSave.execute",
        "RegularLoop.Completed>SwarmSave.execute", "SwarmLoop.Completed>NukeMsg.execute", "NukeState.ReturnValue>NukeMsg.self",
    ])


def build_rapid(y):
    x = EVENT_X
    box("BoxRapid", "Rapid Fire", x - 50, y - 80, 900, 420, (0.6, 0.45, 0.05))
    event_check("Rapid", y, 3)
    Node("CallRapid", "K2Node_CallFunction", x, y, "FunctionReference=(MemberName=\"DiceRapidFire\",bSelfContext=True)") \
        .pin("execute", "exec").pin("then", "exec", True)
    call("RapidState", x + 100, y + 170, "GetFSDGameState", LIBRARY).pin("ReturnValue", "state", True)
    message("RapidMsg", x + 350, y, "Lucky Dice: RAPID FIRE!")
    wire_up(["RapidBranch.then>CallRapid.execute", "CallRapid.then>RapidMsg.execute", "RapidState.ReturnValue>RapidMsg.self"])


def build_fortify_heal(x, y):
    """Heal every living player by FORTIFY_HEAL_SHARE of their max health once a second, FORTIFY_HEALS times.
    HealingStatusEffectItem didn't heal at all in testing, so this calls Heal directly. A second roll resets the count."""
    var_set("HealCount", x, y, "FortifyHealsLeft", "int", FORTIFY_HEALS)
    call("HealWait", x + 300, y, "Delay", SYSTEM).pin("execute", "exec").pin("then", "exec", True).pin("Duration", "float", False, "1.0")
    all_actors("HealPlayers", x + 600, y, PLAYER, "actors")
    loop("HealLoop", x + 950, y, ACTOR, "actors", "actor")
    find_component("HealFind", x + 1300, y, PLAYER_HEALTH)
    Node("HealCast", "K2Node_DynamicCast", x + 1650, y, f"TargetType=Class'\"{PLAYER_HEALTH}\"'").pin("execute", "exec") \
        .pin("then", "exec", True).pin("CastFailed", "exec", True).pin("Object", "component") \
        .pin("AsPlayer Health Component", "playerhealth", True).pin("bSuccess", "bool", True)
    call("HealAlive", x + 1650, y + 250, "IsAlive", HEALTH).pin("self", "health").pin("ReturnValue", "bool", True)
    branch("HealIfAlive", x + 2000, y)
    # Read the MaxHealth property instead of calling GetMaxHealth, which crashes the game from Blueprint.
    Node("HealMax", "K2Node_VariableGet", x + 2000, y + 250, f"VariableReference=(MemberParent=Class'\"{PLAYER_HEALTH}\"',MemberName=\"MaxHealth\")") \
        .pin("MaxHealth", "float", True).pin("self", "playerhealth")
    call("HealShare", x + 2250, y + 250, "Multiply_FloatFloat", MATH).pin("A", "float").pin("B", "float", False, FORTIFY_HEAL_SHARE) \
        .pin("ReturnValue", "float", True)
    call("HealNow", x + 2300, y, "Heal", HEALTH).pin("execute", "exec").pin("then", "exec", True).pin("self", "health") \
        .pin("amount", "float").pin("ReturnValue", "float", True)
    var_get("HealLeftA", x + 950, y + 450, "FortifyHealsLeft", "int")
    call("HealMinusOne", x + 1150, y + 450, "Subtract_IntInt", MATH).pin("A", "int").pin("B", "int", False, "1").pin("ReturnValue", "int", True)
    var_set("HealCountDown", x + 1300, y + 400, "FortifyHealsLeft", "int")
    var_get("HealLeftB", x + 1550, y + 550, "FortifyHealsLeft", "int")
    call("HealMore", x + 1750, y + 550, "Greater_IntInt", MATH).pin("A", "int").pin("B", "int", False, "0").pin("ReturnValue", "bool", True)
    branch("HealAgain", x + 1650, y + 400)
    wire_up([
        "HealCount.then>HealWait.execute", "HealWait.then>HealPlayers.execute", "HealPlayers.then>HealLoop.Exec",
        "HealPlayers.OutActors>HealLoop.Array", "HealLoop.LoopBody>HealFind.execute", "HealLoop.Array Element>HealFind.self",
        "HealFind.then>HealCast.execute", "HealFind.ReturnValue>HealCast.Object", "HealCast.then>HealIfAlive.execute",
        "HealCast.AsPlayer Health Component>HealAlive.self", "HealAlive.ReturnValue>HealIfAlive.Condition",
        "HealIfAlive.then>HealNow.execute", "HealCast.AsPlayer Health Component>HealNow.self",
        "HealCast.AsPlayer Health Component>HealMax.self", "HealMax.MaxHealth>HealShare.A", "HealShare.ReturnValue>HealNow.amount",
        "HealLoop.Completed>HealCountDown.execute", "HealLeftA.FortifyHealsLeft>HealMinusOne.A", "HealMinusOne.ReturnValue>HealCountDown.FortifyHealsLeft",
        "HealCountDown.then>HealAgain.execute", "HealLeftB.FortifyHealsLeft>HealMore.A", "HealMore.ReturnValue>HealAgain.Condition",
        "HealAgain.then>HealWait.execute",
    ])


def build_fortify(y):
    """Less damage and faster shields from STE_Dice_Fortify, plus a heal each second from build_fortify_heal."""
    x = EVENT_X
    box("BoxFortify", "Fortify", x - 50, y - 80, 4000, 1100, (0.1, 0.5, 0.5))
    event_check("Fortify", y, 4)
    all_actors("FortifyPlayers", x, y, PLAYER, "actors")
    loop("FortifyLoop", x + 350, y, ACTOR, "actors", "actor")
    Node("FortifySelf", "K2Node_Self", x + 500, y + 250).pin("self", "self", True)
    call("GiveFortify", x + 750, y, "TryPushActiveStatusEffect", STATUS).pin("execute", "exec").pin("then", "exec", True) \
        .pin("StatusEffect", "effect", False, None, "/Game/LuckyDice/STE_Dice_Fortify.STE_Dice_Fortify_C") \
        .pin("Target", "actor").pin("Owner", "actor")
    call("FortifyState", x + 500, y + 400, "GetFSDGameState", LIBRARY).pin("ReturnValue", "state", True)
    message("FortifyMsg", x + 750, y + 300, "Lucky Dice: FORTIFY!")
    build_fortify_heal(x + 1100, y + 300)
    wire_up([
        "FortifyBranch.then>FortifyPlayers.execute", "FortifyPlayers.then>FortifyLoop.Exec", "FortifyPlayers.OutActors>FortifyLoop.Array",
        "FortifyLoop.LoopBody>GiveFortify.execute", "FortifyLoop.Array Element>GiveFortify.Target", "FortifySelf.self>GiveFortify.Owner",
        "FortifyLoop.Completed>FortifyMsg.execute", "FortifyState.ReturnValue>FortifyMsg.self", "FortifyMsg.then>HealCount.execute",
    ])


FSD_PAWN = "/Script/FSD.FSDPawn"
FREEZE_TICKS = "10"  # Once a second, so enemies stay frozen for about 10 s, including new spawns.


def freeze_pass(prefix, x, y, swarmers, thaw=False, manager="FreezeManager"):
    """Save one enemy list, then freeze each enemy in it, or unfreeze it with thaw."""
    call(f"{prefix}Find", x, y + 200, "FindEnemiesByClass", SPAWN_MANAGER).pin("self", "spawnmanager")         .pin("PawnClass", "pawnclass", False, None, PAWN).pin("isSwarmerEnemy", "bool", False, swarmers).pin("ReturnValue", "pawns", True)
    var_set(f"{prefix}Save", x + 350, y, "NukeTargets", "pawns")
    var_get(f"{prefix}List", x + 350, y + 200, "NukeTargets", "pawns")
    loop(f"{prefix}Loop", x + 650, y, f"Class'\"{PAWN}\"'", "pawns", "pawn")
    Node(f"{prefix}Cast", "K2Node_DynamicCast", x + 1000, y, f"TargetType=Class'\"{FSD_PAWN}\"'").pin("execute", "exec")         .pin("then", "exec", True).pin("CastFailed", "exec", True).pin("Object", "pawn")         .pin("AsFSDPawn", "fsdpawn", True).pin("bSuccess", "bool", True)
    call(f"{prefix}Freeze", x + 1350, y, "UnFreeze" if thaw else "Freeze", FSD_PAWN).pin("execute", "exec").pin("then", "exec", True)         .pin("self", "fsdpawn")
    if not thaw:
        NODES[f"{prefix}Freeze"].pin("Source", "actor")
    p = prefix
    wire_up([
        f"{manager}.EnemySpawnManager>{p}Find.self", f"{p}Find.ReturnValue>{p}Save.NukeTargets", f"{p}Save.then>{p}Loop.Exec",
        f"{p}List.NukeTargets>{p}Loop.Array", f"{p}Loop.LoopBody>{p}Cast.execute", f"{p}Loop.Array Element>{p}Cast.Object",
        f"{p}Cast.then>{p}Freeze.execute", f"{p}Cast.AsFSDPawn>{p}Freeze.self",
    ])
    if not thaw:
        wire_up([f"FreezeSelf.self>{p}Freeze.Source"])


def build_unfreeze(x, y):
    """Unfreeze every enemy. Freeze holds enemies frozen for good, so the effect has to end it."""
    call("ThawGameMode", x, y + 550, "GetFSDGameMode", LIBRARY).pin("ReturnValue", "gamemode", True)
    Node("ThawManager", "K2Node_VariableGet", x, y + 400, f"VariableReference=(MemberParent=Class'\"{GAME_MODE}\"',MemberName=\"EnemySpawnManager\")")         .pin("EnemySpawnManager", "spawnmanager", True).pin("self", "gamemode")
    freeze_pass("ThawRegular", x + 300, y, "false", True, "ThawManager")
    freeze_pass("ThawSwarm", x + 300, y + 600, "true", True, "ThawManager")
    wire_up(["ThawGameMode.ReturnValue>ThawManager.self", "ThawRegularLoop.Completed>ThawSwarmSave.execute"])


def build_freeze(y):
    """Freeze every enemy once a second, FREEZE_TICKS times. Reuses NukeTargets as a scratch list.
    Needs the Integer variable FreezeTicksLeft. A second roll resets the count."""
    x = EVENT_X
    box("BoxFreeze", "Freeze All", x - 50, y - 80, 3300, 2900, (0.15, 0.4, 0.8))
    event_check("Freeze", y, 5)
    call("FreezeState", x, y + 170, "GetFSDGameState", LIBRARY).pin("ReturnValue", "state", True)
    message("FreezeMsg", x + 250, y, "Lucky Dice: FREEZE ALL!")
    var_set("FreezeCount", x + 600, y, "FreezeTicksLeft", "int", FREEZE_TICKS)
    call("FreezeGameMode", x + 600, y + 550, "GetFSDGameMode", LIBRARY).pin("ReturnValue", "gamemode", True)
    Node("FreezeManager", "K2Node_VariableGet", x + 600, y + 400, f"VariableReference=(MemberParent=Class'\"{GAME_MODE}\"',MemberName=\"EnemySpawnManager\")")         .pin("EnemySpawnManager", "spawnmanager", True).pin("self", "gamemode")
    Node("FreezeSelf", "K2Node_Self", x + 2100, y + 300).pin("self", "self", True)
    freeze_pass("FreezeRegular", x + 900, y, "false")
    freeze_pass("FreezeSwarm", x + 900, y + 600, "true")
    var_get("FreezeLeftA", x + 900, y + 1250, "FreezeTicksLeft", "int")
    call("FreezeMinusOne", x + 1100, y + 1250, "Subtract_IntInt", MATH).pin("A", "int").pin("B", "int", False, "1").pin("ReturnValue", "int", True)
    var_set("FreezeCountDown", x + 1350, y + 1150, "FreezeTicksLeft", "int")
    var_get("FreezeLeftB", x + 1600, y + 1300, "FreezeTicksLeft", "int")
    call("FreezeMore", x + 1800, y + 1300, "Greater_IntInt", MATH).pin("A", "int").pin("B", "int", False, "0").pin("ReturnValue", "bool", True)
    branch("FreezeAgain", x + 1700, y + 1150)
    call("FreezeWait", x + 2050, y + 1150, "Delay", SYSTEM).pin("execute", "exec").pin("then", "exec", True).pin("Duration", "float", False, "1.0")
    wire_up([
        "FreezeBranch.then>FreezeMsg.execute", "FreezeState.ReturnValue>FreezeMsg.self", "FreezeMsg.then>FreezeCount.execute",
        "FreezeGameMode.ReturnValue>FreezeManager.self", "FreezeCount.then>FreezeRegularSave.execute",
        "FreezeRegularLoop.Completed>FreezeSwarmSave.execute", "FreezeSwarmLoop.Completed>FreezeCountDown.execute",
        "FreezeLeftA.FreezeTicksLeft>FreezeMinusOne.A", "FreezeMinusOne.ReturnValue>FreezeCountDown.FreezeTicksLeft",
        "FreezeCountDown.then>FreezeAgain.execute", "FreezeLeftB.FreezeTicksLeft>FreezeMore.A", "FreezeMore.ReturnValue>FreezeAgain.Condition",
        "FreezeAgain.then>FreezeWait.execute", "FreezeWait.then>FreezeRegularSave.execute",
    ])
    build_unfreeze(x, y + 1700)
    wire_up(["FreezeAgain.else>ThawRegularSave.execute"])


def settings_member(cls, name, x, y, field):
    return Node(name, cls, x, y, f"VariableReference=(MemberParent=BlueprintGeneratedClass'\"{SETTINGS}\"',MemberName=\"{field}\")")


def load_slot(prefix, x, y):
    """Does the save exist? If so, load it and cast it to our settings class."""
    # Not a pure node in 4.27, so it has to run in the chain or its result is never read.
    call(f"{prefix}Exists", x - 50, y, "DoesSaveGameExist", GAMEPLAY).pin("execute", "exec").pin("then", "exec", True) \
        .pin("SlotName", "string", False, SETTINGS_SLOT).pin("UserIndex", "int", False, "0").pin("ReturnValue", "bool", True)
    branch(f"{prefix}Branch", x + 300, y)
    call(f"{prefix}Load", x + 600, y, "LoadGameFromSlot", GAMEPLAY).pin("execute", "exec").pin("then", "exec", True) \
        .pin("SlotName", "string", False, SETTINGS_SLOT).pin("UserIndex", "int", False, "0").pin("ReturnValue", "savegame", True)
    Node(f"{prefix}Cast", "K2Node_DynamicCast", x + 950, y, f"TargetType=BlueprintGeneratedClass'\"{SETTINGS}\"'").pin("execute", "exec") \
        .pin("then", "exec", True).pin("CastFailed", "exec", True).pin("Object", "savegame") \
        .pin("AsLucky Dice Settings", "settings", True).pin("bSuccess", "bool", True)
    wire_up([
        f"{prefix}Exists.then>{prefix}Branch.execute", f"{prefix}Exists.ReturnValue>{prefix}Branch.Condition", f"{prefix}Branch.then>{prefix}Load.execute",
        f"{prefix}Load.then>{prefix}Cast.execute", f"{prefix}Load.ReturnValue>{prefix}Cast.Object",
    ])


def build_settings_loader():
    """For BP_DiceManager's BeginPlay: copy any saved settings over the defaults, then carry on as before."""
    Node("LoadSequence", "K2Node_ExecutionSequence", 0, 0, 'NodeComment="CONNECT Event BeginPlay HERE"\n   bCommentBubbleVisible=True\n   bCommentBubblePinned=True') \
        .pin("execute", "exec").pin("then_0", "exec", True).pin("then_1", "exec", True)
    load_slot("Saved", 300, 0)
    previous = "SavedCast.then"
    for i, (field, kind) in enumerate(SETTING_FIELDS):
        settings_member("K2Node_VariableGet", f"Saved{field}", 1300 + i * 350, 220, field).pin(field, kind, True).pin("self", "settings")
        var_set(f"Use{field}", 1300 + i * 350, 0, field, kind)
        wire_up([f"{previous}>Use{field}.execute", f"SavedCast.AsLucky Dice Settings>Saved{field}.self", f"Saved{field}.{field}>Use{field}.{field}"])
        previous = f"Use{field}.then"
    # Then 1 is left free, for the nodes BeginPlay used to run.
    wire_up(["LoadSequence.then_0>SavedExists.execute"])


def build_settings_widget():
    """Event graph for WBP_LuckyDiceSettings: fill the boxes from the save, and save whenever a box changes."""
    Node("PageConstruct", "K2Node_Event", 0, 0, "EventReference=(MemberParent=Class'\"/Script/UMG.UserWidget\"',MemberName=\"Construct\")\n   bOverrideFunction=True") \
        .pin("OutputDelegate", "delegate", True).pin("then", "exec", True)
    load_slot("Page", 300, 0)
    call("PageNew", 950, 400, "CreateSaveGameObject", GAMEPLAY).pin("execute", "exec").pin("then", "exec", True) \
        .pin("SaveGameClass", "savegameclass", False, None, SETTINGS).pin("ReturnValue", "savegame", True)
    Node("PageNewCast", "K2Node_DynamicCast", 1300, 400, f"TargetType=BlueprintGeneratedClass'\"{SETTINGS}\"'").pin("execute", "exec") \
        .pin("then", "exec", True).pin("CastFailed", "exec", True).pin("Object", "savegame") \
        .pin("AsLucky Dice Settings", "settings", True).pin("bSuccess", "bool", True)
    var_set("PageKeepLoaded", 1650, 0, "Settings", "settings")
    var_set("PageKeepNew", 1650, 400, "Settings", "settings")
    wire_up([
        "PageConstruct.then>PageExists.execute", "PageBranch.else>PageNew.execute", "PageNew.then>PageNewCast.execute",
        "PageNew.ReturnValue>PageNewCast.Object", "PageCast.then>PageKeepLoaded.execute", "PageCast.AsLucky Dice Settings>PageKeepLoaded.Settings",
        "PageNewCast.then>PageKeepNew.execute", "PageNewCast.AsLucky Dice Settings>PageKeepNew.Settings",
    ])
    previous = ["PageKeepLoaded.then", "PageKeepNew.then"]
    for i, (field, kind) in enumerate(SETTING_FIELDS):
        x, box_name = 2000 + i * 400, f"{field}Box"
        var_get(f"Fill{field}Box", x, 250, box_name, "spinbox")
        var_get(f"Fill{field}Settings", x - 150, 380, "Settings", "settings")
        settings_member("K2Node_VariableGet", f"Fill{field}Value", x, 380, field).pin(field, kind, True).pin("self", "settings")
        call(f"Fill{field}", x, 0, "SetValue", SPINBOX).pin("execute", "exec").pin("then", "exec", True).pin("self", "spinbox").pin("NewValue", "float")
        wires = [f"{p}>Fill{field}.execute" for p in previous] + [
            f"Fill{field}Box.{box_name}>Fill{field}.self", f"Fill{field}Settings.Settings>Fill{field}Value.self"]
        if kind == "int":
            call(f"Fill{field}Float", x + 200, 380, "Conv_IntToFloat", MATH).pin("InInt", "int").pin("ReturnValue", "float", True)
            wires += [f"Fill{field}Value.{field}>Fill{field}Float.InInt", f"Fill{field}Float.ReturnValue>Fill{field}.NewValue"]
        else:
            wires.append(f"Fill{field}Value.{field}>Fill{field}.NewValue")
        wire_up(wires)
        previous = [f"Fill{field}.then"]

        # Save whenever this box's value is committed.
        y = 800 + i * 400
        event = f"BndEvt__{box_name}_K2Node_ComponentBoundEvent_{i}_OnSpinBoxValueCommittedEvent__DelegateSignature"
        Node(f"Changed{field}", "K2Node_ComponentBoundEvent", 0, y,
             f"DelegatePropertyName=\"OnValueCommitted\"\n   DelegateOwnerClass=Class'\"{SPINBOX}\"'\n   ComponentPropertyName=\"{box_name}\"\n"
             f"   EventReference=(MemberParent=Package'\"/Script/UMG\"',MemberName=\"OnSpinBoxValueCommittedEvent__DelegateSignature\")\n"
             f"   CustomFunctionName=\"{event}\"") \
            .pin("OutputDelegate", "delegate", True).pin("then", "exec", True).pin("InValue", "float", True).pin("CommitMethod", "textcommit", True)
        var_get(f"Changed{field}Settings", 300, y + 200, "Settings", "settings")
        settings_member("K2Node_VariableSet", f"Store{field}", 350, y, field).pin("execute", "exec").pin("then", "exec", True) \
            .pin(field, kind).pin("self", "settings")
        call(f"Save{field}", 700, y, "SaveGameToSlot", GAMEPLAY).pin("execute", "exec").pin("then", "exec", True).pin("SaveGameObject", "savegame") \
            .pin("SlotName", "string", False, SETTINGS_SLOT).pin("UserIndex", "int", False, "0").pin("ReturnValue", "bool", True)
        wires = [f"Changed{field}.then>Store{field}.execute", f"Changed{field}Settings.Settings>Store{field}.self",
                 f"Store{field}.then>Save{field}.execute", f"Changed{field}Settings.Settings>Save{field}.SaveGameObject"]
        if kind == "int":
            call(f"Changed{field}Round", 200, y + 300, "Round", MATH).pin("A", "float").pin("ReturnValue", "int", True)
            wires += [f"Changed{field}.InValue>Changed{field}Round.A", f"Changed{field}Round.ReturnValue>Store{field}.{field}"]
        else:
            wires.append(f"Changed{field}.InValue>Store{field}.{field}")
        wire_up(wires)


def build_debug_readout():
    """Every 0.25 s, post any change in the host's health plus shield to chat, and whether Fortify and Regen are active."""
    branch("DbgStart", 0, 0)
    NODES["DbgStart"].body = 'NodeComment="CONNECT Sequence Then 2 HERE"\n   bCommentBubbleVisible=True\n   bCommentBubblePinned=True'
    var_get("DbgOn", -250, 150, "DebugReadout", "bool")
    call("DbgWait", 300, 0, "Delay", SYSTEM).pin("execute", "exec").pin("then", "exec", True).pin("Duration", "float", False, "0.25")
    call("DbgPlayer", 300, 250, "GetPlayerCharacter", GAMEPLAY).pin("PlayerIndex", "int", False, "0").pin("ReturnValue", "character", True)
    Node("DbgCast", "K2Node_DynamicCast", 650, 0, f"TargetType=Class'\"{PLAYER}\"'").pin("execute", "exec") \
        .pin("then", "exec", True).pin("CastFailed", "exec", True).pin("Object", "character") \
        .pin("AsPlayer Character", "playerchar", True).pin("bSuccess", "bool", True)
    Node("DbgHealthComp", "K2Node_VariableGet", 650, 300, f"VariableReference=(MemberParent=Class'\"{PLAYER}\"',MemberName=\"HealthComponent\")") \
        .pin("HealthComponent", "playerhealth", True).pin("self", "playerchar")
    Node("DbgStatusComp", "K2Node_VariableGet", 650, 450, f"VariableReference=(MemberParent=Class'\"{PLAYER}\"',MemberName=\"StatusEffectsComponent\")") \
        .pin("StatusEffectsComponent", "status", True).pin("self", "playerchar")
    call("DbgHealth", 950, 250, "GetHealth", HEALTH).pin("self", "health").pin("ReturnValue", "float", True)
    call("DbgShield", 950, 350, "GetArmor", "/Script/FSD.HealthComponent").pin("self", "health").pin("ReturnValue", "float", True)
    call("DbgTotal", 1200, 300, "Add_FloatFloat", MATH).pin("A", "float").pin("B", "float").pin("ReturnValue", "float", True)
    var_get("DbgLast", 1200, 450, "DebugLastHealth", "float")
    call("DbgChange", 1450, 300, "Subtract_FloatFloat", MATH).pin("A", "float").pin("B", "float").pin("ReturnValue", "float", True)
    call("DbgSize", 1650, 400, "Abs", MATH).pin("A", "float").pin("ReturnValue", "float", True)
    call("DbgBig", 1850, 400, "Greater_FloatFloat", MATH).pin("A", "float").pin("B", "float", False, "0.5").pin("ReturnValue", "bool", True)
    branch("DbgChanged", 1950, 0)
    for name, y, effect in (("DbgFortify", 550, "STE_Dice_Fortify"), ("DbgRegen", 650, "STE_Dice_Regen")):
        call(name, 950, y, "HasActiveEffect", STATUS).pin("self", "status") \
            .pin("StatusEffect", "effect", False, None, f"/Game/LuckyDice/{effect}.{effect}_C").pin("ReturnValue", "bool", True)

    # Build the chat line one piece at a time.
    parts = [("Dice debug: change ", "DbgChange.ReturnValue", "float"), (" | HP ", "DbgHealth.ReturnValue", "float"),
             (" | shield ", "DbgShield.ReturnValue", "float"), (" | Fortify ", "DbgFortify.ReturnValue", "bool"),
             (" | Regen ", "DbgRegen.ReturnValue", "bool")]
    text, wires = None, []
    for i, (label, source, kind) in enumerate(parts):
        x = 1200 + i * 450
        convert = "Conv_FloatToString" if kind == "float" else "Conv_BoolToString"
        source_pin = "InFloat" if kind == "float" else "InBool"
        call(f"DbgText{i}", x, 800, convert, STRING).pin(source_pin, kind).pin("ReturnValue", "string", True)
        call(f"DbgLabel{i}", x + 200, 900, "Concat_StrStr", STRING).pin("A", "string", False, label if text is None else None) \
            .pin("B", "string", False, None if text is None else label).pin("ReturnValue", "string", True)
        call(f"DbgJoin{i}", x + 200, 1000, "Concat_StrStr", STRING).pin("A", "string").pin("B", "string").pin("ReturnValue", "string", True)
        wires += [f"{source}>DbgText{i}.{source_pin}", f"DbgLabel{i}.ReturnValue>DbgJoin{i}.A", f"DbgText{i}.ReturnValue>DbgJoin{i}.B"]
        if text is not None:
            wires.append(f"{text}>DbgLabel{i}.A")
        text = f"DbgJoin{i}.ReturnValue"
    call("DbgState", 2200, 250, "GetFSDGameState", LIBRARY).pin("ReturnValue", "state", True)
    message("DbgMsg", 2300, 0, "")
    var_set("DbgRemember", 2650, 0, "DebugLastHealth", "float")
    wire_up(wires + [
        "DbgOn.DebugReadout>DbgStart.Condition", "DbgStart.then>DbgWait.execute", "DbgWait.then>DbgCast.execute",
        "DbgPlayer.ReturnValue>DbgCast.Object", "DbgCast.CastFailed>DbgWait.execute",
        "DbgCast.AsPlayer Character>DbgHealthComp.self", "DbgCast.AsPlayer Character>DbgStatusComp.self",
        "DbgHealthComp.HealthComponent>DbgHealth.self", "DbgHealthComp.HealthComponent>DbgShield.self",
        "DbgHealth.ReturnValue>DbgTotal.A", "DbgShield.ReturnValue>DbgTotal.B", "DbgTotal.ReturnValue>DbgChange.A",
        "DbgLast.DebugLastHealth>DbgChange.B", "DbgChange.ReturnValue>DbgSize.A", "DbgSize.ReturnValue>DbgBig.A",
        "DbgCast.then>DbgChanged.execute", "DbgBig.ReturnValue>DbgChanged.Condition",
        "DbgStatusComp.StatusEffectsComponent>DbgFortify.self", "DbgStatusComp.StatusEffectsComponent>DbgRegen.self",
        "DbgChanged.then>DbgMsg.execute", "DbgState.ReturnValue>DbgMsg.self", f"{text}>DbgMsg.Msg",
        "DbgMsg.then>DbgRemember.execute", "DbgChanged.else>DbgRemember.execute", "DbgTotal.ReturnValue>DbgRemember.DebugLastHealth",
        "DbgRemember.then>DbgWait.execute",
    ])


def build_logic():
    build_choice()
    build_ammo(0)
    build_speed(1400)
    build_nuke(2200)
    build_rapid(4000)
    build_fortify(4600)
    build_freeze(5900)
    wire_up([
        "RapidBranch.else>FortifyBranch.execute", "FortifyBranch.else>FreezeBranch.execute",
        "SetForced.then>AmmoBranch.execute", "SetRandom.then>AmmoBranch.execute", "AmmoBranch.else>SpeedBranch.execute",
        "SpeedBranch.else>NukeBranch.execute", "NukeBranch.else>RapidBranch.execute",
    ])


def build_reload_event(y):
    # Each player's own game tracks their ammo, so every machine reloads its own copies.
    box("BoxReload", "Max Ammo: reload on every machine", -50, y - 80, 1750, 320, (0.1, 0.5, 0.15))
    Node("ReloadEvent", "K2Node_CustomEvent", 0, y, 'CustomFunctionName="DiceReloadAll"\n   FunctionFlags=16576') \
        .pin("OutputDelegate", "delegate", True).pin("then", "exec", True)
    call("WaitForRefill", 350, y, "Delay", SYSTEM).pin("execute", "exec").pin("then", "exec", True).pin("Duration", "float", False, "0.25")
    all_actors("Weapons", 700, y, WEAPON, "weapons")
    loop("WeaponLoop", 1050, y, f"Class'\"{WEAPON}\"'", "weapons", "weapon")
    call("Reload", 1400, y, "InstantlyReload", WEAPON).pin("execute", "exec").pin("then", "exec", True).pin("self", "weapon")
    wire_up([
        "ReloadEvent.then>WaitForRefill.execute", "WaitForRefill.then>Weapons.execute", "Weapons.then>WeaponLoop.Exec",
        "Weapons.OutActors>WeaponLoop.Array", "WeaponLoop.LoopBody>Reload.execute", "WeaponLoop.Array Element>Reload.self",
    ])


def scale_item(name, x, y, weapon, previous, parent, prop, operation, value):
    """Multiply or divide one weapon setting, as the next step of a loop."""
    ref = f"VariableReference=(MemberParent=Class'\"{parent}\"',MemberName=\"{prop}\")"
    Node(f"{name}Get", "K2Node_VariableGet", x - 100, y + 220, ref).pin(prop, "float", True).pin("self", "item")
    call(f"{name}Math", x + 100, y + 220, operation, MATH).pin("A", "float").pin("B", "float", False, value).pin("ReturnValue", "float", True)
    Node(f"{name}Set", "K2Node_VariableSet", x, y, ref).pin("execute", "exec").pin("then", "exec", True).pin(prop, "float").pin("self", "item")
    wire_up([
        f"{previous}>{name}Set.execute", f"{weapon}>{name}Get.self", f"{name}Get.{prop}>{name}Math.A",
        f"{name}Math.ReturnValue>{name}Set.{prop}", f"{weapon}>{name}Set.self",
    ])


def heat_settings(prefix, x, y, heat_operation, cool_operation):
    """Stop heat building up and make it drain almost instantly, or undo that."""
    weapon, previous = f"{prefix}Loop.Array Element", f"{prefix}Set.then"
    scale_item(f"{prefix}Heat", x, y, weapon, previous, ITEM, "ManualHeatPerUse", heat_operation, NO_HEAT_SCALE)
    scale_item(f"{prefix}Start", x + 350, y, weapon, f"{prefix}HeatSet.then", ITEM, "HeatOnStartUse", heat_operation, NO_HEAT_SCALE)
    scale_item(f"{prefix}Cool", x + 700, y, weapon, f"{prefix}StartSet.then", ITEM, "CooldownRate", cool_operation, FAST_COOLING_SCALE)


def curve_member(cls, name, x, y):
    return Node(name, cls, x, y, f"VariableReference=(MemberParent=Class'\"{ITEM}\"',MemberName=\"HeatCurve\")")


def clear_saved_curves(x, y):
    """Empty the saved curve list. An array SET can't be left with nothing wired in, so this uses Clear."""
    var_get("CurvesList", x, y + 150, "RapidFireCurves", "curves")
    Node("CurvesEmpty", "K2Node_CallArrayFunction", x, y, "FunctionReference=(MemberParent=Class'\"/Script/Engine.KismetArrayLibrary\"',MemberName=\"Array_Clear\")") \
        .pin("execute", "exec").pin("then", "exec", True).pin("TargetArray", "curves")
    wire_up(["CurvesList.RapidFireCurves>CurvesEmpty.TargetArray"])


def clear_heat_curve(x, y):
    """Save each weapon's heat curve, then swap in a flat one so held-fire weapons like the minigun don't heat up.
    Leaving the curve empty also stops the heat, but crashes the game when drills hit an enemy."""
    var_get("NoHeatGuns", x + 150, y + 220, "NoHeatCurve", "curve")
    curve_member("K2Node_VariableGet", "CurveRead", x, y + 220).pin("HeatCurve", "curve", True).pin("self", "item")
    var_get("CurveSaved", x + 100, y + 330, "RapidFireCurves", "curves")
    Node("CurveAdd", "K2Node_CallArrayFunction", x, y, "FunctionReference=(MemberParent=Class'\"/Script/Engine.KismetArrayLibrary\"',MemberName=\"Array_Add\")") \
        .pin("execute", "exec").pin("then", "exec", True).pin("TargetArray", "curves").pin("NewItem", "curve").pin("ReturnValue", "int", True)
    curve_member("K2Node_VariableSet", "CurveClear", x + 350, y).pin("execute", "exec").pin("then", "exec", True).pin("HeatCurve", "curve").pin("self", "item")
    wire_up([
        "NoHeatGuns.NoHeatCurve>CurveClear.HeatCurve", "FasterCoolSet.then>CurveAdd.execute", "FasterLoop.Array Element>CurveRead.self", "CurveRead.HeatCurve>CurveAdd.NewItem",
        "CurveSaved.RapidFireCurves>CurveAdd.TargetArray", "CurveAdd.then>CurveClear.execute", "FasterLoop.Array Element>CurveClear.self",
    ])


def restore_heat_curve(x, y):
    """Give each weapon its saved curve back. Both saved lists were filled in the same order."""
    var_get("CurveList", x - 200, y + 220, "RapidFireCurves", "curves")
    Node("CurveItem", "K2Node_GetArrayItem", x, y + 220).pin("Array", "curves").pin("Dimension 1", "int").pin("Output", "curve", True)
    curve_member("K2Node_VariableSet", "CurveRestore", x, y).pin("execute", "exec").pin("then", "exec", True).pin("HeatCurve", "curve").pin("self", "item")
    wire_up([
        "RestoreCoolSet.then>CurveRestore.execute", "RestoreLoop.Array Element>CurveRestore.self", "CurveList.RapidFireCurves>CurveItem.Array",
        "RestoreLoop.Array Index>CurveItem.Dimension 1", "CurveItem.Output>CurveRestore.HeatCurve",
    ])


def cannon_member(cls, name, x, y, prop):
    return Node(name, cls, x, y, f"VariableReference=(MemberParent=Class'\"{CANNON}\"',MemberName=\"{prop}\")")


def skip_cannon_ramp(x, y):
    """Double each Thunderhead's top speed, which RateOfFire doesn't affect, and start it there so it needs no spin-up."""
    all_actors("CannonFind", x, y, CANNON, "cannons")
    var_set("CannonSave", x + 350, y, "RapidFireCannons", "cannons")
    var_get("CannonRatesA", x + 650, y + 150, "RapidFireCannonRates", "floats")
    Node("CannonRatesEmpty", "K2Node_CallArrayFunction", x + 650, y, "FunctionReference=(MemberParent=Class'\"/Script/Engine.KismetArrayLibrary\"',MemberName=\"Array_Clear\")") \
        .pin("execute", "exec").pin("then", "exec", True).pin("TargetArray", "floats")
    var_get("CannonList", x + 950, y + 200, "RapidFireCannons", "cannons")
    loop("CannonLoop", x + 1200, y, f"Class'\"{CANNON}\"'", "cannons", "cannon")
    cannon_member("K2Node_VariableGet", "CannonStart", x + 1550, y + 220, "StartingFireRate").pin("StartingFireRate", "float", True).pin("self", "cannon")
    var_get("CannonRatesB", x + 1550, y + 330, "RapidFireCannonRates", "floats")
    Node("CannonAdd", "K2Node_CallArrayFunction", x + 1550, y, "FunctionReference=(MemberParent=Class'\"/Script/Engine.KismetArrayLibrary\"',MemberName=\"Array_Add\")") \
        .pin("execute", "exec").pin("then", "exec", True).pin("TargetArray", "floats").pin("NewItem", "float").pin("ReturnValue", "int", True)
    scale_item("CannonTop", x + 1900, y, "CannonLoop.Array Element", "CannonAdd.then", CANNON, "MaxFireRate", "Multiply_FloatFloat", RAPID_MULTIPLIER)
    cannon_member("K2Node_VariableGet", "CannonMax", x + 2250, y + 220, "MaxFireRate").pin("MaxFireRate", "float", True).pin("self", "cannon")
    cannon_member("K2Node_VariableSet", "CannonSet", x + 2250, y, "StartingFireRate").pin("execute", "exec").pin("then", "exec", True) \
        .pin("StartingFireRate", "float").pin("self", "cannon")
    wire_up([
        "CannonFind.then>CannonSave.execute", "CannonFind.OutActors>CannonSave.RapidFireCannons", "CannonSave.then>CannonRatesEmpty.execute",
        "CannonRatesA.RapidFireCannonRates>CannonRatesEmpty.TargetArray", "CannonRatesEmpty.then>CannonLoop.Exec", "CannonList.RapidFireCannons>CannonLoop.Array",
        "CannonLoop.LoopBody>CannonAdd.execute", "CannonLoop.Array Element>CannonStart.self", "CannonStart.StartingFireRate>CannonAdd.NewItem",
        "CannonRatesB.RapidFireCannonRates>CannonAdd.TargetArray", "CannonTopSet.then>CannonSet.execute", "CannonLoop.Array Element>CannonMax.self",
        "CannonMax.MaxFireRate>CannonSet.StartingFireRate", "CannonLoop.Array Element>CannonSet.self",
    ])


def restore_cannon_ramp(x, y):
    """Give each Thunderhead its saved starting fire rate and normal top speed back. Both saved lists were filled in the same order."""
    var_get("RestoreCannonList", x, y + 200, "RapidFireCannons", "cannons")
    loop("RestoreCannonLoop", x + 300, y, f"Class'\"{CANNON}\"'", "cannons", "cannon").pin("Array Index", "int", True)
    var_get("RestoreRates", x + 450, y + 330, "RapidFireCannonRates", "floats")
    Node("RestoreRate", "K2Node_GetArrayItem", x + 650, y + 220).pin("Array", "floats").pin("Dimension 1", "int").pin("Output", "float", True)
    cannon_member("K2Node_VariableSet", "RestoreCannonSet", x + 650, y, "StartingFireRate").pin("execute", "exec").pin("then", "exec", True) \
        .pin("StartingFireRate", "float").pin("self", "cannon")
    wire_up([
        "RestoreCannonList.RapidFireCannons>RestoreCannonLoop.Array", "RestoreCannonLoop.LoopBody>RestoreCannonSet.execute",
        "RestoreCannonLoop.Array Element>RestoreCannonSet.self", "RestoreRates.RapidFireCannonRates>RestoreRate.Array",
        "RestoreCannonLoop.Array Index>RestoreRate.Dimension 1", "RestoreRate.Output>RestoreCannonSet.StartingFireRate",
    ])
    scale_item("RestoreTop", x + 1000, y, "RestoreCannonLoop.Array Element", "RestoreCannonSet.then", CANNON, "MaxFireRate", "Divide_FloatFloat", RAPID_MULTIPLIER)


def hold_cryo_pressure(x, y):
    """The Cryo Cannon cuts out on low pressure rather than heat, so make its pressure drop almost nothing."""
    all_actors("CryoFind", x, y, CRYO, "cryos")
    var_set("CryoSave", x + 350, y, "RapidFireCryos", "cryos")
    var_get("CryoList", x + 650, y + 200, "RapidFireCryos", "cryos")
    loop("CryoLoop", x + 900, y, f"Class'\"{CRYO}\"'", "cryos", "cryo")
    scale_item("CryoDrop", x + 1250, y, "CryoLoop.Array Element", "CryoLoop.LoopBody", CRYO, "PressureDropMultiplier", "Multiply_FloatFloat", NO_HEAT_SCALE)
    wire_up(["CryoFind.then>CryoSave.execute", "CryoFind.OutActors>CryoSave.RapidFireCryos", "CryoSave.then>CryoLoop.Exec", "CryoList.RapidFireCryos>CryoLoop.Array"])


def restore_cryo_pressure(x, y):
    var_get("RestoreCryoList", x, y + 200, "RapidFireCryos", "cryos")
    loop("RestoreCryoLoop", x + 300, y, f"Class'\"{CRYO}\"'", "cryos", "cryo")
    scale_item("RestoreCryo", x + 650, y, "RestoreCryoLoop.Array Element", "RestoreCryoLoop.LoopBody", CRYO, "PressureDropMultiplier", "Divide_FloatFloat", NO_HEAT_SCALE)
    wire_up(["RestoreCryoList.RapidFireCryos>RestoreCryoLoop.Array"])


def skip_drill_heat(x, y):
    """Drills aren't Ammo Driven Weapons, so they get their own list. Same heat changes, saving each drill's curve first."""
    all_actors("DrillFind", x, y, DRILL, "drills")
    var_set("DrillSave", x + 350, y, "RapidFireDrills", "drills")
    var_get("DrillCurvesA", x + 650, y + 150, "RapidFireDrillCurves", "curves")
    Node("DrillCurvesEmpty", "K2Node_CallArrayFunction", x + 650, y, "FunctionReference=(MemberParent=Class'\"/Script/Engine.KismetArrayLibrary\"',MemberName=\"Array_Clear\")") \
        .pin("execute", "exec").pin("then", "exec", True).pin("TargetArray", "curves")
    var_get("DrillList", x + 950, y + 200, "RapidFireDrills", "drills")
    loop("DrillLoop", x + 1200, y, f"Class'\"{DRILL}\"'", "drills", "drill")
    curve_member("K2Node_VariableGet", "DrillCurveRead", x + 1550, y + 220).pin("HeatCurve", "curve", True).pin("self", "item")
    var_get("DrillCurvesB", x + 1550, y + 330, "RapidFireDrillCurves", "curves")
    Node("DrillCurveAdd", "K2Node_CallArrayFunction", x + 1550, y, "FunctionReference=(MemberParent=Class'\"/Script/Engine.KismetArrayLibrary\"',MemberName=\"Array_Add\")") \
        .pin("execute", "exec").pin("then", "exec", True).pin("TargetArray", "curves").pin("NewItem", "curve").pin("ReturnValue", "int", True)
    curve_member("K2Node_VariableSet", "DrillCurveClear", x + 1900, y).pin("execute", "exec").pin("then", "exec", True).pin("HeatCurve", "curve").pin("self", "item")
    var_get("NoHeatDrills", x + 1900, y + 220, "NoHeatCurve", "curve")
    wire_up([
        "NoHeatDrills.NoHeatCurve>DrillCurveClear.HeatCurve",
        "DrillFind.then>DrillSave.execute", "DrillFind.OutActors>DrillSave.RapidFireDrills", "DrillSave.then>DrillCurvesEmpty.execute",
        "DrillCurvesA.RapidFireDrillCurves>DrillCurvesEmpty.TargetArray", "DrillCurvesEmpty.then>DrillLoop.Exec", "DrillList.RapidFireDrills>DrillLoop.Array",
        "DrillLoop.LoopBody>DrillCurveAdd.execute", "DrillLoop.Array Element>DrillCurveRead.self", "DrillCurveRead.HeatCurve>DrillCurveAdd.NewItem",
        "DrillCurvesB.RapidFireDrillCurves>DrillCurveAdd.TargetArray", "DrillCurveAdd.then>DrillCurveClear.execute", "DrillLoop.Array Element>DrillCurveClear.self",
    ])
    element = "DrillLoop.Array Element"
    scale_item("DrillHeat", x + 2250, y, element, "DrillCurveClear.then", ITEM, "ManualHeatPerUse", "Multiply_FloatFloat", NO_HEAT_SCALE)
    scale_item("DrillStart", x + 2600, y, element, "DrillHeatSet.then", ITEM, "HeatOnStartUse", "Multiply_FloatFloat", NO_HEAT_SCALE)
    scale_item("DrillCool", x + 2950, y, element, "DrillStartSet.then", ITEM, "CooldownRate", "Multiply_FloatFloat", FAST_COOLING_SCALE)


def restore_drill_heat(x, y):
    """Give each drill its saved curve and normal heat settings back. Both saved lists were filled in the same order."""
    var_get("RestoreDrillList", x, y + 200, "RapidFireDrills", "drills")
    loop("RestoreDrillLoop", x + 300, y, f"Class'\"{DRILL}\"'", "drills", "drill").pin("Array Index", "int", True)
    var_get("RestoreDrillCurves", x + 450, y + 330, "RapidFireDrillCurves", "curves")
    Node("RestoreDrillItem", "K2Node_GetArrayItem", x + 650, y + 220).pin("Array", "curves").pin("Dimension 1", "int").pin("Output", "curve", True)
    curve_member("K2Node_VariableSet", "RestoreDrillCurve", x + 650, y).pin("execute", "exec").pin("then", "exec", True).pin("HeatCurve", "curve").pin("self", "item")
    element = "RestoreDrillLoop.Array Element"
    wire_up([
        "RestoreDrillList.RapidFireDrills>RestoreDrillLoop.Array", "RestoreDrillLoop.LoopBody>RestoreDrillCurve.execute", f"{element}>RestoreDrillCurve.self",
        "RestoreDrillCurves.RapidFireDrillCurves>RestoreDrillItem.Array", "RestoreDrillLoop.Array Index>RestoreDrillItem.Dimension 1",
        "RestoreDrillItem.Output>RestoreDrillCurve.HeatCurve",
    ])
    scale_item("RestoreDrillHeat", x + 1000, y, element, "RestoreDrillCurve.then", ITEM, "ManualHeatPerUse", "Divide_FloatFloat", NO_HEAT_SCALE)
    scale_item("RestoreDrillStart", x + 1350, y, element, "RestoreDrillHeatSet.then", ITEM, "HeatOnStartUse", "Divide_FloatFloat", NO_HEAT_SCALE)
    scale_item("RestoreDrillCool", x + 1700, y, element, "RestoreDrillStartSet.then", ITEM, "CooldownRate", "Divide_FloatFloat", FAST_COOLING_SCALE)


def cool_drills(y):
    """The drills' part of the 0.1 s heat check."""
    var_get("DrillTickList", 3700, y + 200, "RapidFireDrills", "drills")
    loop("DrillTickLoop", 3950, y, f"Class'\"{DRILL}\"'", "drills", "drill")
    Node("DrillTickTemperature", "K2Node_VariableSet", 4300, y, f"VariableReference=(MemberParent=Class'\"{ITEM}\"',MemberName=\"CurrentTemperature\")") \
        .pin("execute", "exec").pin("then", "exec", True).pin("CurrentTemperature", "float", False, "0.0").pin("self", "item")
    Node("DrillTickOverheated", "K2Node_VariableSet", 4650, y, f"VariableReference=(MemberParent=Class'\"{ITEM}\"',MemberName=\"overheated\")") \
        .pin("execute", "exec").pin("then", "exec", True).pin("overheated", "bool", False, "false").pin("self", "item")
    wire_up([
        "DrillTickList.RapidFireDrills>DrillTickLoop.Array", "DrillTickLoop.LoopBody>DrillTickTemperature.execute", "DrillTickLoop.Array Element>DrillTickTemperature.self",
        "DrillTickTemperature.then>DrillTickOverheated.execute", "DrillTickLoop.Array Element>DrillTickOverheated.self",
    ])


def rate_pass(prefix, x, y, operation, value):
    """Change the fire rate of every weapon in the saved list."""
    var_get(f"{prefix}List", x, y + 200, "RapidFireWeapons", "weapons")
    loop(f"{prefix}Loop", x + 300, y, f"Class'\"{WEAPON}\"'", "weapons", "weapon").pin("Array Index", "int", True)
    Node(f"{prefix}Get", "K2Node_VariableGet", x + 650, y + 250, f"VariableReference=(MemberParent=Class'\"{WEAPON}\"',MemberName=\"RateOfFire\")") \
        .pin("RateOfFire", "float", True).pin("self", "weapon")
    call(f"{prefix}Math", x + 900, y + 250, operation, MATH).pin("A", "float").pin("B", "float", False, value).pin("ReturnValue", "float", True)
    Node(f"{prefix}Set", "K2Node_VariableSet", x + 1200, y, f"VariableReference=(MemberParent=Class'\"{WEAPON}\"',MemberName=\"RateOfFire\")") \
        .pin("execute", "exec").pin("then", "exec", True).pin("RateOfFire", "float").pin("self", "weapon")
    p = prefix
    wire_up([
        f"{p}List.RapidFireWeapons>{p}Loop.Array", f"{p}Loop.LoopBody>{p}Set.execute", f"{p}Loop.Array Element>{p}Get.self",
        f"{p}Get.RateOfFire>{p}Math.A", f"{p}Math.ReturnValue>{p}Set.RateOfFire", f"{p}Loop.Array Element>{p}Set.self",
    ])


def build_cooling(y):
    """While Rapid Fire is active, keep clearing the heat on the saved weapons."""
    cool_drills(y)
    var_get("CoolActive", 1600, y + 200, "RapidFireActive", "bool")
    branch("CoolCheck", 1600, y)
    var_get("CoolList", 1900, y + 200, "RapidFireWeapons", "weapons")
    loop("CoolLoop", 1900, y, f"Class'\"{WEAPON}\"'", "weapons", "weapon")
    Node("CoolTemperature", "K2Node_VariableSet", 2250, y, f"VariableReference=(MemberParent=Class'\"{ITEM}\"',MemberName=\"CurrentTemperature\")") \
        .pin("execute", "exec").pin("then", "exec", True).pin("CurrentTemperature", "float", False, "0.0").pin("self", "item")
    Node("CoolOverheated", "K2Node_VariableSet", 2600, y, f"VariableReference=(MemberParent=Class'\"{ITEM}\"',MemberName=\"overheated\")") \
        .pin("execute", "exec").pin("then", "exec", True).pin("overheated", "bool", False, "false").pin("self", "item")
    call("CoolWait", 2250, y + 250, "Delay", SYSTEM).pin("execute", "exec").pin("then", "exec", True).pin("Duration", "float", False, COOLING_SECONDS)

    # Top up from reserves at half a magazine, early enough that no weapon runs dry and starts its reload animation.
    Node("ClipCount", "K2Node_VariableGet", 2600, y + 220, f"VariableReference=(MemberParent=Class'\"{WEAPON}\"',MemberName=\"ClipCount\")") \
        .pin("ClipCount", "int", True).pin("self", "weapon")
    call("ClipDouble", 2800, y + 220, "Multiply_IntInt", MATH).pin("A", "int").pin("B", "int", False, "2").pin("ReturnValue", "int", True)
    Node("ClipSize", "K2Node_VariableGet", 2800, y + 340, f"VariableReference=(MemberParent=Class'\"{WEAPON}\"',MemberName=\"ClipSize\")") \
        .pin("ClipSize", "int", True).pin("self", "weapon")
    call("ClipLow", 3000, y + 220, "LessEqual_IntInt", MATH).pin("A", "int").pin("B", "int").pin("ReturnValue", "bool", True)
    branch("ClipCheck", 2950, y)
    call("ClipReload", 3250, y, "InstantlyReload", WEAPON).pin("execute", "exec").pin("then", "exec", True).pin("self", "weapon")
    wire_up([
        "CoolOverheated.then>ClipCheck.execute", "CoolLoop.Array Element>ClipCount.self", "ClipCount.ClipCount>ClipDouble.A",
        "ClipDouble.ReturnValue>ClipLow.A", "CoolLoop.Array Element>ClipSize.self", "ClipSize.ClipSize>ClipLow.B",
        "ClipLow.ReturnValue>ClipCheck.Condition", "ClipCheck.then>ClipReload.execute", "CoolLoop.Array Element>ClipReload.self",
    ])
    wire_up([
        "CoolActive.RapidFireActive>CoolCheck.Condition", "CoolCheck.then>CoolLoop.Exec", "CoolList.RapidFireWeapons>CoolLoop.Array",
        "CoolLoop.LoopBody>CoolTemperature.execute", "CoolLoop.Array Element>CoolTemperature.self", "CoolTemperature.then>CoolOverheated.execute",
        "CoolLoop.Array Element>CoolOverheated.self", "CoolLoop.Completed>DrillTickLoop.Exec", "DrillTickLoop.Completed>CoolWait.execute", "CoolWait.then>CoolCheck.execute",
    ])


def build_rapid_chain(y):
    """Everything DiceRapidFire runs. Firing runs on each player's own machine, so every machine changes its own weapons."""
    Node("RapidSequence", "K2Node_ExecutionSequence", 1300, y + 450).pin("execute", "exec").pin("then_0", "exec", True).pin("then_1", "exec", True)
    build_cooling(y + 450)
    wire_up(["RapidSequence.then_1>CoolCheck.execute"])
    # A second roll mid-effect is ignored, or the rate would stack and never fully come back down.
    var_get("RapidActive", 0, y + 200, "RapidFireActive", "bool")
    branch("RapidGuard", 350, y)
    var_set("RapidOn", 650, y, "RapidFireActive", "bool", "true")
    all_actors("RapidWeapons", 950, y, WEAPON, "weapons")
    # Only the saved weapons get restored, so a weapon that appears mid-effect doesn't end up slowed.
    var_set("RapidSave", 1300, y, "RapidFireWeapons", "weapons")
    rate_pass("Faster", 1600, y, "Multiply_FloatFloat", RAPID_MULTIPLIER)
    heat_settings("Faster", 3150, y, "Multiply_FloatFloat", "Multiply_FloatFloat")
    clear_heat_curve(4200, y)
    call("RapidWait", 4950, y, "Delay", SYSTEM).pin("execute", "exec").pin("then", "exec", True).pin("Duration", "float", False, RAPID_SECONDS)
    rate_pass("Restore", 5250, y, "Divide_FloatFloat", RAPID_MULTIPLIER)
    heat_settings("Restore", 6800, y, "Divide_FloatFloat", "Divide_FloatFloat")
    restore_heat_curve(7850, y)
    var_set("RapidOff", 8200, y, "RapidFireActive", "bool", "false")
    clear_saved_curves(1000, y + 450)
    skip_cannon_ramp(1600, y + 850)
    restore_cannon_ramp(5250, y + 850)
    hold_cryo_pressure(1600, y + 1300)
    restore_cryo_pressure(5250, y + 1300)
    skip_drill_heat(1600, y + 1750)
    restore_drill_heat(5250, y + 1750)
    wire_up([
        "RapidActive.RapidFireActive>RapidGuard.Condition", "RapidGuard.else>RapidOn.execute",
        "RapidOn.then>RapidWeapons.execute", "RapidWeapons.then>RapidSave.execute", "RapidWeapons.OutActors>RapidSave.RapidFireWeapons",
        "RapidSave.then>CurvesEmpty.execute", "CurvesEmpty.then>RapidSequence.execute", "RapidSequence.then_0>FasterLoop.Exec", "FasterLoop.Completed>CannonFind.execute", "CannonLoop.Completed>CryoFind.execute", "CryoLoop.Completed>DrillFind.execute", "DrillLoop.Completed>RapidWait.execute", "RapidWait.then>RestoreLoop.Exec",
        "RestoreLoop.Completed>RestoreCannonLoop.Exec", "RestoreCannonLoop.Completed>RestoreCryoLoop.Exec", "RestoreCryoLoop.Completed>RestoreDrillLoop.Exec", "RestoreDrillLoop.Completed>RapidOff.execute",
    ])


def build_rapid_event(y):
    box("BoxRapidEvent", "Rapid Fire: change fire rate on every machine", -50, y - 80, 8600, 2300, (0.6, 0.45, 0.05))
    Node("RapidEvent", "K2Node_CustomEvent", 0, y, 'CustomFunctionName="DiceRapidFire"\n   FunctionFlags=16576') \
        .pin("OutputDelegate", "delegate", True).pin("then", "exec", True)
    build_rapid_chain(y)
    wire_up(["RapidEvent.then>RapidGuard.execute"])


def pin_text(name, pin):
    category, sub_object, container = TYPES[pin["kind"]]
    parts = [f"PinId={pin['id']}", f'PinName="{name}"']
    if pin["out"]:
        parts.append('Direction="EGPD_Output"')
    parts.append(f'PinType.PinCategory="{category}"')
    if sub_object:
        parts.append(f"PinType.PinSubCategoryObject={sub_object}")
    if container:
        parts.append(f"PinType.ContainerType={container}")
    if pin["default"] is not None:
        parts.append(f'DefaultValue="{pin["default"]}"')
    if pin["object"] is not None:
        parts.append(f'DefaultObject="{pin["object"]}"')
    if pin["links"]:
        parts.append("LinkedTo=(" + ",".join(f"{n} {p}" for n, p in pin["links"]) + ",)")
    return "   CustomProperties Pin (" + ",".join(parts) + ",)"


def node_text(node):
    cls = node.cls if node.cls.startswith("/") else f"/Script/BlueprintGraph.{node.cls}"
    lines = [f'Begin Object Class={cls} Name="{node.name}"']
    if node.body:
        lines.append(f"   {node.body}")
    lines += [f"   NodePosX={node.x}", f"   NodePosY={node.y}", f"   NodeGuid={uuid.uuid4().hex.upper()}"]
    lines += [pin_text(n, p) for n, p in node.pins.items()]
    lines.append("End Object")
    return "\n".join(lines)


def main():
    if len(sys.argv) != 3 or sys.argv[2] not in ("--events", "--logic", "--reload-only", "--rapid-chain", "--curve-clear", "--fortify-only", "--settings-loader", "--settings-widget", "--debug-readout", "--fortify-heal", "--freeze-only", "--unfreeze-only"):
        sys.exit(__doc__)
    if sys.argv[2] == "--fortify-heal":
        build_fortify_heal(0, 0)
        NODES["HealCount"].body += '\n   NodeComment="CONNECT the FORTIFY! Post Game Message HERE"\n   bCommentBubbleVisible=True\n   bCommentBubblePinned=True'
    elif sys.argv[2] == "--debug-readout":
        build_debug_readout()
    elif sys.argv[2] == "--settings-loader":
        build_settings_loader()
    elif sys.argv[2] == "--settings-widget":
        build_settings_widget()
    elif sys.argv[2] == "--unfreeze-only":
        build_unfreeze(0, 0)
        NODES["ThawRegularSave"].body += '\n   NodeComment="CONNECT the Freeze Branch False HERE"\n   bCommentBubbleVisible=True\n   bCommentBubblePinned=True'
    elif sys.argv[2] == "--freeze-only":
        build_freeze(0)
    elif sys.argv[2] == "--fortify-only":
        build_fortify(0)
    elif sys.argv[2] == "--reload-only":
        build_reload_event(0)
    elif sys.argv[2] == "--curve-clear":
        clear_saved_curves(0, 0)
    elif sys.argv[2] == "--rapid-chain":
        build_rapid_chain(0)
        NODES["RapidGuard"].body = 'NodeComment="CONNECT DiceRapidFire HERE"\n   bCommentBubbleVisible=True\n   bCommentBubblePinned=True'
    elif sys.argv[2] == "--events":
        build_reload_event(0)
        build_rapid_event(450)
    else:
        build_logic()
    text = "\n".join(node_text(n) for n in NODES.values()) + "\n"
    with open(sys.argv[1], "w", newline="\r\n", encoding="utf-8") as f:
        f.write(text)
    links = sum(len(p["links"]) for n in NODES.values() for p in n.pins.values()) // 2
    print(f"{len(NODES)} nodes, {links} links, {len(text)} characters")


main()
