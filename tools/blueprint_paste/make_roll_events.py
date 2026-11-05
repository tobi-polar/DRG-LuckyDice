"""Generate BP_DiceManager's event logic as text to paste.

Usage: python make_roll_events.py <output.txt>

Paste into the Event Graph of BP_DiceManager, which needs the Integer variables
ForceEvent (default -1) and EventId. Connect the RollDice event to the first
Branch. ForceEvent picks the event for testing: 0 Full Ammo, 1 Speed Boost.
Any negative value rolls at random.

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
TYPES = {
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
OBJECTS = {"actor", "self", "state", "component", "inventory", "weapon", "sentry"}
MATH = "/Script/Engine.KismetMathLibrary"
LIBRARY = "/Script/FSD.GameFunctionLibrary"
STATUS = "/Script/FSD.StatusEffectsComponent"
GAMEPLAY = "/Script/Engine.GameplayStatics"
SYSTEM = "/Script/Engine.KismetSystemLibrary"
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


def call(name, x, y, function, parent):
    ref = f"FunctionReference=(MemberParent=Class'\"{parent}\"',MemberName=\"{function}\")"
    return Node(name, "K2Node_CallFunction", x, y, ref)


def var_get(name, x, y, variable, kind):
    ref = f"VariableReference=(MemberName=\"{variable}\",bSelfContext=True)"
    return Node(name, "K2Node_VariableGet", x, y, ref).pin(variable, kind, True)


def var_set(name, x, y, variable, kind):
    ref = f"VariableReference=(MemberName=\"{variable}\",bSelfContext=True)"
    return Node(name, "K2Node_VariableSet", x, y, ref).pin("execute", "exec").pin("then", "exec", True).pin(variable, kind)


def branch(name, x, y):
    return Node(name, "K2Node_IfThenElse", x, y).pin("execute", "exec").pin("Condition", "bool") \
        .pin("then", "exec", True).pin("else", "exec", True)


def equals(name, x, y, value):
    return call(name, x, y, "EqualEqual_IntInt", MATH).pin("A", "int").pin("B", "int", False, str(value)).pin("ReturnValue", "bool", True)


def push(name, x, y, effect):
    return call(name, x, y, "TryPushActiveStatusEffect", STATUS).pin("execute", "exec").pin("then", "exec", True) \
        .pin("StatusEffect", "effect", False, None, f"/Game/LuckyDice/{effect}.{effect}_C") \
        .pin("Target", "actor").pin("Owner", "actor")


def message(name, x, y, text):
    return call(name, x, y, "PostGameMessage", "/Script/FSD.FSDGameState").pin("execute", "exec").pin("then", "exec", True) \
        .pin("self", "state").pin("Msg", "string", False, text)


def link(src, src_pin, dst, dst_pin):
    a, b = NODES[src].pins[src_pin], NODES[dst].pins[dst_pin]
    if not a["out"] or b["out"]:
        raise ValueError(f"{src}.{src_pin} -> {dst}.{dst_pin} has the wrong direction")
    if a["kind"] != b["kind"] and not (a["kind"] in OBJECTS and b["kind"] in OBJECTS):
        raise ValueError(f"{src}.{src_pin} -> {dst}.{dst_pin} has mismatched types")
    a["links"].append((dst, b["id"]))
    b["links"].append((src, a["id"]))


def build():
    # Choose the event: forced for testing, otherwise at random.
    branch("IsForced", 0, 0)
    var_get("GetForceA", -300, 150, "ForceEvent", "int")
    call("ForceSet", 0, 150, "GreaterEqual_IntInt", MATH).pin("A", "int").pin("B", "int", False, "0").pin("ReturnValue", "bool", True)
    var_get("GetForceB", 300, 150, "ForceEvent", "int")
    var_set("SetForced", 500, 0, "EventId", "int")
    call("RandomEvent", 300, 350, "RandomIntegerInRange", MATH).pin("Min", "int", False, "0").pin("Max", "int", False, "1") \
        .pin("ReturnValue", "int", True)
    var_set("SetRandom", 500, 250, "EventId", "int")

    # Apply it to every player.
    Node("Players", "K2Node_CallFunction", 850, 0,
         f"FunctionReference=(MemberParent=Class'\"{GAMEPLAY}\"',MemberName=\"GetAllActorsOfClass\")") \
        .pin("execute", "exec").pin("then", "exec", True).pin("ActorClass", "class", False, None, PLAYER).pin("OutActors", "actors", True)
    Node("Loop", "K2Node_MacroInstance", 1200, 0, for_each(ACTOR)).pin("Exec", "exec").pin("Array", "actors") \
        .pin("LoopBody", "exec", True).pin("Array Element", "actor", True).pin("Completed", "exec", True)

    var_get("GetIdA", 1200, 300, "EventId", "int")
    equals("IsAmmo", 1500, 300, 0)
    branch("ApplyAmmo", 1550, 0)
    Node("FindInventory", "K2Node_CallFunction", 1850, 0, "FunctionReference=(MemberName=\"GetComponentByClass\",MemberParent=Class'\"/Script/Engine.Actor\"')") \
        .pin("execute", "exec").pin("then", "exec", True).pin("self", "actor") \
        .pin("ComponentClass", "componentclass", False, None, INVENTORY).pin("ReturnValue", "component", True)
    Node("AsInventory", "K2Node_DynamicCast", 2200, 0, f"TargetType=Class'\"{INVENTORY}\"'").pin("execute", "exec") \
        .pin("then", "exec", True).pin("CastFailed", "exec", True).pin("Object", "component") \
        .pin("AsInventory Component", "inventory", True).pin("bSuccess", "bool", True)
    call("Refill", 2550, 0, "Resupply", INVENTORY).pin("execute", "exec").pin("then", "exec", True).pin("self", "inventory") \
        .pin("percentage", "float", False, "1.0")

    equals("IsSpeed", 1500, 650, 1)
    branch("ApplySpeed", 1850, 500)
    Node("Self", "K2Node_Self", 1850, 800).pin("self", "self", True)
    push("GiveSpeed", 2200, 450, "STE_Dice_Speed")

    # Announce it once, after the loop.
    var_get("GetIdB", 1200, 1150, "EventId", "int")
    call("GameState", 2100, 1250, "GetFSDGameState", LIBRARY).pin("ReturnValue", "state", True)
    equals("SayAmmoCheck", 1500, 1150, 0)
    branch("SayAmmo", 1800, 1050)
    message("MsgAmmo", 2300, 1000, "Lucky Dice: FULL AMMO!")
    equals("SaySpeedCheck", 1500, 1400, 1)
    branch("SaySpeed", 1800, 1350)
    message("MsgSpeed", 2300, 1250, "Lucky Dice: SPEED BOOST!")

    # Full Ammo also fills every deployed turret, on the host.
    Node("Sentries", "K2Node_CallFunction", 2650, 1000,
         f"FunctionReference=(MemberParent=Class'\"{GAMEPLAY}\"',MemberName=\"GetAllActorsOfClass\")") \
        .pin("execute", "exec").pin("then", "exec", True).pin("ActorClass", "class", False, None, SENTRY).pin("OutActors", "sentries", True)
    Node("SentryLoop", "K2Node_MacroInstance", 3000, 1000, for_each(f"Class'\"{SENTRY}\"'")).pin("Exec", "exec").pin("Array", "sentries") \
        .pin("LoopBody", "exec", True).pin("Array Element", "sentry", True).pin("Completed", "exec", True)
    call("SentryMax", 3300, 1250, "GetMaxAmmoCount", SENTRY).pin("self", "sentry").pin("ReturnValue", "int", True)
    Node("SentryFill", "K2Node_VariableSet", 3650, 950, f"VariableReference=(MemberParent=Class'\"{SENTRY}\"',MemberName=\"AmmoCount\")") \
        .pin("execute", "exec").pin("then", "exec", True).pin("AmmoCount", "int").pin("self", "sentry")
    # Setting the value alone leaves the HUD stale, so overfill by one and spend it through the game's own call.
    call("SentryPlusOne", 3450, 1250, "Add_IntInt", MATH).pin("A", "int").pin("B", "int", False, "1").pin("ReturnValue", "int", True)
    call("SentryUpdate", 4000, 950, "UseAmmo", SENTRY).pin("execute", "exec").pin("then", "exec", True).pin("self", "sentry") \
        .pin("amount", "int", False, "1")

    # Reloading uses reserve ammo, so refill the reserves again afterwards.
    Node("CallReload", "K2Node_CallFunction", 3300, 1450, "FunctionReference=(MemberName=\"DiceReloadWeapons\",bSelfContext=True)") \
        .pin("execute", "exec").pin("then", "exec", True)
    call("WaitForReload", 3650, 1450, "Delay", SYSTEM).pin("execute", "exec").pin("then", "exec", True).pin("Duration", "float", False, "0.5")
    Node("TopUpLoop", "K2Node_MacroInstance", 4000, 1450, for_each(ACTOR)).pin("Exec", "exec").pin("Array", "actors") \
        .pin("LoopBody", "exec", True).pin("Array Element", "actor", True).pin("Completed", "exec", True)
    Node("TopUpFind", "K2Node_CallFunction", 4300, 1450, "FunctionReference=(MemberName=\"GetComponentByClass\",MemberParent=Class'\"/Script/Engine.Actor\"')") \
        .pin("execute", "exec").pin("then", "exec", True).pin("self", "actor") \
        .pin("ComponentClass", "componentclass", False, None, INVENTORY).pin("ReturnValue", "component", True)
    Node("TopUpCast", "K2Node_DynamicCast", 4650, 1450, f"TargetType=Class'\"{INVENTORY}\"'").pin("execute", "exec") \
        .pin("then", "exec", True).pin("CastFailed", "exec", True).pin("Object", "component") \
        .pin("AsInventory Component", "inventory", True).pin("bSuccess", "bool", True)
    call("TopUp", 5000, 1450, "Resupply", INVENTORY).pin("execute", "exec").pin("then", "exec", True).pin("self", "inventory") \
        .pin("percentage", "float", False, "1.0")

    # Each player's own game tracks their ammo, so every machine reloads its own copies.
    Node("ReloadEvent", "K2Node_CustomEvent", 0, 1800, 'CustomFunctionName="DiceReloadWeapons"\n   FunctionFlags=16576') \
        .pin("OutputDelegate", "delegate", True).pin("then", "exec", True)
    call("WaitForRefill", 350, 1800, "Delay", SYSTEM).pin("execute", "exec").pin("then", "exec", True).pin("Duration", "float", False, "0.25")
    Node("Weapons", "K2Node_CallFunction", 700, 1800,
         f"FunctionReference=(MemberParent=Class'\"{GAMEPLAY}\"',MemberName=\"GetAllActorsOfClass\")") \
        .pin("execute", "exec").pin("then", "exec", True).pin("ActorClass", "class", False, None, WEAPON).pin("OutActors", "weapons", True)
    Node("WeaponLoop", "K2Node_MacroInstance", 1050, 1800, for_each(f"Class'\"{WEAPON}\"'")).pin("Exec", "exec").pin("Array", "weapons") \
        .pin("LoopBody", "exec", True).pin("Array Element", "weapon", True).pin("Completed", "exec", True)
    call("Reload", 1400, 1800, "InstantlyReload", WEAPON).pin("execute", "exec").pin("then", "exec", True).pin("self", "weapon")

    for wire in [
        "GetForceA.ForceEvent>ForceSet.A", "ForceSet.ReturnValue>IsForced.Condition", "IsForced.then>SetForced.execute",
        "GetForceB.ForceEvent>SetForced.EventId", "IsForced.else>SetRandom.execute", "RandomEvent.ReturnValue>SetRandom.EventId",
        "SetForced.then>Players.execute", "SetRandom.then>Players.execute", "Players.then>Loop.Exec", "Players.OutActors>Loop.Array",
        "Loop.LoopBody>ApplyAmmo.execute", "GetIdA.EventId>IsAmmo.A", "IsAmmo.ReturnValue>ApplyAmmo.Condition",
        "ApplyAmmo.then>FindInventory.execute", "Loop.Array Element>FindInventory.self", "FindInventory.then>AsInventory.execute",
        "FindInventory.ReturnValue>AsInventory.Object", "AsInventory.then>Refill.execute",
        "AsInventory.AsInventory Component>Refill.self",
        "ApplyAmmo.else>ApplySpeed.execute", "GetIdA.EventId>IsSpeed.A", "IsSpeed.ReturnValue>ApplySpeed.Condition",
        "ApplySpeed.then>GiveSpeed.execute", "Loop.Array Element>GiveSpeed.Target", "Self.self>GiveSpeed.Owner",
        "Loop.Completed>SayAmmo.execute", "GetIdB.EventId>SayAmmoCheck.A", "SayAmmoCheck.ReturnValue>SayAmmo.Condition",
        "SayAmmo.then>MsgAmmo.execute", "GameState.ReturnValue>MsgAmmo.self",
        "SayAmmo.else>SaySpeed.execute", "GetIdB.EventId>SaySpeedCheck.A", "SaySpeedCheck.ReturnValue>SaySpeed.Condition",
        "SaySpeed.then>MsgSpeed.execute", "GameState.ReturnValue>MsgSpeed.self",
        "MsgAmmo.then>Sentries.execute", "Sentries.then>SentryLoop.Exec", "Sentries.OutActors>SentryLoop.Array",
        "SentryLoop.LoopBody>SentryFill.execute", "SentryLoop.Array Element>SentryMax.self", "SentryMax.ReturnValue>SentryPlusOne.A", "SentryPlusOne.ReturnValue>SentryFill.AmmoCount",
        "SentryLoop.Array Element>SentryFill.self", "SentryFill.then>SentryUpdate.execute", "SentryLoop.Array Element>SentryUpdate.self",
        "SentryLoop.Completed>CallReload.execute", "CallReload.then>WaitForReload.execute", "WaitForReload.then>TopUpLoop.Exec",
        "Players.OutActors>TopUpLoop.Array", "TopUpLoop.LoopBody>TopUpFind.execute", "TopUpLoop.Array Element>TopUpFind.self",
        "TopUpFind.then>TopUpCast.execute", "TopUpFind.ReturnValue>TopUpCast.Object", "TopUpCast.then>TopUp.execute",
        "TopUpCast.AsInventory Component>TopUp.self",
        "ReloadEvent.then>WaitForRefill.execute", "WaitForRefill.then>Weapons.execute", "Weapons.then>WeaponLoop.Exec",
        "Weapons.OutActors>WeaponLoop.Array", "WeaponLoop.LoopBody>Reload.execute", "WeaponLoop.Array Element>Reload.self",
    ]:
        left, right = wire.split(">")
        src, src_pin = left.split(".", 1)
        dst, dst_pin = right.split(".", 1)
        link(src, src_pin, dst, dst_pin)


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
    lines = [f'Begin Object Class=/Script/BlueprintGraph.{node.cls} Name="{node.name}"']
    if node.body:
        lines.append(f"   {node.body}")
    lines += [f"   NodePosX={node.x}", f"   NodePosY={node.y}", f"   NodeGuid={uuid.uuid4().hex.upper()}"]
    lines += [pin_text(n, p) for n, p in node.pins.items()]
    lines.append("End Object")
    return "\n".join(lines)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    build()
    text = "\n".join(node_text(n) for n in NODES.values()) + "\n"
    with open(sys.argv[1], "w", newline="\r\n", encoding="utf-8") as f:
        f.write(text)
    links = sum(len(p["links"]) for n in NODES.values() for p in n.pins.values()) // 2
    print(f"{len(NODES)} nodes, {links} links, {len(text)} characters")


main()
