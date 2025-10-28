bl_info = {
    "name": "OVITO → Blender Visualizer",
    "author": "Aaron Cuevas + Technical Arts",
    "version": (0, 1, 0),
    "blender": (3, 6, 0),
    "location": "3D Viewport > N-Panel > SciViz",
    "description": "Real-time playback of LAMMPS/OVITO dumps, Geometry Nodes instancing, per-atom scale, and Alembic export for deterministic renders.",
    "warning": "",
    "category": "Import-Export",
}

import os
import re
import bpy
from bpy.props import (
    StringProperty,
    PointerProperty,
    FloatProperty,
    IntProperty,
    BoolProperty,
)
from bpy.types import Operator, Panel, AddonPreferences, PropertyGroup
from bpy.app.handlers import persistent

# --------------------------------------------------------------------------------------
# Global state (lifetime = Blender session)
# --------------------------------------------------------------------------------------
_OVB = {
    "frames": {},        # {frame_number: [(x,y,z), ...]}
    "frame_keys": [],    # sorted list of frame numbers
    "carrier": None,     # object that holds the vertices
    "handler_added": False,
    "nodegroup_name": "GN_AtomsInstance",
    "modifier_name": "GN_AtomsInstance",
}

# --------------------------------------------------------------------------------------
# Utilities
# --------------------------------------------------------------------------------------
def _msg(info):
    print(f"[OVB] {info}")

def _ensure_collection(context):
    coll = context.scene.collection
    return coll

def _create_or_get_carrier(name="AtomInstancer", mesh_name="AtomInstancer_Mesh"):
    me = bpy.data.meshes.get(mesh_name) or bpy.data.meshes.new(mesh_name)
    obj = bpy.data.objects.get(name)
    if obj is None:
        obj = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(obj)
    else:
        obj.data = me
    return obj

def _build_vertices(obj, coords):
    me = obj.data
    me.clear_geometry()
    me.from_pydata(coords if coords else [(0, 0, 0)], [], [])
    me.update()

def _parse_dump(filepath):
    """
    Minimal LAMMPS/OVITO dump parser.
    Supports x y z or xs ys zs with BOX BOUNDS (orthogonal).
    Returns: frames dict and sorted keys.
    """
    assert os.path.exists(filepath), f"File not found: {filepath}"
    positions = {}
    frame_keys = []
    with open(filepath, "r") as f:
        lines = f.readlines()

    i = 0
    n = len(lines)
    while i < n:
        if lines[i].startswith("ITEM: TIMESTEP"):
            step = int(lines[i + 1].strip())
            frame_keys.append(step)
            i += 2

            if not lines[i].startswith("ITEM: NUMBER OF ATOMS"):
                raise ValueError("Expected: ITEM: NUMBER OF ATOMS")
            num_atoms = int(lines[i + 1].strip())
            i += 2

            # BOX BOUNDS (3 lines)
            if not lines[i].startswith("ITEM: BOX BOUNDS"):
                raise ValueError("Expected: ITEM: BOX BOUNDS")
            xlo, xhi = map(float, lines[i + 1].split()[:2])
            ylo, yhi = map(float, lines[i + 2].split()[:2])
            zlo, zhi = map(float, lines[i + 3].split()[:2])
            i += 4

            if not lines[i].startswith("ITEM: ATOMS"):
                raise ValueError("Expected: ITEM: ATOMS")
            header = lines[i].split()[2:]
            i += 1

            use_scaled = all(k in header for k in ("xs", "ys", "zs"))
            if use_scaled:
                ix, iy, iz = header.index("xs"), header.index("ys"), header.index("zs")
            else:
                assert all(k in header for k in ("x", "y", "z")), "Header must contain x y z or xs ys zs"
                ix, iy, iz = header.index("x"), header.index("y"), header.index("z")

            coords = []
            for _ in range(num_atoms):
                cols = lines[i].split()
                x, y, z = float(cols[ix]), float(cols[iy]), float(cols[iz])
                if use_scaled:
                    x = x * (xhi - xlo) + xlo
                    y = y * (yhi - ylo) + ylo
                    z = z * (zhi - zlo) + zlo
                coords.append((x, y, z))
                i += 1

            positions[step] = coords
        else:
            i += 1

    frame_keys.sort()
    return positions, frame_keys

