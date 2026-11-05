"""Generate the dice's vacuum pickup as text to paste into a Blueprint graph.

Usage: python make_vacuum.py <output.txt>

Paste into the Event Graph of BP_DicePickup, which needs the variables
FlyTarget (Player Character reference, Replicated), FlySpeed and FlightTime.

FlyTarget replicates, so each player's game flies the dice itself. PickedUp is
only ever true on the host, so only the host rolls and destroys the dice.
"""
import sys
import uuid

VEC = "ScriptStruct'\"/Script/CoreUObject.Vector\"'"
PLAYER = "Class'\"/Script/FSD.PlayerCharacter\"'"
OBJECT = "Class'\"/Script/CoreUObject.Object\"'"
ACTOR = "Class'\"/Script/Engine.Actor\"'"
TYPES = {
    "exec": ("exec", None),
    "bool": ("bool", None),
    "float": ("float", None),
    "vector": ("struct", VEC),
    "player": ("object", PLAYER),
    "object": ("object", OBJECT),
    "actor": ("object", ACTOR),
}
OBJECT_KINDS = {"player", "object", "actor"}
MATH = "/Script/Engine.KismetMathLibrary"
SYSTEM = "/Script/Engine.KismetSystemLibrary"
STATICS = "/Script/Engine.GameplayStatics"
MANAGER = "BlueprintGeneratedClass'\"/Game/LuckyDice/BP_DiceManager.BP_DiceManager_C\"'"

NODES = {}


class Node:
    def __init__(self, name, cls, x, y, body=""):
        self.name, self.cls, self.x, self.y, self.body = name, cls, x, y, body
        self.pins = {}
        NODES[name] = self

    def pin(self, name, kind, output=False, default=None):
        self.pins[name] = {"id": uuid.uuid4().hex.upper(), "kind": kind, "out": output, "default": default, "links": []}
        return self


def call(name, x, y, function, parent=None):
    if parent:
        ref = f"FunctionReference=(MemberParent=Class'\"{parent}\"',MemberName=\"{function}\")"
    else:
        ref = f"FunctionReference=(MemberName=\"{function}\",bSelfContext=True)"
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


def pure2(name, x, y, function, kind="float", result="float", b_default=None):
    return call(name, x, y, function, MATH).pin("A", kind).pin("B", kind, False, b_default).pin("ReturnValue", result, True)


def link(src, src_pin, dst, dst_pin):
    a, b = NODES[src].pins[src_pin], NODES[dst].pins[dst_pin]
    if not a["out"] or b["out"]:
        raise ValueError(f"{src}.{src_pin} -> {dst}.{dst_pin} has the wrong direction")
    if a["kind"] != b["kind"] and not (a["kind"] in OBJECT_KINDS and b["kind"] in OBJECT_KINDS):
        raise ValueError(f"{src}.{src_pin} -> {dst}.{dst_pin} has mismatched types")
    a["links"].append((dst, b["id"]))
    b["links"].append((src, a["id"]))


