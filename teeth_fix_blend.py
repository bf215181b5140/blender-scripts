"""
Blend the teeth/braces/tongue correction into individual shape keys.

Open this in Blender's Text Editor (Scripting tab) and press Run Script.
Edit the CALLS section at the bottom, then run again. Save the .blend afterwards.

  blend 0.0 = the key keeps its old teeth pose exactly (how it is now)
  blend 1.0 = the key's teeth get the full "Teeth_closed_fix_3" correction on top

"""
import bpy, json, numpy as np

OBJ = "Body"


def _ctx():
    ob = bpy.data.objects[OBJ]
    if ob.mode != "OBJECT":
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.mode_set(mode="OBJECT")
        print("(switched Body out of Edit Mode - shape key edits are discarded otherwise)")
    me = ob.data
    n = len(me.vertices)
    kbs = me.shape_keys.key_blocks

    def get(name):
        a = np.empty(n * 3)
        kbs[name].data.foreach_get("co", a)
        return a.reshape(n, 3)

    D = get("Basis") - get(me["teeth_fix_revert_key"])       # the correction vector
    sid = np.array(me["teeth_fix_shell_id"])
    labels = me["teeth_fix_shell_labels"].split(",")
    state = json.loads(me["teeth_fix_state"])
    return ob, me, n, kbs, D, sid, labels, state, get


def _blend_dict(entry):
    b = entry.get("blend", 0.0)
    if not isinstance(b, dict):
        b = {str(j): float(b) for j in entry["held"]}
        entry["blend"] = b
    return b


def list_keys(contains=""):
    """Print every key that holds its own teeth pose, and its current blend."""
    _, _, _, _, _, _, labels, state, _ = _ctx()
    rows = [(nm, e) for nm, e in sorted(state.items()) if contains.lower() in nm.lower()]
    print("%-38s %-9s %s" % ("shape key", "blend", "shells it poses"))
    for nm, e in rows:
        b = _blend_dict(e)
        vals = sorted({round(v, 3) for v in b.values()})
        grp = sorted({labels[j] for j in e["held"]})
        print("%-38s %-9s %s" % (nm, ",".join(str(v) for v in vals), " ".join(grp)))
    print("(%d keys)" % len(rows))


def set_blend(name, t, shells=None):
    """Set how much of the correction `name` receives. shells: substring or list."""
    ob, me, n, kbs, D, sid, labels, state, get = _ctx()
    if name not in state:
        print("!! %r does not pose teeth/braces/tongue - it already has the full fix" % name)
        return
    entry = state[name]
    b = _blend_dict(entry)
    if shells is None:
        want = list(entry["held"])
    else:
        pats = [shells] if isinstance(shells, str) else list(shells)
        want = [j for j in entry["held"] if any(p.lower() in labels[j].lower() for p in pats)]
        if not want:
            print("!! %r poses none of %s" % (name, shells))
            return
    t = float(max(0.0, min(1.0, t)))
    co = get(name)
    moved = 0
    for j in want:
        prev = float(b.get(str(j), 0.0))
        if abs(t - prev) < 1e-12:
            continue
        v = np.where(sid == j)[0]
        co[v] += (t - prev) * D[v]
        b[str(j)] = t
        moved += len(v)
    kbs[name].data.foreach_set("co", co.reshape(-1))
    me["teeth_fix_state"] = json.dumps(state, ensure_ascii=False)
    print("%-34s blend -> %.2f  (%s, %d verts)" %
          (name, t, " ".join(sorted({labels[j] for j in want})), moved))


# ============================ CALLS ==========================================
list_keys("mouth_wide")

# set_blend("mouth_wide", 0.5)
# set_blend("mouth_wide", 1.0, shells="teeth_LOWER")
# set_blend("vrc.v_aa", 0.35)