def _ensure_gn_instancing(inst_obj, proto_obj, ng_name, mod_name, atom_scale):
    """
    Build a clean Geometry Nodes graph:
    Group Input(Geometry) → Mesh to Points(radius=0) → Instance on Points(Instance=proto)
    → Realize Instances (optional off) → Group Output(Geometry)
    Adds a Float input 'AtomScale' that multiplies the prototype scale.
    """
    mod = inst_obj.modifiers.get(mod_name) or inst_obj.modifiers.new(mod_name, "NODES")
    ng = mod.node_group or bpy.data.node_groups.get(ng_name) or bpy.data.node_groups.new(ng_name, "GeometryNodeTree")
    mod.node_group = ng

    ng.nodes.clear()
    ng.links.clear()

    # IO sockets
    if "Geometry" not in [s.name for s in ng.inputs]:
        ng.inputs.new("NodeSocketGeometry", "Geometry")
    if "AtomScale" not in [s.name for s in ng.inputs]:
        s = ng.inputs.new("NodeSocketFloat", "AtomScale")
        s.default_value = float(atom_scale)
        s.min_value = 0.0
    if "Geometry" not in [s.name for s in ng.outputs]:
        ng.outputs.new("NodeSocketGeometry", "Geometry")

    n_in = ng.nodes.new("NodeGroupInput")
    n_out = ng.nodes.new("NodeGroupOutput")
    n_mesh2pts = ng.nodes.new("GeometryNodeMeshToPoints")
    n_mesh2pts.inputs["Radius"].default_value = 0.0
    n_inst = ng.nodes.new("GeometryNodeInstanceOnPoints")
    n_obj = ng.nodes.new("GeometryNodeObjectInfo")
    n_obj.inputs["Object"].default_value = proto_obj
    if hasattr(n_obj, "as_instance"):
        n_obj.as_instance = True

    # Optional: scale instances via node
    n_scale = ng.nodes.new("GeometryNodeTransform")
    n_scale.inputs["Scale"].default_value[0] = atom_scale
    n_scale.inputs["Scale"].default_value[1] = atom_scale
    n_scale.inputs["Scale"].default_value[2] = atom_scale

    # Links
    ng.links.new(n_in.outputs["Geometry"], n_mesh2pts.inputs["Mesh"])
    ng.links.new(n_mesh2pts.outputs["Points"], n_inst.inputs["Points"])
    ng.links.new(n_obj.outputs["Geometry"], n_scale.inputs["Geometry"])
    ng.links.new(n_scale.outputs["Geometry"], n_inst.inputs["Instance"])
    ng.links.new(n_inst.outputs["Instances"], n_out.inputs["Geometry"])

    # Expose AtomScale to Transform node (x=y=z)
    # Blender 3.6 does not support direct group input link to vector components; set via driver:
    for axis in range(3):
        drv = n_scale.inputs["Scale"].driver_add("default_value", axis).driver
        drv.type = 'SCRIPTED'
        var = drv.variables.new()
        var.name = "s"
        var.targets[0].id_type = 'NODETREE'
        var.targets[0].id = ng
        var.targets[0].data_path = f'inputs[1].default_value'  # AtomScale index = 1 (Geometry is 0)
        drv.expression = "s"

    # Modifier input default
    # Find "AtomScale" index safely
    for i, inp in enumerate(mod.node_group.inputs):
        if inp.name == "AtomScale":
            try:
                mod["Input_%d" % i] = atom_scale
            except Exception:
                pass
            break

    # Disable legacy dupli-verts
    inst_obj.instance_type = 'NONE'

def _set_meshcache_first_then_gn(inst_obj, gn_name):
    deps = inst_obj.modifiers
    mc = next((m for m in deps if m.type == 'MESH_CACHE'), None)
    gn = inst_obj.modifiers.get(gn_name)
    if not gn:
        return
    if mc:
        # Move Mesh Cache above GN; leave GN at the end
        while deps.find(mc.name) > deps.find(gn.name):
            bpy.ops.object.modifier_move_up(modifier=mc.name)
        for _ in range(64):
            if deps.find(gn.name) == len(deps) - 1:
                break
            bpy.ops.object.modifier_move_down(modifier=gn.name)