def build():
    # Replaces Roll Dice and Destroy Actor at the end of the overlap chain.
    var_set("SetFlyTarget", 0, 0, "FlyTarget", "player")

    # Every frame, ahead of the hover logic.
    branch("IsFlying", 0, 250)
    var_get("GetFlyTarget", -300, 350, "FlyTarget", "player")
    call("TargetValid", 0, 400, "IsValid", SYSTEM).pin("Object", "object").pin("ReturnValue", "bool", True)

    # The dice lost its target, such as the player leaving: resolve it anyway.
    branch("TargetLost", 300, 500)
    var_get("GetPickedUpA", 0, 600, "PickedUp", "bool")

    # Fly towards the player, speeding up the longer it takes.
    call("Here", 300, 700, "K2_GetActorLocation").pin("ReturnValue", "vector", True)
    call("There", 300, 800, "K2_GetActorLocation").pin("self", "actor").pin("ReturnValue", "vector", True)
    call("DeltaA", 300, 900, "GetWorldDeltaSeconds", STATICS).pin("ReturnValue", "float", True)
    var_get("GetFlightTimeA", 0, 1050, "FlightTime", "float")
    pure2("Boost", 300, 1050, "Multiply_FloatFloat", b_default="3000")
    var_get("GetFlySpeed", 300, 1200, "FlySpeed", "float")
    pure2("Speed", 600, 1100, "Add_FloatFloat")
    call("Step", 850, 800, "VInterpTo_Constant", MATH).pin("Current", "vector").pin("Target", "vector") \
        .pin("DeltaTime", "float").pin("InterpSpeed", "float").pin("ReturnValue", "vector", True)
    call("Fly", 1200, 250, "K2_SetActorLocation").pin("execute", "exec").pin("then", "exec", True) \
        .pin("NewLocation", "vector")

    # Keep count of the flight time.
    var_get("GetFlightTimeB", 1200, 500, "FlightTime", "float")
    call("DeltaB", 1200, 600, "GetWorldDeltaSeconds", STATICS).pin("ReturnValue", "float", True)
    pure2("NextTime", 1500, 500, "Add_FloatFloat")
    var_set("SetFlightTime", 1600, 250, "FlightTime", "float")

    # Arrived, or two seconds have passed. Only the host has PickedUp set.
    call("Distance", 1500, 700, "GetDistanceTo").pin("OtherActor", "actor").pin("ReturnValue", "float", True)
    pure2("Close", 1800, 700, "Less_FloatFloat", result="bool", b_default="100")
    var_get("GetFlightTimeC", 1500, 850, "FlightTime", "float")
    pure2("TimedOut", 1800, 850, "GreaterEqual_FloatFloat", result="bool", b_default="2")
    pure2("Done", 2050, 750, "BooleanOR", "bool", "bool")
    var_get("GetPickedUpB", 2050, 600, "PickedUp", "bool")
    pure2("HostDone", 2300, 650, "BooleanAND", "bool", "bool")
    branch("Finish", 2300, 250)

    # Fire the event and remove the dice.
    var_get("GetManager", 2550, 500, "Manager", "object")
    Node("Roll", "K2Node_CallFunction", 2550, 250,
         f"FunctionReference=(MemberParent={MANAGER},MemberName=\"RollDice\")") \
        .pin("execute", "exec").pin("then", "exec", True).pin("self", "object").pin("Picker", "player")
    call("Destroy", 2900, 250, "K2_DestroyActor").pin("execute", "exec")

    for src, src_pin, dst, dst_pin in [
        ("GetFlyTarget", "FlyTarget", "TargetValid", "Object"),
        ("TargetValid", "ReturnValue", "IsFlying", "Condition"),
        ("IsFlying", "else", "TargetLost", "execute"),
        ("GetPickedUpA", "PickedUp", "TargetLost", "Condition"),
        ("TargetLost", "then", "Roll", "execute"),
        ("IsFlying", "then", "Fly", "execute"),
        ("Here", "ReturnValue", "Step", "Current"),
        ("GetFlyTarget", "FlyTarget", "There", "self"),
        ("There", "ReturnValue", "Step", "Target"),
        ("DeltaA", "ReturnValue", "Step", "DeltaTime"),
        ("GetFlightTimeA", "FlightTime", "Boost", "A"),
        ("Boost", "ReturnValue", "Speed", "A"),
        ("GetFlySpeed", "FlySpeed", "Speed", "B"),
        ("Speed", "ReturnValue", "Step", "InterpSpeed"),
        ("Step", "ReturnValue", "Fly", "NewLocation"),
        ("Fly", "then", "SetFlightTime", "execute"),
        ("GetFlightTimeB", "FlightTime", "NextTime", "A"),
        ("DeltaB", "ReturnValue", "NextTime", "B"),
        ("NextTime", "ReturnValue", "SetFlightTime", "FlightTime"),
        ("SetFlightTime", "then", "Finish", "execute"),
        ("GetFlyTarget", "FlyTarget", "Distance", "OtherActor"),
        ("Distance", "ReturnValue", "Close", "A"),
        ("GetFlightTimeC", "FlightTime", "TimedOut", "A"),
        ("Close", "ReturnValue", "Done", "A"),
        ("TimedOut", "ReturnValue", "Done", "B"),
        ("GetPickedUpB", "PickedUp", "HostDone", "A"),
        ("Done", "ReturnValue", "HostDone", "B"),
        ("HostDone", "ReturnValue", "Finish", "Condition"),
        ("Finish", "then", "Roll", "execute"),
        ("GetManager", "Manager", "Roll", "self"),
        ("GetFlyTarget", "FlyTarget", "Roll", "Picker"),
        ("Roll", "then", "Destroy", "execute"),
    ]:
        link(src, src_pin, dst, dst_pin)


def pin_text(name, pin):
    category, sub_object = TYPES[pin["kind"]]
    parts = [f"PinId={pin['id']}", f'PinName="{name}"']
    if pin["out"]:
        parts.append('Direction="EGPD_Output"')
    parts.append(f'PinType.PinCategory="{category}"')
    if sub_object:
        parts.append(f"PinType.PinSubCategoryObject={sub_object}")
    if pin["default"] is not None:
        parts.append(f'DefaultValue="{pin["default"]}"')
    if pin["links"]:
        linked = ",".join(f"{node} {pid}" for node, pid in pin["links"]) + ","
        parts.append(f"LinkedTo=({linked})")
    return "   CustomProperties Pin (" + ",".join(parts) + ",)"


def node_text(node):
    lines = [f'Begin Object Class=/Script/BlueprintGraph.{node.cls} Name="{node.name}"']
    if node.body:
        lines.append(f"   {node.body}")
    lines += [f"   NodePosX={node.x}", f"   NodePosY={node.y}", f"   NodeGuid={uuid.uuid4().hex.upper()}"]
    lines += [pin_text(name, pin) for name, pin in node.pins.items()]
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
