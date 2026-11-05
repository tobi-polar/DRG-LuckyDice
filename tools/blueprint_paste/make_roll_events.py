"""Generate BP_DiceManager's event logic as text to paste.

Usage: python make_roll_events.py <output.txt> --events | --logic | --reload-only | --rapid-chain | --curve-clear

--curve-clear writes just the node that empties RapidFireCurves.

--reload-only writes just the DiceReloadAll event, to replace one that pasted with
the wrong name. Delete the old one and compile before pasting, so the name is free.

--rapid-chain writes everything DiceRapidFire runs, without the event itself. Keep the
event, delete what it runs, paste this, and connect the event to the marked Branch.

Paste into the Event Graph of BP_DiceManager, which needs the Integer variables
ForceEvent (default -1) and EventId, NukeTargets (Pawn array), RapidFireActive
(Boolean), RapidFireWeapons (Ammo Driven Weapon array) and RapidFireCurves (Curve
Float array). ForceEvent picks the event
for testing: 0 Max Ammo, 1 Speed Boost, 2 Nuke, 3 Rapid Fire. Any negative value
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
TYPES = {
    "curve": ("object", f"Class'\"{CURVE}\"'", None), "curves": ("object", f"Class'\"{CURVE}\"'", "Array"),
    "item": ("object", f"Class'\"{ITEM}\"'", None),
    "pawn": ("object", f"Class'\"{PAWN}\"'", None), "pawns": ("object", f"Class'\"{PAWN}\"'", "Array"),
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
OBJECTS = {"actor", "self", "state", "component", "inventory", "weapon", "sentry", "pawn", "health", "item"}
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
    call("RandomEvent", -900, 350, "RandomIntegerInRange", MATH).pin("Min", "int", False, "0").pin("Max", "int", False, "3") \
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


def build_logic():
    build_choice()
    build_ammo(0)
    build_speed(1400)
    build_nuke(2200)
    build_rapid(4000)
    wire_up([
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
    """Save each weapon's heat curve, then remove it. With no curve, held-fire weapons like the minigun don't heat up."""
    curve_member("K2Node_VariableGet", "CurveRead", x, y + 220).pin("HeatCurve", "curve", True).pin("self", "item")
    var_get("CurveSaved", x + 100, y + 330, "RapidFireCurves", "curves")
    Node("CurveAdd", "K2Node_CallArrayFunction", x, y, "FunctionReference=(MemberParent=Class'\"/Script/Engine.KismetArrayLibrary\"',MemberName=\"Array_Add\")") \
        .pin("execute", "exec").pin("then", "exec", True).pin("TargetArray", "curves").pin("NewItem", "curve").pin("ReturnValue", "int", True)
    curve_member("K2Node_VariableSet", "CurveClear", x + 350, y).pin("execute", "exec").pin("then", "exec", True).pin("HeatCurve", "curve").pin("self", "item")
    wire_up([
        "FasterCoolSet.then>CurveAdd.execute", "FasterLoop.Array Element>CurveRead.self", "CurveRead.HeatCurve>CurveAdd.NewItem",
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
    var_get("CoolActive", 1600, y + 200, "RapidFireActive", "bool")
    branch("CoolCheck", 1600, y)
    var_get("CoolList", 1900, y + 200, "RapidFireWeapons", "weapons")
    loop("CoolLoop", 1900, y, f"Class'\"{WEAPON}\"'", "weapons", "weapon")
    Node("CoolTemperature", "K2Node_VariableSet", 2250, y, f"VariableReference=(MemberParent=Class'\"{ITEM}\"',MemberName=\"CurrentTemperature\")") \
        .pin("execute", "exec").pin("then", "exec", True).pin("CurrentTemperature", "float", False, "0.0").pin("self", "item")
    Node("CoolOverheated", "K2Node_VariableSet", 2600, y, f"VariableReference=(MemberParent=Class'\"{ITEM}\"',MemberName=\"overheated\")") \
        .pin("execute", "exec").pin("then", "exec", True).pin("overheated", "bool", False, "false").pin("self", "item")
    call("CoolWait", 2250, y + 250, "Delay", SYSTEM).pin("execute", "exec").pin("then", "exec", True).pin("Duration", "float", False, COOLING_SECONDS)
    wire_up([
        "CoolActive.RapidFireActive>CoolCheck.Condition", "CoolCheck.then>CoolLoop.Exec", "CoolList.RapidFireWeapons>CoolLoop.Array",
        "CoolLoop.LoopBody>CoolTemperature.execute", "CoolLoop.Array Element>CoolTemperature.self", "CoolTemperature.then>CoolOverheated.execute",
        "CoolLoop.Array Element>CoolOverheated.self", "CoolLoop.Completed>CoolWait.execute", "CoolWait.then>CoolCheck.execute",
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
    wire_up([
        "RapidActive.RapidFireActive>RapidGuard.Condition", "RapidGuard.else>RapidOn.execute",
        "RapidOn.then>RapidWeapons.execute", "RapidWeapons.then>RapidSave.execute", "RapidWeapons.OutActors>RapidSave.RapidFireWeapons",
        "RapidSave.then>CurvesEmpty.execute", "CurvesEmpty.then>RapidSequence.execute", "RapidSequence.then_0>FasterLoop.Exec", "FasterLoop.Completed>RapidWait.execute", "RapidWait.then>RestoreLoop.Exec",
        "RestoreLoop.Completed>RapidOff.execute",
    ])


def build_rapid_event(y):
    box("BoxRapidEvent", "Rapid Fire: change fire rate on every machine", -50, y - 80, 8600, 960, (0.6, 0.45, 0.05))
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
    if len(sys.argv) != 3 or sys.argv[2] not in ("--events", "--logic", "--reload-only", "--rapid-chain", "--curve-clear"):
        sys.exit(__doc__)
    if sys.argv[2] == "--reload-only":
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