# --------------------------------------------------------------------------------------
# Properties
# --------------------------------------------------------------------------------------
class OVB_Props(PropertyGroup):
    dump_path: StringProperty(
        name="Dump path",
        subtype='FILE_PATH',
        description="LAMMPS/OVITO dump file",
        default="",
    )
    prototype: PointerProperty(
        name="Prototype",
        type=bpy.types.Object,
        description="Object to instance per atom (e.g., a UV Sphere with metallic material)",
    )
    atom_scale: FloatProperty(
        name="Atom Scale",
        default=0.2,
        min=0.0,
        description="Uniform scale for instanced atoms (post-radius)",
    )
    start_frame: IntProperty(
        name="Start",
        default=1,
        min=1,
    )
    step: IntProperty(
        name="Step",
        default=1,
        min=1,
    )
    live_playback: BoolProperty(
        name="Live playback",
        default=True,
        description="Update vertex positions on frame change",
    )

# --------------------------------------------------------------------------------------
# Handlers
# --------------------------------------------------------------------------------------
@persistent
def OVB_frame_update(scene):
    if not _OVB["handler_added"]:
        return
    frames = _OVB["frames"]
    keys = _OVB["frame_keys"]
    carrier = _OVB["carrier"]
    if not (frames and keys and carrier and carrier.data):
        return

    start = scene.ovb_props.start_frame
    step = scene.ovb_props.step
    if step <= 0:
        step = 1

    t = (scene.frame_current - start) // step
    if t < 0:
        t = 0
    if t >= len(keys):
        t = len(keys) - 1

    fkey = keys[t]
    coords = frames.get(fkey)
    if not coords:
        return

    me = carrier.data
    if len(me.vertices) != len(coords):
        me.clear_geometry()
        me.from_pydata(coords, [], [])
        me.update()
        return

    # Fast update
    for i, v in enumerate(me.vertices):
        v.co = coords[i]
    me.update()

def _remove_handler():
    to_remove = []
    for h in bpy.app.handlers.frame_change_post:
        if getattr(h, "__name__", "") == "OVB_frame_update":
            to_remove.append(h)
    for h in to_remove:
        bpy.app.handlers.frame_change_post.remove(h)
    _OVB["handler_added"] = False

def _add_handler():
    _remove_handler()
    bpy.app.handlers.frame_change_post.append(OVB_frame_update)
    _OVB["handler_added"] = True

# --------------------------------------------------------------------------------------
# Operators
# --------------------------------------------------------------------------------------
class OVB_OT_LoadDump(Operator):
    bl_idname = "ovb.load_dump"
    bl_label = "Load Dump"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        p = context.scene.ovb_props.dump_path
        proto = context.scene.ovb_props.prototype
        atom_scale = context.scene.ovb_props.atom_scale
        assert p, "Set a dump path"
        positions, frame_keys = _parse_dump(bpy.path.abspath(p))
        _OVB["frames"] = positions
        _OVB["frame_keys"] = frame_keys

        # Create carrier and set first frame vertices
        carrier = _create_or_get_carrier()
        _build_vertices(carrier, positions[frame_keys[0]])
        _OVB["carrier"] = carrier

        # Timeline
        scn = context.scene
        scn.frame_start = context.scene.ovb_props.start_frame
        scn.frame_end = scn.frame_start + max(0, (len(frame_keys) - 1)) * max(1, context.scene.ovb_props.step)

        # GN if prototype provided
        if proto:
            _ensure_gn_instancing(carrier, proto, _OVB["nodegroup_name"], _OVB["modifier_name"], atom_scale)
            _set_meshcache_first_then_gn(carrier, _OVB["modifier_name"])

        # Handlers
        if context.scene.ovb_props.live_playback:
            _add_handler()
        else:
            _remove_handler()

        self.report({'INFO'}, f"Loaded {len(positions[frame_keys[0]])} atoms, {len(frame_keys)} frames.")
        return {'FINISHED'}

class OVB_OT_BuildNodes(Operator):
    bl_idname = "ovb.build_nodes"
    bl_label = "Build GN"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        carrier = _OVB["carrier"] or _create_or_get_carrier()
        proto = context.scene.ovb_props.prototype
        atom_scale = context.scene.ovb_props.atom_scale
        assert proto is not None, "Assign a Prototype object"
        _ensure_gn_instancing(carrier, proto, _OVB["nodegroup_name"], _OVB["modifier_name"], atom_scale)
        _set_meshcache_first_then_gn(carrier, _OVB["modifier_name"])
        self.report({'INFO'}, "Geometry Nodes ready.")
        return {'FINISHED'}

