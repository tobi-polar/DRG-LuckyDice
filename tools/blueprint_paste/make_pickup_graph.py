"""Generate BP_DicePickup's whole Event Graph as text to paste.

Usage: python make_pickup_graph.py <output.txt>

Delete everything in the Event Graph, compile, then paste. The Blueprint needs
the Sphere component and the variables Manager, PickedUp, HoverHeight, FallSpeed,
TargetZ, Falling, FlyTarget (Replicated), FlySpeed and FlightTime.
"""
import sys
import uuid

VEC = "ScriptStruct'\"/Script/CoreUObject.Vector\"'"
HIT = "ScriptStruct'\"/Script/Engine.HitResult\"'"
TRACE = "Enum'\"/Script/Engine.ETraceTypeQuery\"'"
PLAYER = "Class'\"/Script/FSD.PlayerCharacter\"'"
OBJECT = "Class'\"/Script/CoreUObject.Object\"'"
ACTOR = "Class'\"/Script/Engine.Actor\"'"
TYPES = {
    "exec": ("exec", None), "bool": ("bool", None), "float": ("float", None),
    "vector": ("struct", VEC), "hit": ("struct", HIT), "trace": ("byte", TRACE),
    "delegate": ("delegate", None), "player": ("object", PLAYER),
    "object": ("object", OBJECT), "actor": ("object", ACTOR),
}
OBJECTS = {"player", "object", "actor"}
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


def var_set(name, x, y, variable, kind, default=None):
    ref = f"VariableReference=(MemberName=\"{variable}\",bSelfContext=True)"
    return Node(name, "K2Node_VariableSet", x, y, ref).pin("execute", "exec").pin("then", "exec", True) \
        .pin(variable, kind, False, default)


def branch(name, x, y):
    return Node(name, "K2Node_IfThenElse", x, y).pin("execute", "exec").pin("Condition", "bool") \
        .pin("then", "exec", True).pin("else", "exec", True)


def event(name, x, y, member):
    body = f"EventReference=(MemberParent=Class'\"/Script/Engine.Actor\"',MemberName=\"{member}\")\n   bOverrideFunction=True"
    return Node(name, "K2Node_Event", x, y, body).pin("then", "exec", True)


def pure2(name, x, y, function, kind="float", result="float", b_default=None):
    return call(name, x, y, function, MATH).pin("A", kind).pin("B", kind, False, b_default).pin("ReturnValue", result, True)


def link(src, src_pin, dst, dst_pin):
    a, b = NODES[src].pins[src_pin], NODES[dst].pins[dst_pin]
    if not a["out"] or b["out"]:
        raise ValueError(f"{src}.{src_pin} -> {dst}.{dst_pin} has the wrong direction")
    if a["kind"] != b["kind"] and not (a["kind"] in OBJECTS and b["kind"] in OBJECTS):
        raise ValueError(f"{src}.{src_pin} -> {dst}.{dst_pin} has mismatched types")
    a["links"].append((dst, b["id"]))
    b["links"].append((src, a["id"]))


