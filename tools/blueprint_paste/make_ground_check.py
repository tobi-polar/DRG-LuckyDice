"""Generate the dice's ground-check nodes as text to paste into a Blueprint graph.

Usage: python make_ground_check.py <output.txt>

Paste into the Event Graph of BP_DicePickup, which needs the variables
HoverHeight, FallSpeed, TargetZ and Falling. Then connect Event BeginPlay to
Set Timer by Event, and Event Tick to the first Branch.
"""
import sys
import uuid

VEC = "ScriptStruct'\"/Script/CoreUObject.Vector\"'"
HIT = "ScriptStruct'\"/Script/Engine.HitResult\"'"
TRACE = "Enum'\"/Script/Engine.ETraceTypeQuery\"'"
TYPES = {
    "exec": ("exec", None),
    "bool": ("bool", None),
    "float": ("float", None),
    "vector": ("struct", VEC),
    "hit": ("struct", HIT),
    "trace": ("byte", TRACE),
    "delegate": ("delegate", None),
}
MATH = "/Script/Engine.KismetMathLibrary"
SYSTEM = "/Script/Engine.KismetSystemLibrary"
STATICS = "/Script/Engine.GameplayStatics"


def guid():
    return uuid.uuid4().hex.upper()


class Node:
    def __init__(self, name, cls, x, y, body):
        self.name, self.cls, self.x, self.y, self.body = name, cls, x, y, body
        self.pins = {}

    def pin(self, name, kind, output=False, default=None):
        self.pins[name] = {"id": guid(), "kind": kind, "out": output, "default": default, "links": []}
        return self


NODES = {}


def add(node):
    NODES[node.name] = node
    return node


def call(name, x, y, function, parent=None):
    if parent:
        ref = f"FunctionReference=(MemberParent=Class'\"{parent}\"',MemberName=\"{function}\")"
    else:
        ref = f"FunctionReference=(MemberName=\"{function}\",bSelfContext=True)"
    return add(Node(name, "K2Node_CallFunction", x, y, ref))


def var_get(name, x, y, variable, kind):
    node = add(Node(name, "K2Node_VariableGet", x, y, f"VariableReference=(MemberName=\"{variable}\",bSelfContext=True)"))
    return node.pin(variable, kind, True)


def var_set(name, x, y, variable, kind, default=None):
    node = add(Node(name, "K2Node_VariableSet", x, y, f"VariableReference=(MemberName=\"{variable}\",bSelfContext=True)"))
    return node.pin("execute", "exec").pin("then", "exec", True).pin(variable, kind, False, default)


def branch(name, x, y):
    node = add(Node(name, "K2Node_IfThenElse", x, y, ""))
    return node.pin("execute", "exec").pin("Condition", "bool").pin("then", "exec", True).pin("else", "exec", True)


def link(src, src_pin, dst, dst_pin):
    a, b = NODES[src].pins[src_pin], NODES[dst].pins[dst_pin]
    if not a["out"] or b["out"]:
        raise ValueError(f"{src}.{src_pin} -> {dst}.{dst_pin} has the wrong direction")
    if a["kind"] != b["kind"]:
        raise ValueError(f"{src}.{src_pin} -> {dst}.{dst_pin} has mismatched types")
    a["links"].append((dst, b["id"]))
    b["links"].append((src, a["id"]))