class OVB_OT_SetScale(Operator):
    bl_idname = "ovb.set_scale"
    bl_label = "Apply Scale"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        inst_obj = _OVB["carrier"]
        assert inst_obj is not None, "Load a dump first"
        mod = inst_obj.modifiers.get(_OVB["modifier_name"])
        if not mod or not mod.node_group:
            self.report({'WARNING'}, "Build GN first")
            return {'CANCELLED'}
        ng = mod.node_group
        atom_scale = context.scene.ovb_props.atom_scale

        # Update group input default for AtomScale
        for i, inp in enumerate(ng.inputs):
            if inp.name == "AtomScale":
                try:
                    mod["Input_%d" % i] = atom_scale
                except Exception:
                    pass
                # Also update the Transform node defaults (for immediate feedback)
                for node in ng.nodes:
                    if node.bl_idname == "GeometryNodeTransform":
                        node.inputs["Scale"].default_value = (atom_scale, atom_scale, atom_scale)
                break

        self.report({'INFO'}, f"Atom scale = {atom_scale}")
        return {'FINISHED'}

class OVB_OT_TogglePlayback(Operator):
    bl_idname = "ovb.toggle_playback"
    bl_label = "Toggle Live Playback"
    bl_options = {'REGISTER', 'UNDO'}

    enable: BoolProperty(default=True)

    def execute(self, context):
        if self.enable:
            _add_handler()
            context.scene.ovb_props.live_playback = True
            self.report({'INFO'}, "Live playback ON")
        else:
            _remove_handler()
            context.scene.ovb_props.live_playback = False
            self.report({'INFO'}, "Live playback OFF")
        return {'FINISHED'}

class OVB_OT_ExportAlembic(Operator):
    bl_idname = "ovb.export_alembic"
    bl_label = "Export Alembic (.abc)"
    bl_options = {'REGISTER'}

    filepath: StringProperty(subtype='FILE_PATH')

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        carrier = _OVB["carrier"]
        assert carrier is not None, "Load a dump first"
        # Export evaluated mesh animation for deterministic renders.
        bpy.ops.wm.alembic_export(
            filepath=bpy.path.abspath(self.filepath),
            selected=False,
            start=context.scene.frame_start,
            end=context.scene.frame_end,
            global_scale=1.0,
            visible_objects_only=False,
            flatten=False,
            use_subdiv_schema=False,
            export_hair=False,
            export_particles=False,
            export_custom_properties=False,
            as_background_job=False,
        )
        self.report({'INFO'}, f"Alembic saved to {self.filepath}")
        return {'FINISHED'}

# --------------------------------------------------------------------------------------
# UI
# --------------------------------------------------------------------------------------
class OVB_PT_Main(Panel):
    bl_label = "OVITO → Blender"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "SciViz"

    def draw(self, context):
        s = context.scene.ovb_props
        col = self.layout.column(align=True)
        col.prop(s, "dump_path")
        col.prop(s, "prototype")
        col.prop(s, "atom_scale", slider=True)
        row = col.row(align=True)
        row.operator("ovb.load_dump", text="Load Dump", icon='FILE_FOLDER')
        row.operator("ovb.build_nodes", text="Build GN", icon='MOD_NODES')

        col.separator()
        col.label(text="Playback:")
        row = col.row(align=True)
        row.prop(s, "start_frame")
        row.prop(s, "step")
        row = col.row(align=True)
        row.operator("ovb.toggle_playback", text="Play").enable = True
        row.operator("ovb.toggle_playback", text="Stop").enable = False
        col.operator("ovb.set_scale", text="Apply Scale", icon='FULLSCREEN_ENTER')

        col.separator()
        col.label(text="Deterministic Render:")
        col.operator("ovb.export_alembic", text="Export Alembic (.abc)", icon='EXPORT')

# --------------------------------------------------------------------------------------
# Registration
# --------------------------------------------------------------------------------------
classes = (
    OVB_Props,
    OVB_OT_LoadDump,
    OVB_OT_BuildNodes,
    OVB_OT_SetScale,
    OVB_OT_TogglePlayback,
    OVB_OT_ExportAlembic,
    OVB_PT_Main,
)

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.ovb_props = PointerProperty(type=OVB_Props)
    _remove_handler()  # safety

def unregister():
    _remove_handler()
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
    if hasattr(bpy.types.Scene, "ovb_props"):
        del bpy.types.Scene.ovb_props