def build():
    # Pickup: lock the dice to the first player in range, on the host only.
    Node("Overlap", "K2Node_ComponentBoundEvent", 0, 0,
         'ComponentPropertyName="Sphere"\n   DelegatePropertyName="OnComponentBeginOverlap"\n'
         "   DelegateOwnerClass=Class'\"/Script/Engine.PrimitiveComponent\"'\n"
         "   EventReference=(MemberParent=Package'\"/Script/Engine\"',MemberName=\"ComponentBeginOverlapSignature__DelegateSignature\")\n"
         '   bInternalEvent=True\n   CustomFunctionName="BndEvt__Sphere_K2Node_ComponentBoundEvent_0_ComponentBeginOverlapSignature__DelegateSignature"') \
        .pin("then", "exec", True).pin("OtherActor", "actor", True)
    call("HasAuthority", 300, 150, "HasAuthority").pin("ReturnValue", "bool", True)
    branch("OnHost", 350, 0)
    Node("Cast", "K2Node_DynamicCast", 650, 0, f"TargetType={PLAYER}").pin("execute", "exec").pin("then", "exec", True) \
        .pin("CastFailed", "exec", True).pin("Object", "actor").pin("AsPlayer Character", "player", True).pin("bSuccess", "bool", True)
    var_get("GetPickedUpNew", 750, 250, "PickedUp", "bool")
    call("NotPicked", 1000, 250, "Not_PreBool", MATH).pin("A", "bool").pin("ReturnValue", "bool", True)
    branch("FirstPickup", 1050, 0)
    var_set("SetPickedUp", 1350, 0, "PickedUp", "bool", "true")
    var_set("SetFlyTarget", 1650, 0, "FlyTarget", "player")

    # Startup: check for the ground four times a second.
    event("BeginPlay", 0, 450, "ReceiveBeginPlay")
    call("Timer", 300, 450, "K2_SetTimerDelegate", SYSTEM).pin("execute", "exec").pin("then", "exec", True) \
        .pin("Delegate", "delegate").pin("Time", "float", False, "0.25").pin("bLooping", "bool", False, "true")

    # FindGround: trace down and remember the hover height.
    Node("FindGround", "K2Node_CustomEvent", 0, 750, 'CustomFunctionName="FindGround"') \
        .pin("OutputDelegate", "delegate", True).pin("then", "exec", True)
    call("LocationA", 0, 950, "K2_GetActorLocation").pin("ReturnValue", "vector", True)
    call("TraceStart", 300, 900, "Add_VectorVector", MATH).pin("A", "vector") \
        .pin("B", "vector", False, "0, 0, 50").pin("ReturnValue", "vector", True)
    call("TraceEnd", 300, 1050, "Subtract_VectorVector", MATH).pin("A", "vector") \
        .pin("B", "vector", False, "0, 0, 20000").pin("ReturnValue", "vector", True)
    call("Trace", 650, 750, "LineTraceSingle", SYSTEM).pin("execute", "exec").pin("then", "exec", True) \
        .pin("Start", "vector").pin("End", "vector").pin("TraceChannel", "trace", False, "TraceTypeQuery1") \
        .pin("bIgnoreSelf", "bool", False, "true").pin("OutHit", "hit", True).pin("ReturnValue", "bool", True)
    branch("HitGround", 1050, 750)
    call("BreakHit", 1050, 950, "BreakHitResult", STATICS).pin("Hit", "hit").pin("Location", "vector", True)
    call("BreakHitLocation", 1400, 1000, "BreakVector", MATH).pin("InVec", "vector").pin("Z", "float", True)
    var_get("GetHoverHeight", 1400, 1150, "HoverHeight", "float")
    pure2("AddHover", 1700, 1050, "Add_FloatFloat")
    var_set("SetTargetZ", 1950, 750, "TargetZ", "float")
    var_set("SetFallingOn", 2250, 750, "Falling", "bool", "true")

    # Every frame: fly to the player if locked on, otherwise hover.
    event("Tick", 0, 1450, "ReceiveTick")
    branch("IsFlying", 300, 1450)
    var_get("GetFlyTarget", 0, 1600, "FlyTarget", "player")
    call("TargetValid", 300, 1650, "IsValid", SYSTEM).pin("Object", "object").pin("ReturnValue", "bool", True)
    branch("TargetLost", 650, 1700)
    var_get("GetPickedUpA", 350, 1800, "PickedUp", "bool")

    call("Here", 300, 1950, "K2_GetActorLocation").pin("ReturnValue", "vector", True)
    call("There", 300, 2050, "K2_GetActorLocation").pin("self", "actor").pin("ReturnValue", "vector", True)
    call("DeltaA", 300, 2150, "GetWorldDeltaSeconds", STATICS).pin("ReturnValue", "float", True)
    var_get("GetFlightTimeA", 0, 2300, "FlightTime", "float")
    pure2("Boost", 300, 2300, "Multiply_FloatFloat", b_default="3000")
    var_get("GetFlySpeed", 300, 2450, "FlySpeed", "float")
    pure2("Speed", 600, 2350, "Add_FloatFloat")
    call("Step", 850, 2050, "VInterpTo_Constant", MATH).pin("Current", "vector").pin("Target", "vector") \
        .pin("DeltaTime", "float").pin("InterpSpeed", "float").pin("ReturnValue", "vector", True)
    call("Fly", 1200, 1450, "K2_SetActorLocation").pin("execute", "exec").pin("then", "exec", True).pin("NewLocation", "vector")
    var_get("GetFlightTimeB", 1200, 1700, "FlightTime", "float")
    call("DeltaB", 1200, 1800, "GetWorldDeltaSeconds", STATICS).pin("ReturnValue", "float", True)
    pure2("NextTime", 1500, 1700, "Add_FloatFloat")
    var_set("SetFlightTime", 1600, 1450, "FlightTime", "float")
    call("Distance", 1500, 1900, "GetDistanceTo").pin("OtherActor", "actor").pin("ReturnValue", "float", True)
    pure2("Close", 1800, 1900, "Less_FloatFloat", result="bool", b_default="100")
    var_get("GetFlightTimeC", 1500, 2050, "FlightTime", "float")
    pure2("TimedOut", 1800, 2050, "GreaterEqual_FloatFloat", result="bool", b_default="2")
    pure2("Done", 2050, 1950, "BooleanOR", "bool", "bool")
    var_get("GetPickedUpB", 2050, 1800, "PickedUp", "bool")
    pure2("HostDone", 2300, 1850, "BooleanAND", "bool", "bool")
    branch("Finish", 2300, 1450)
    var_get("GetManager", 2550, 1700, "Manager", "object")
    Node("Roll", "K2Node_CallFunction", 2550, 1450, f"FunctionReference=(MemberParent={MANAGER},MemberName=\"RollDice\")") \
        .pin("execute", "exec").pin("then", "exec", True).pin("self", "object").pin("Picker", "player")
    call("Destroy", 2900, 1450, "K2_DestroyActor").pin("execute", "exec")

    # Hover: move towards the height found by FindGround.
    branch("IsFalling", 1000, 2700)
    var_get("GetFalling", 700, 2800, "Falling", "bool")
    call("LocationB", 0, 3000, "K2_GetActorLocation").pin("ReturnValue", "vector", True)
    call("BreakLocation", 300, 3000, "BreakVector", MATH).pin("InVec", "vector") \
        .pin("X", "float", True).pin("Y", "float", True).pin("Z", "float", True)
    var_get("GetTargetZA", 300, 3200, "TargetZ", "float")
    call("DeltaC", 300, 3300, "GetWorldDeltaSeconds", STATICS).pin("ReturnValue", "float", True)
    var_get("GetFallSpeed", 300, 3400, "FallSpeed", "float")
    call("Interp", 650, 3150, "FInterpTo_Constant", MATH).pin("Current", "float").pin("Target", "float") \
        .pin("DeltaTime", "float").pin("InterpSpeed", "float").pin("ReturnValue", "float", True)
    call("NewLocation", 1000, 2950, "MakeVector", MATH).pin("X", "float").pin("Y", "float").pin("Z", "float") \
        .pin("ReturnValue", "vector", True)
    call("Move", 1300, 2700, "K2_SetActorLocation").pin("execute", "exec").pin("then", "exec", True).pin("NewLocation", "vector")
    var_get("GetTargetZB", 1300, 3100, "TargetZ", "float")
    call("Arrived", 1600, 3000, "NearlyEqual_FloatFloat", MATH).pin("A", "float").pin("B", "float") \
        .pin("ErrorTolerance", "float", False, "1.0").pin("ReturnValue", "bool", True)
    branch("HasArrived", 1800, 2700)
    var_set("SetFallingOff", 2100, 2700, "Falling", "bool", "false")

    for wire in [
        "Overlap.then>OnHost.execute", "HasAuthority.ReturnValue>OnHost.Condition", "OnHost.then>Cast.execute",
        "Overlap.OtherActor>Cast.Object", "Cast.then>FirstPickup.execute", "GetPickedUpNew.PickedUp>NotPicked.A",
        "NotPicked.ReturnValue>FirstPickup.Condition", "FirstPickup.then>SetPickedUp.execute",
        "SetPickedUp.then>SetFlyTarget.execute", "Cast.AsPlayer Character>SetFlyTarget.FlyTarget",
        "BeginPlay.then>Timer.execute", "FindGround.OutputDelegate>Timer.Delegate", "FindGround.then>Trace.execute",
        "LocationA.ReturnValue>TraceStart.A", "LocationA.ReturnValue>TraceEnd.A", "TraceStart.ReturnValue>Trace.Start",
        "TraceEnd.ReturnValue>Trace.End", "Trace.then>HitGround.execute", "Trace.ReturnValue>HitGround.Condition",
        "Trace.OutHit>BreakHit.Hit", "BreakHit.Location>BreakHitLocation.InVec", "BreakHitLocation.Z>AddHover.A",
        "GetHoverHeight.HoverHeight>AddHover.B", "HitGround.then>SetTargetZ.execute",
        "AddHover.ReturnValue>SetTargetZ.TargetZ", "SetTargetZ.then>SetFallingOn.execute",
        "Tick.then>IsFlying.execute", "GetFlyTarget.FlyTarget>TargetValid.Object",
        "TargetValid.ReturnValue>IsFlying.Condition", "IsFlying.else>TargetLost.execute",
        "GetPickedUpA.PickedUp>TargetLost.Condition", "TargetLost.then>Roll.execute", "TargetLost.else>IsFalling.execute",
        "IsFlying.then>Fly.execute", "Here.ReturnValue>Step.Current", "GetFlyTarget.FlyTarget>There.self",
        "There.ReturnValue>Step.Target", "DeltaA.ReturnValue>Step.DeltaTime", "GetFlightTimeA.FlightTime>Boost.A",
        "Boost.ReturnValue>Speed.A", "GetFlySpeed.FlySpeed>Speed.B", "Speed.ReturnValue>Step.InterpSpeed",
        "Step.ReturnValue>Fly.NewLocation", "Fly.then>SetFlightTime.execute", "GetFlightTimeB.FlightTime>NextTime.A",
        "DeltaB.ReturnValue>NextTime.B", "NextTime.ReturnValue>SetFlightTime.FlightTime", "SetFlightTime.then>Finish.execute",
        "GetFlyTarget.FlyTarget>Distance.OtherActor", "Distance.ReturnValue>Close.A", "GetFlightTimeC.FlightTime>TimedOut.A",
        "Close.ReturnValue>Done.A", "TimedOut.ReturnValue>Done.B", "GetPickedUpB.PickedUp>HostDone.A",
        "Done.ReturnValue>HostDone.B", "HostDone.ReturnValue>Finish.Condition", "Finish.then>Roll.execute",
        "GetManager.Manager>Roll.self", "GetFlyTarget.FlyTarget>Roll.Picker", "Roll.then>Destroy.execute",
        "GetFalling.Falling>IsFalling.Condition", "LocationB.ReturnValue>BreakLocation.InVec", "BreakLocation.Z>Interp.Current",
        "GetTargetZA.TargetZ>Interp.Target", "DeltaC.ReturnValue>Interp.DeltaTime", "GetFallSpeed.FallSpeed>Interp.InterpSpeed",
        "BreakLocation.X>NewLocation.X", "BreakLocation.Y>NewLocation.Y", "Interp.ReturnValue>NewLocation.Z",
        "IsFalling.then>Move.execute", "NewLocation.ReturnValue>Move.NewLocation", "Move.then>HasArrived.execute",
        "BreakLocation.Z>Arrived.A", "GetTargetZB.TargetZ>Arrived.B", "Arrived.ReturnValue>HasArrived.Condition",
        "HasArrived.then>SetFallingOff.execute",
    ]:
        left, right = wire.split(">")
        src, src_pin = left.split(".", 1)
        dst, dst_pin = right.split(".", 1)
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