def build():
    # Startup: run the ground check four times a second.
    call("Timer", 0, 0, "K2_SetTimerDelegate", SYSTEM).pin("execute", "exec").pin("then", "exec", True) \
        .pin("Delegate", "delegate").pin("Time", "float", False, "0.25").pin("bLooping", "bool", False, "true")

    # FindGround: trace straight down and remember the hover height.
    add(Node("FindGround", "K2Node_CustomEvent", 0, 300, 'CustomFunctionName="FindGround"')) \
        .pin("OutputDelegate", "delegate", True).pin("then", "exec", True)
    call("LocationA", 0, 500, "K2_GetActorLocation").pin("ReturnValue", "vector", True)
    call("TraceStart", 300, 450, "Add_VectorVector", MATH).pin("A", "vector") \
        .pin("B", "vector", False, "0, 0, 50").pin("ReturnValue", "vector", True)
    call("TraceEnd", 300, 600, "Subtract_VectorVector", MATH).pin("A", "vector") \
        .pin("B", "vector", False, "0, 0, 20000").pin("ReturnValue", "vector", True)
    call("Trace", 650, 300, "LineTraceSingle", SYSTEM).pin("execute", "exec").pin("then", "exec", True) \
        .pin("Start", "vector").pin("End", "vector").pin("TraceChannel", "trace", False, "TraceTypeQuery1") \
        .pin("bIgnoreSelf", "bool", False, "true").pin("OutHit", "hit", True).pin("ReturnValue", "bool", True)
    branch("HitGround", 1050, 300)
    call("BreakHit", 1050, 500, "BreakHitResult", STATICS).pin("Hit", "hit").pin("Location", "vector", True)
    call("BreakHitLocation", 1400, 550, "BreakVector", MATH).pin("InVec", "vector").pin("Z", "float", True)
    var_get("GetHoverHeight", 1400, 700, "HoverHeight", "float")
    call("AddHover", 1700, 600, "Add_FloatFloat", MATH).pin("A", "float").pin("B", "float").pin("ReturnValue", "float", True)
    var_set("SetTargetZ", 1950, 300, "TargetZ", "float")
    var_set("SetFallingOn", 2250, 300, "Falling", "bool", "true")

    # Every frame: move towards the target height, then stop when there.
    var_get("GetFalling", 0, 1000, "Falling", "bool")
    branch("IsFalling", 300, 900)
    call("LocationB", 0, 1200, "K2_GetActorLocation").pin("ReturnValue", "vector", True)
    call("BreakLocation", 300, 1200, "BreakVector", MATH).pin("InVec", "vector") \
        .pin("X", "float", True).pin("Y", "float", True).pin("Z", "float", True)
    var_get("GetTargetZA", 300, 1400, "TargetZ", "float")
    call("DeltaTime", 300, 1500, "GetWorldDeltaSeconds", STATICS).pin("ReturnValue", "float", True)
    var_get("GetFallSpeed", 300, 1600, "FallSpeed", "float")
    call("Interp", 650, 1350, "FInterpTo_Constant", MATH).pin("Current", "float").pin("Target", "float") \
        .pin("DeltaTime", "float").pin("InterpSpeed", "float").pin("ReturnValue", "float", True)
    call("NewLocation", 1000, 1150, "MakeVector", MATH).pin("X", "float").pin("Y", "float").pin("Z", "float") \
        .pin("ReturnValue", "vector", True)
    call("Move", 1300, 900, "K2_SetActorLocation").pin("execute", "exec").pin("then", "exec", True) \
        .pin("NewLocation", "vector")
    var_get("GetTargetZB", 1300, 1300, "TargetZ", "float")
    call("Arrived", 1600, 1200, "NearlyEqual_FloatFloat", MATH).pin("A", "float").pin("B", "float") \
        .pin("ErrorTolerance", "float", False, "1.0").pin("ReturnValue", "bool", True)
    branch("HasArrived", 1800, 900)
    var_set("SetFallingOff", 2100, 900, "Falling", "bool", "false")

    for src, src_pin, dst, dst_pin in [
        ("FindGround", "OutputDelegate", "Timer", "Delegate"),
        ("FindGround", "then", "Trace", "execute"),
        ("LocationA", "ReturnValue", "TraceStart", "A"),
        ("LocationA", "ReturnValue", "TraceEnd", "A"),
        ("TraceStart", "ReturnValue", "Trace", "Start"),
        ("TraceEnd", "ReturnValue", "Trace", "End"),
        ("Trace", "then", "HitGround", "execute"),
        ("Trace", "ReturnValue", "HitGround", "Condition"),
        ("Trace", "OutHit", "BreakHit", "Hit"),
        ("BreakHit", "Location", "BreakHitLocation", "InVec"),
        ("BreakHitLocation", "Z", "AddHover", "A"),
        ("GetHoverHeight", "HoverHeight", "AddHover", "B"),
        ("HitGround", "then", "SetTargetZ", "execute"),
        ("AddHover", "ReturnValue", "SetTargetZ", "TargetZ"),
        ("SetTargetZ", "then", "SetFallingOn", "execute"),
        ("GetFalling", "Falling", "IsFalling", "Condition"),
        ("LocationB", "ReturnValue", "BreakLocation", "InVec"),
        ("BreakLocation", "Z", "Interp", "Current"),
        ("GetTargetZA", "TargetZ", "Interp", "Target"),
        ("DeltaTime", "ReturnValue", "Interp", "DeltaTime"),
        ("GetFallSpeed", "FallSpeed", "Interp", "InterpSpeed"),
        ("BreakLocation", "X", "NewLocation", "X"),
        ("BreakLocation", "Y", "NewLocation", "Y"),
        ("Interp", "ReturnValue", "NewLocation", "Z"),
        ("IsFalling", "then", "Move", "execute"),
        ("NewLocation", "ReturnValue", "Move", "NewLocation"),
        ("Move", "then", "HasArrived", "execute"),
        ("BreakLocation", "Z", "Arrived", "A"),
        ("GetTargetZB", "TargetZ", "Arrived", "B"),
        ("Arrived", "ReturnValue", "HasArrived", "Condition"),
        ("HasArrived", "then", "SetFallingOff", "execute"),
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
    lines += [f"   NodePosX={node.x}", f"   NodePosY={node.y}", f"   NodeGuid={guid()}"]
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
