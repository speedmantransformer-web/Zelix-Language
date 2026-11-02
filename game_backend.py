"""Raylib game API metadata and generated native runtime."""

from __future__ import annotations

GAME_FUNCTIONS = {
    "init_window": 3,
    "close_window": 0,
    "window_should_close": 0,
    "frame_time": 0,
    "set_target_fps": 1,
    "begin_drawing": 0,
    "end_drawing": 0,
    "clear_background": 1,
    "draw_rectangle": 5,
    "draw_circle": 4,
    "draw_line": 5,
    "draw_text": 5,
    "begin_3d": 0,
    "end_3d": 0,
    "set_camera_3d": 6,
    "draw_cube": 5,
    "draw_voxel_face": 6,
    "draw_voxel_world": 8,
    "set_voxel_render_distance": 1,
    "distance_3d": 6,
    "draw_sphere": 5,
    "key_pressed": 1,
    "key_down": 1,
    "key_released": 1,
    "mouse_x": 0,
    "mouse_y": 0,
    "mouse_button_pressed": 1,
    "mouse_wheel": 0,
    "init_audio": 0,
    "load_sound": 1,
    "play_sound": 1,
    "unload_sound": 1,
    "close_audio": 0,
    "create_scene": 0,
    "activate_scene": 1,
    "create_object": 5,
    "add_object": 2,
    "move_object": 3,
    "set_object_position": 3,
    "draw_scene": 0,
    "clear_scene": 1,
    "create_body": 5,
    "physics_set_gravity": 1,
    "physics_update": 1,
    "body_set_velocity": 3,
    "body_apply_force": 3,
    "body_x": 1,
    "body_y": 1,
    "body_collides": 2,
    "network_start": 1,
    "network_send": 4,
    "network_receive": 1,
    "network_close": 1,
    "load_texture": 1,
    "unload_texture": 1,
    "draw_sprite": 3,
    "draw_sprite_ex": 6,
    "texture_width": 1,
    "texture_height": 1,
    "enable_asset_hot_reload": 0,
    "create_animation": 5,
    "update_animation": 2,
    "draw_animation": 4,
    "set_animation_looping": 2,
    "animation_frame": 1,
    "create_animation_machine": 0,
    "add_animation_state": 3,
    "add_animation_transition": 4,
    "set_animation_state": 2,
    "trigger_animation_event": 2,
    "update_animation_machine": 2,
    "draw_animation_machine": 4,
    "set_camera_2d": 6,
    "begin_camera_2d": 0,
    "end_camera_2d": 0,
    "mouse_button_down": 1,
    "mouse_button_released": 1,
    "mouse_world_x": 0,
    "mouse_world_y": 0,
    "create_combatant": 2,
    "destroy_combatant": 1,
    "combatant_health": 1,
    "combatant_max_health": 1,
    "combatant_armor": 1,
    "set_combatant_armor": 2,
    "apply_damage": 2,
    "heal_combatant": 2,
    "is_combatant_alive": 1,
    "apply_status_effect": 4,
    "remove_status_effect": 2,
    "has_status_effect": 2,
    "status_effect_remaining": 2,
    "update_status_effects": 2,
    "clear_status_effects": 1,
    "create_entity": 0,
    "destroy_entity": 1,
    "add_transform": 3,
    "entity_x": 1,
    "entity_y": 1,
    "set_entity_position": 3,
    "add_rigidbody": 2,
    "entity_set_velocity": 3,
    "entity_apply_force": 3,
    "entity_velocity_x": 1,
    "entity_velocity_y": 1,
    "add_box_collider": 5,
    "entity_collides": 2,
    "add_transform_3d": 4,
    "entity_z": 1,
    "set_entity_position_3d": 4,
    "entity_velocity_z": 1,
    "entity_set_velocity_3d": 4,
    "entity_apply_force_3d": 4,
    "add_box_collider_3d": 6,
    "entity_collides_3d": 2,
    "physics_set_gravity_3d": 3,
    "create_path_grid": 3,
    "destroy_path_grid": 1,
    "set_path_blocked": 4,
    "find_path": 5,
    "destroy_path": 1,
    "path_length": 1,
    "path_x": 2,
    "path_y": 2,
    "follow_path": 4,
    "create_particle_emitter": 1,
    "destroy_particle_emitter": 1,
    "emit_particles": 7,
    "update_particle_emitter": 2,
    "set_particle_gravity": 2,
    "draw_particle_emitter": 1,
    "particle_count": 1,
    "clear_particle_emitter": 1,
    "ui_panel": 5,
    "ui_label": 5,
    "ui_button": 5,
    "ui_checkbox": 4,
    "ui_progress_bar": 7,
    "save_number": 3,
    "load_number": 3,
    "save_text": 3,
    "load_text": 3,
    "save_boolean": 3,
    "load_boolean": 3,
}

GAME_FUNCTION_IDS = {name: index for index, name in enumerate(GAME_FUNCTIONS)}

GAME_FUNCTION_ARGUMENT_TYPES = {
    "load_texture": {0: "text"},
    "unload_texture": {0: "texture"},
    "draw_sprite": {0: "texture"},
    "draw_sprite_ex": {0: "texture"},
    "texture_width": {0: "texture"},
    "texture_height": {0: "texture"},
    "load_sound": {0: "text"},
    "play_sound": {0: "sound"},
    "unload_sound": {0: "sound"},
    "create_animation": {0: "texture"},
    "update_animation": {0: "animation"},
    "draw_animation": {0: "animation"},
    "set_animation_looping": {0: "animation"},
    "animation_frame": {0: "animation"},
    "add_animation_state": {0: "animation_machine", 2: "animation"},
    "add_animation_transition": {0: "animation_machine"},
    "set_animation_state": {0: "animation_machine"},
    "trigger_animation_event": {0: "animation_machine"},
    "update_animation_machine": {0: "animation_machine"},
    "draw_animation_machine": {0: "animation_machine"},
    "create_combatant": {0: "number", 1: "number"},
    "apply_damage": {0: "combatant", 1: "number"},
    "heal_combatant": {0: "combatant", 1: "number"},
    "update_status_effects": {0: "combatant", 1: "number"},
    "clear_status_effects": {0: "combatant"},
    "destroy_combatant": {0: "combatant"},
    "combatant_health": {0: "combatant"},
    "combatant_max_health": {0: "combatant"},
    "combatant_armor": {0: "combatant"},
    "set_combatant_armor": {0: "combatant", 1: "number"},
    "is_combatant_alive": {0: "combatant"},
    "apply_status_effect": {0: "combatant", 1: "text", 2: "number", 3: "number"},
    "remove_status_effect": {0: "combatant", 1: "text"},
    "has_status_effect": {0: "combatant", 1: "text"},
    "status_effect_remaining": {0: "combatant", 1: "text"},
    "destroy_entity": {0: "entity"},
    "add_transform": {0: "entity", 1: "number", 2: "number"},
    "entity_x": {0: "entity"},
    "entity_y": {0: "entity"},
    "set_entity_position": {0: "entity", 1: "number", 2: "number"},
    "add_rigidbody": {0: "entity", 1: "number"},
    "entity_set_velocity": {0: "entity", 1: "number", 2: "number"},
    "entity_apply_force": {0: "entity", 1: "number", 2: "number"},
    "entity_velocity_x": {0: "entity"},
    "entity_velocity_y": {0: "entity"},
    "add_box_collider": {
        0: "entity", 1: "number", 2: "number", 3: "number", 4: "number",
    },
    "entity_collides": {0: "entity", 1: "entity"},
    "add_transform_3d": {
        0: "entity", 1: "number", 2: "number", 3: "number",
    },
    "entity_z": {0: "entity"},
    "set_entity_position_3d": {
        0: "entity", 1: "number", 2: "number", 3: "number",
    },
    "entity_velocity_z": {0: "entity"},
    "entity_set_velocity_3d": {
        0: "entity", 1: "number", 2: "number", 3: "number",
    },
    "entity_apply_force_3d": {
        0: "entity", 1: "number", 2: "number", 3: "number",
    },
    "add_box_collider_3d": {
        0: "entity", 1: "number", 2: "number", 3: "number",
        4: "number", 5: "number",
    },
    "entity_collides_3d": {0: "entity", 1: "entity"},
    "physics_set_gravity_3d": {0: "number", 1: "number", 2: "number"},
    "destroy_path_grid": {0: "path_grid"},
    "set_path_blocked": {
        0: "path_grid", 1: "number", 2: "number", 3: "boolean",
    },
    "find_path": {
        0: "path_grid", 1: "number", 2: "number", 3: "number", 4: "number",
    },
    "destroy_path": {0: "path"},
    "path_length": {0: "path"},
    "path_x": {0: "path", 1: "number"},
    "path_y": {0: "path", 1: "number"},
    "follow_path": {0: "path", 1: "entity", 2: "number", 3: "number"},
    "create_particle_emitter": {0: "number"},
    "destroy_particle_emitter": {0: "particle_emitter"},
    "emit_particles": {
        0: "particle_emitter", 1: "number", 2: "number", 3: "number",
        4: "number", 5: "number", 6: "text",
    },
    "update_particle_emitter": {0: "particle_emitter", 1: "number"},
    "set_particle_gravity": {0: "particle_emitter", 1: "number"},
    "draw_particle_emitter": {0: "particle_emitter"},
    "particle_count": {0: "particle_emitter"},
    "clear_particle_emitter": {0: "particle_emitter"},
    "ui_panel": {0: "number", 1: "number", 2: "number", 3: "number", 4: "text"},
    "ui_label": {
        0: "number", 1: "number", 2: "text", 3: "number", 4: "text",
    },
    "ui_button": {
        0: "number", 1: "number", 2: "number", 3: "number", 4: "text",
    },
    "ui_checkbox": {
        0: "number", 1: "number", 2: "text", 3: "boolean",
    },
    "ui_progress_bar": {
        0: "number", 1: "number", 2: "number", 3: "number",
        4: "number", 5: "number", 6: "text",
    },
    "set_camera_3d": {
        0: "number", 1: "number", 2: "number",
        3: "number", 4: "number", 5: "number",
    },
    "set_voxel_render_distance": {0: "number"},
    "distance_3d": {
        0: "number", 1: "number", 2: "number",
        3: "number", 4: "number", 5: "number",
    },
    "save_number": {0: "text", 1: "text", 2: "number"},
    "load_number": {0: "text", 1: "text", 2: "number"},
    "save_text": {0: "text", 1: "text", 2: "text"},
    "load_text": {0: "text", 1: "text", 2: "text"},
    "save_boolean": {0: "text", 1: "text", 2: "boolean"},
    "load_boolean": {0: "text", 1: "text", 2: "boolean"},
}
GAME_FUNCTION_RETURN_TYPES = {
    "window_should_close": "boolean",
    "frame_time": "number",
    "key_down": "boolean",
    "load_texture": "texture",
    "load_sound": "sound",
    "create_animation": "animation",
    "create_animation_machine": "animation_machine",
    "create_combatant": "combatant",
    "destroy_combatant": "void",
    "apply_status_effect": "void",
    "update_status_effects": "void",
    "clear_status_effects": "void",
    "combatant_health": "number",
    "combatant_max_health": "number",
    "combatant_armor": "number",
    "set_combatant_armor": "void",
    "apply_damage": "number",
    "heal_combatant": "number",
    "is_combatant_alive": "boolean",
    "remove_status_effect": "boolean",
    "has_status_effect": "boolean",
    "status_effect_remaining": "number",
    "create_entity": "entity",
    "destroy_entity": "void",
    "add_transform": "void",
    "entity_x": "number",
    "entity_y": "number",
    "set_entity_position": "void",
    "add_rigidbody": "void",
    "entity_set_velocity": "void",
    "entity_apply_force": "void",
    "entity_velocity_x": "number",
    "entity_velocity_y": "number",
    "add_box_collider": "void",
    "entity_collides": "boolean",
    "add_transform_3d": "void",
    "entity_z": "number",
    "set_entity_position_3d": "void",
    "entity_velocity_z": "number",
    "entity_set_velocity_3d": "void",
    "entity_apply_force_3d": "void",
    "add_box_collider_3d": "void",
    "entity_collides_3d": "boolean",
    "physics_set_gravity_3d": "void",
    "create_path_grid": "path_grid",
    "destroy_path_grid": "void",
    "set_path_blocked": "void",
    "find_path": "path",
    "destroy_path": "void",
    "path_length": "number",
    "path_x": "number",
    "path_y": "number",
    "follow_path": "boolean",
    "create_particle_emitter": "particle_emitter",
    "destroy_particle_emitter": "void",
    "emit_particles": "number",
    "update_particle_emitter": "void",
    "set_particle_gravity": "void",
    "draw_particle_emitter": "void",
    "particle_count": "number",
    "clear_particle_emitter": "void",
    "ui_panel": "void",
    "ui_label": "void",
    "ui_button": "boolean",
    "ui_checkbox": "boolean",
    "ui_progress_bar": "void",
    "set_camera_3d": "void",
    "set_voxel_render_distance": "void",
    "distance_3d": "number",
    "save_number": "void",
    "load_number": "number",
    "save_text": "void",
    "load_text": "text",
    "save_boolean": "void",
    "load_boolean": "boolean",
}


GAME_RUNTIME_C = r'''
#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#endif
#include "raylib.h"
#include "rlgl.h"
#include <errno.h>
#include <float.h>
#include <limits.h>
#include <stdint.h>
#ifndef _WIN32
#include <arpa/inet.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>
#endif

#define Z_GAME_MAX_HANDLES 256
#define Z_GAME_MAX_SCENES 64
#define Z_GAME_MAX_OBJECTS 1024
#define Z_GAME_MAX_COMBATANTS 256
#define Z_GAME_MAX_ENTITIES 512
#define Z_GAME_MAX_PATH_GRIDS 8
#define Z_GAME_MAX_PATHS 32
#define Z_GAME_MAX_PATH_CELLS 4096
#define Z_GAME_MAX_PARTICLE_EMITTERS 32
#define Z_GAME_MAX_PARTICLES 256
#define Z_GAME_MAX_STATUS_EFFECTS 8
#define Z_GAME_MAX_ANIMATION_STATES 32
#define Z_GAME_MAX_ANIMATION_TRANSITIONS 64

enum {
    __GAME_FUNCTION_ENUM__
};

static bool z_window_open = false;
static bool z_audio_open = false;
static Camera3D z_camera = { 0 };
static bool z_camera_3d_initialized = false;
static double z_voxel_render_distance = 64.0;
static Camera2D z_camera_2d = { 0 };
static bool z_camera_2d_active = false;
static Sound z_sounds[Z_GAME_MAX_HANDLES];
static bool z_sound_loaded[Z_GAME_MAX_HANDLES];
static bool z_texture_loaded[Z_GAME_MAX_HANDLES];
static Texture2D z_textures[Z_GAME_MAX_HANDLES];
static char *z_texture_paths[Z_GAME_MAX_HANDLES];
static long long z_texture_modified[Z_GAME_MAX_HANDLES];
static bool z_asset_hot_reload = false;
static bool z_animation_active[Z_GAME_MAX_HANDLES];
static int z_animation_texture[Z_GAME_MAX_HANDLES];
static int z_animation_frame_width[Z_GAME_MAX_HANDLES];
static int z_animation_frame_height[Z_GAME_MAX_HANDLES];
static int z_animation_frame_count[Z_GAME_MAX_HANDLES];
static int z_animation_frame[Z_GAME_MAX_HANDLES];
static double z_animation_fps[Z_GAME_MAX_HANDLES];
static double z_animation_elapsed[Z_GAME_MAX_HANDLES];
static bool z_animation_looping[Z_GAME_MAX_HANDLES];
static bool z_animation_finished[Z_GAME_MAX_HANDLES];
static float z_gravity = 980.0f;
static Vector3 z_gravity_3d = { 0, -9.8f, 0 };
static int z_active_scene = -1;

typedef struct {
    char name[64];
    int animation;
} ZAnimationState;

typedef struct {
    char from[64];
    char event[64];
    char to[64];
} ZAnimationTransition;

typedef struct {
    bool active;
    ZAnimationState states[Z_GAME_MAX_ANIMATION_STATES];
    int state_count;
    int active_state;
    ZAnimationTransition transitions[Z_GAME_MAX_ANIMATION_TRANSITIONS];
    int transition_count;
} ZAnimationMachine;

typedef struct {
    bool active;
    float x, y, width, height;
    Color color;
} ZGameObject;

typedef struct {
    bool active;
    int objects[Z_GAME_MAX_OBJECTS];
    int count;
} ZGameScene;

typedef struct {
    bool active;
    float x, y, width, height, mass, vx, vy, restitution, friction;
} ZPhysicsBody;

typedef struct {
    bool active;
    uint32_t generation;
} ZEntity;

typedef struct {
    bool active;
    bool three_dimensional;
    float x, y, z;
} ZTransform;

typedef struct {
    bool active;
    float mass, vx, vy, vz, force_x, force_y, force_z;
} ZRigidBody;

typedef struct {
    bool active;
    float width, height, restitution, friction;
} ZBoxCollider;

typedef struct {
    bool active;
    float width, height, depth, restitution, friction;
} ZBoxCollider3D;

typedef struct {
    bool active;
    uint32_t generation;
    int width, height;
    float cell_size;
    bool blocked[Z_GAME_MAX_PATH_CELLS];
} ZPathGrid;

typedef struct {
    bool active;
    uint32_t generation;
    int grid_index;
    uint32_t grid_generation;
    int length;
    int x[Z_GAME_MAX_PATH_CELLS];
    int y[Z_GAME_MAX_PATH_CELLS];
    int cursor;
    int entity_index;
    uint32_t entity_generation;
} ZPath;

typedef struct {
    bool active;
    float x, y, vx, vy, remaining, radius;
    Color color;
} ZParticle;

typedef struct {
    bool active;
    uint32_t generation;
    int capacity;
    float gravity;
    uint32_t random_state;
    ZParticle particles[Z_GAME_MAX_PARTICLES];
} ZParticleEmitter;

typedef struct {
    bool active;
    char name[16];
    double remaining;
    double strength;
} ZStatusEffect;

typedef struct {
    bool active;
    uint32_t generation;
    double health;
    double max_health;
    double armor;
    ZStatusEffect effects[Z_GAME_MAX_STATUS_EFFECTS];
} ZCombatant;

static ZGameObject z_objects[Z_GAME_MAX_OBJECTS];
static ZGameScene z_scenes[Z_GAME_MAX_SCENES];
static ZPhysicsBody z_bodies[Z_GAME_MAX_OBJECTS];
static ZEntity z_entities[Z_GAME_MAX_ENTITIES];
static ZTransform z_transforms[Z_GAME_MAX_ENTITIES];
static ZRigidBody z_rigid_bodies[Z_GAME_MAX_ENTITIES];
static ZBoxCollider z_box_colliders[Z_GAME_MAX_ENTITIES];
static ZBoxCollider3D z_box_colliders_3d[Z_GAME_MAX_ENTITIES];
static ZPathGrid z_path_grids[Z_GAME_MAX_PATH_GRIDS];
static ZPath z_paths[Z_GAME_MAX_PATHS];
static ZParticleEmitter z_particle_emitters[Z_GAME_MAX_PARTICLE_EMITTERS];
static ZCombatant z_combatants[Z_GAME_MAX_COMBATANTS];
static ZAnimationMachine z_animation_machines[Z_GAME_MAX_HANDLES];

#ifdef _WIN32
static SOCKET z_sockets[Z_GAME_MAX_HANDLES];
static bool z_socket_used[Z_GAME_MAX_HANDLES];
static bool z_winsock_open = false;
#else
static int z_sockets[Z_GAME_MAX_HANDLES];
static bool z_socket_used[Z_GAME_MAX_HANDLES];
#endif

static Value z_game_number(double number) {
    Value value;
    value.type = Z_NUMBER;
    value.number = number;
    value.string = NULL;
    return value;
}

static Value z_game_string(const char *string) {
    Value value;
    value.type = Z_STRING;
    value.number = 0;
    value.string = string;
    return value;
}

static double z_game_num(Value *args, int index, int line) {
    return z_number(args[index], line);
}

static const char *z_game_str(Value *args, int index, int line) {
    if (args[index].type != Z_STRING) z_fail(line, "Expected text argument");
    return args[index].string;
}

static int z_game_handle(Value *args, int index, int limit, int line, const char *kind) {
    double number = z_game_num(args, index, line);
    if (floor(number) != number || number < 0 || number >= limit) {
        z_fail(line, kind);
    }
    return (int)number;
}

static const char *z_game_asset_path(const char *path, int line) {
    if (path[0] == '/' || path[0] == '\\' ||
        (path[0] && path[1] == ':')) return path;
    static char resolved[4096];
    int length = snprintf(resolved, sizeof resolved, "%s/%s", Z_ASSET_ROOT, path);
    if (length < 0 || (size_t)length >= sizeof resolved)
        z_fail(line, "Asset path is too long");
    return resolved;
}

static const char *z_game_save_path(const char *path, int line) {
    if (!path[0] || path[0] == '/' || path[0] == '\\' ||
        (path[0] && path[1] == ':'))
        z_fail(line, "Save filename must be a non-empty relative path");
    const char *segment = path;
    for (const char *cursor = path;; ++cursor) {
        if (*cursor == ':' || (unsigned char)*cursor < 32)
            z_fail(line, "Save filename contains an invalid character");
        if (*cursor == '/' || *cursor == '\\' || *cursor == '\0') {
            size_t length = (size_t)(cursor - segment);
            if (length == 2 && segment[0] == '.' && segment[1] == '.')
                z_fail(line, "Save filename cannot leave the game directory");
            if (*cursor == '\0') break;
            segment = cursor + 1;
        }
    }
    static char resolved[4096];
    int length = snprintf(resolved, sizeof resolved, "%s/%s", Z_ASSET_ROOT, path);
    if (length < 0 || (size_t)length >= sizeof resolved)
        z_fail(line, "Save filename is too long");
    return resolved;
}

static void z_game_validate_save_key(const char *key, int line) {
    size_t length = strlen(key);
    if (length == 0 || length > 64)
        z_fail(line, "Save key must contain 1 to 64 characters");
    for (size_t i = 0; i < length; ++i) {
        unsigned char c = (unsigned char)key[i];
        if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
              (c >= '0' && c <= '9') || c == '_' || c == '-' || c == '.'))
            z_fail(line, "Save keys may contain only letters, numbers, '.', '_' and '-'");
    }
}

static int z_game_hex_value(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    return -1;
}

static void z_game_encode_save_text(const char *text, char *output,
                                   size_t output_size, int line) {
    static const char hex[] = "0123456789ABCDEF";
    if (strlen(text) > 4095)
        z_fail(line, "Text save value exceeds the maximum supported size");
    size_t written = 0;
    for (const unsigned char *cursor = (const unsigned char *)text; *cursor; ++cursor) {
        unsigned char value = *cursor;
        bool escape = value < 32 || value > 126 || value == '%' || value == '\t';
        size_t needed = escape ? 3 : 1;
        if (written + needed >= output_size)
            z_fail(line, "Text save value exceeds the maximum supported size");
        if (escape) {
            output[written++] = '%';
            output[written++] = hex[value >> 4];
            output[written++] = hex[value & 15];
        } else {
            output[written++] = (char)value;
        }
    }
    output[written] = '\0';
}

static void z_game_save_value(const char *filename, const char *key,
                              char type, const char *value, int line) {
    const char *path = z_game_save_path(filename, line);
    z_game_validate_save_key(key, line);
    if (strlen(key) + strlen(value) + 4 > 8191)
        z_fail(line, "Save record exceeds the maximum supported size");
    FILE *file = fopen(path, "ab");
    if (!file) z_fail(line, "Could not open save file for writing");
    bool failed = fprintf(file, "%s\t%c\t%s\n", key, type, value) < 0;
    if (fflush(file) != 0) failed = true;
    if (fclose(file) != 0) failed = true;
    if (failed) z_fail(line, "Could not write save data");
}

static bool z_game_load_value(const char *filename, const char *key,
                              char expected_type, char *output,
                              size_t output_size, int line) {
    const char *path = z_game_save_path(filename, line);
    z_game_validate_save_key(key, line);
    FILE *file = fopen(path, "rb");
    if (!file) {
        if (errno == ENOENT) return false;
        z_fail(line, "Could not open save file for reading");
    }
    char row[8192], found_type = '\0';
    char latest[8192] = { 0 };
    bool found = false;
    while (fgets(row, sizeof row, file)) {
        size_t length = strlen(row);
        if (!length || row[length - 1] != '\n')
            z_fail(line, "Save record is truncated or exceeds the maximum supported size");
        row[--length] = '\0';
        if (length && row[length - 1] == '\r') row[--length] = '\0';
        char *first = strchr(row, '\t');
        if (!first) z_fail(line, "Malformed save record");
        *first++ = '\0';
        char *second = strchr(first, '\t');
        if (!second || strchr(second + 1, '\t'))
            z_fail(line, "Malformed save record");
        *second++ = '\0';
        z_game_validate_save_key(row, line);
        if (first[1] != '\0' ||
            (first[0] != 'n' && first[0] != 'b' && first[0] != 's'))
            z_fail(line, "Malformed save record type");
        if (strcmp(row, key) != 0) continue;
        found_type = first[0];
        size_t value_length = strlen(second);
        if (value_length >= sizeof latest)
            z_fail(line, "Save value exceeds the maximum supported size");
        memcpy(latest, second, value_length + 1);
        found = true;
    }
    if (ferror(file)) {
        fclose(file);
        z_fail(line, "Could not read save data");
    }
    if (fclose(file) != 0) z_fail(line, "Could not close save file");
    if (!found) return false;
    if (found_type != expected_type)
        z_fail(line, "Saved value has a different type");

    size_t decoded = 0;
    for (size_t i = 0; latest[i]; ++i) {
        unsigned char value = (unsigned char)latest[i];
        if (expected_type == 's' && value == '%') {
            int high = z_game_hex_value(latest[i + 1]);
            int low = z_game_hex_value(latest[i + 2]);
            if (high < 0 || low < 0)
                z_fail(line, "Malformed escaped text in save file");
            value = (unsigned char)((high << 4) | low);
            i += 2;
        }
        if (value == '\0' || decoded + 1 >= output_size)
            z_fail(line, "Loaded save value exceeds the maximum supported size");
        output[decoded++] = (char)value;
    }
    output[decoded] = '\0';
    return true;
}

static int z_game_texture_handle(Value *args, int index, int line) {
    int handle = z_game_handle(args, index, Z_GAME_MAX_HANDLES, line, "Invalid texture handle");
    if (!z_texture_loaded[handle]) z_fail(line, "Texture handle is not loaded");
    return handle;
}

static int z_game_animation_handle(Value *args, int index, int line) {
    int handle = z_game_handle(args, index, Z_GAME_MAX_HANDLES, line, "Invalid animation handle");
    if (!z_animation_active[handle]) z_fail(line, "Animation handle is not active");
    return handle;
}

static int z_game_machine_handle(Value *args, int index, int line) {
    int handle = z_game_handle(args, index, Z_GAME_MAX_HANDLES, line, "Invalid animation machine handle");
    if (!z_animation_machines[handle].active) z_fail(line, "Animation machine does not exist");
    return handle;
}

static int z_game_combatant_handle(Value *args, int index, int line) {
    double raw = z_game_num(args, index, line);
    double maximum = (double)UINT32_MAX * Z_GAME_MAX_COMBATANTS +
                     (Z_GAME_MAX_COMBATANTS - 1);
    if (!isfinite(raw) || floor(raw) != raw || raw < Z_GAME_MAX_COMBATANTS ||
        raw > maximum) z_fail(line, "Invalid combatant handle");
    uint64_t token = (uint64_t)raw;
    int handle = (int)(token % Z_GAME_MAX_COMBATANTS);
    uint32_t generation = (uint32_t)(token / Z_GAME_MAX_COMBATANTS);
    if (!z_combatants[handle].active ||
        z_combatants[handle].generation != generation)
        z_fail(line, "Combatant handle is not active");
    return handle;
}

static int z_game_entity_handle(Value *args, int index, int line) {
    double raw = z_game_num(args, index, line);
    double maximum = (double)UINT32_MAX * Z_GAME_MAX_ENTITIES +
                     (Z_GAME_MAX_ENTITIES - 1);
    if (!isfinite(raw) || floor(raw) != raw || raw < Z_GAME_MAX_ENTITIES ||
        raw > maximum) z_fail(line, "Invalid entity handle");
    uint64_t token = (uint64_t)raw;
    int handle = (int)(token % Z_GAME_MAX_ENTITIES);
    uint32_t generation = (uint32_t)(token / Z_GAME_MAX_ENTITIES);
    if (!z_entities[handle].active ||
        z_entities[handle].generation != generation)
        z_fail(line, "Entity handle is not active");
    return handle;
}

static int z_game_path_grid_handle(Value *args, int index, int line) {
    double raw = z_game_num(args, index, line);
    double maximum = (double)UINT32_MAX * Z_GAME_MAX_PATH_GRIDS +
                     (Z_GAME_MAX_PATH_GRIDS - 1);
    if (!isfinite(raw) || floor(raw) != raw || raw < Z_GAME_MAX_PATH_GRIDS ||
        raw > maximum) z_fail(line, "Invalid path-grid handle");
    uint64_t token = (uint64_t)raw;
    int handle = (int)(token % Z_GAME_MAX_PATH_GRIDS);
    uint32_t generation = (uint32_t)(token / Z_GAME_MAX_PATH_GRIDS);
    if (!z_path_grids[handle].active ||
        z_path_grids[handle].generation != generation)
        z_fail(line, "Path-grid handle is not active");
    return handle;
}

static int z_game_path_handle(Value *args, int index, int line) {
    double raw = z_game_num(args, index, line);
    double maximum = (double)UINT32_MAX * Z_GAME_MAX_PATHS +
                     (Z_GAME_MAX_PATHS - 1);
    if (!isfinite(raw) || floor(raw) != raw || raw < Z_GAME_MAX_PATHS ||
        raw > maximum) z_fail(line, "Invalid path handle");
    uint64_t token = (uint64_t)raw;
    int handle = (int)(token % Z_GAME_MAX_PATHS);
    uint32_t generation = (uint32_t)(token / Z_GAME_MAX_PATHS);
    if (!z_paths[handle].active || z_paths[handle].generation != generation)
        z_fail(line, "Path handle is not active");
    ZPath *path = &z_paths[handle];
    if (path->grid_index < 0 || path->grid_index >= Z_GAME_MAX_PATH_GRIDS ||
        !z_path_grids[path->grid_index].active ||
        z_path_grids[path->grid_index].generation != path->grid_generation)
        z_fail(line, "Path grid is no longer active");
    return handle;
}

static int z_game_particle_emitter_handle(Value *args, int index, int line) {
    double raw = z_game_num(args, index, line);
    double maximum = (double)UINT32_MAX * Z_GAME_MAX_PARTICLE_EMITTERS +
                     (Z_GAME_MAX_PARTICLE_EMITTERS - 1);
    if (!isfinite(raw) || floor(raw) != raw ||
        raw < Z_GAME_MAX_PARTICLE_EMITTERS || raw > maximum)
        z_fail(line, "Invalid particle-emitter handle");
    uint64_t token = (uint64_t)raw;
    int handle = (int)(token % Z_GAME_MAX_PARTICLE_EMITTERS);
    uint32_t generation = (uint32_t)(token / Z_GAME_MAX_PARTICLE_EMITTERS);
    if (!z_particle_emitters[handle].active ||
        z_particle_emitters[handle].generation != generation)
        z_fail(line, "Particle-emitter handle is not active");
    return handle;
}

static void z_game_find_path(ZPathGrid *grid, ZPath *path, int sx, int sy,
                             int gx, int gy, int line) {
    if (sx < 0 || sy < 0 || sx >= grid->width || sy >= grid->height ||
        gx < 0 || gy < 0 || gx >= grid->width || gy >= grid->height)
        z_fail(line, "Path coordinates are outside the grid");
    path->length = 0;
    path->cursor = 0;
    path->entity_index = -1;
    if (grid->blocked[sy * grid->width + sx] ||
        grid->blocked[gy * grid->width + gx]) return;

    int count = grid->width * grid->height;
    float cost[Z_GAME_MAX_PATH_CELLS];
    int parent[Z_GAME_MAX_PATH_CELLS];
    bool open[Z_GAME_MAX_PATH_CELLS] = { false };
    bool closed[Z_GAME_MAX_PATH_CELLS] = { false };
    for (int i = 0; i < count; ++i) {
        cost[i] = FLT_MAX;
        parent[i] = -1;
    }
    int start = sy * grid->width + sx;
    int goal = gy * grid->width + gx;
    cost[start] = 0;
    open[start] = true;
    const int dx[4] = { 1, -1, 0, 0 };
    const int dy[4] = { 0, 0, 1, -1 };

    while (true) {
        int current = -1;
        float best = FLT_MAX;
        for (int i = 0; i < count; ++i) {
            if (!open[i] || closed[i]) continue;
            int x = i % grid->width, y = i / grid->width;
            float heuristic = (float)(abs(gx - x) + abs(gy - y));
            float score = cost[i] + heuristic;
            if (score < best) {
                best = score;
                current = i;
            }
        }
        if (current < 0) return;
        if (current == goal) break;
        closed[current] = true;
        int x = current % grid->width, y = current / grid->width;
        for (int direction = 0; direction < 4; ++direction) {
            int nx = x + dx[direction], ny = y + dy[direction];
            if (nx < 0 || ny < 0 || nx >= grid->width || ny >= grid->height)
                continue;
            int neighbor = ny * grid->width + nx;
            if (grid->blocked[neighbor] || closed[neighbor]) continue;
            float candidate = cost[current] + 1;
            if (candidate >= cost[neighbor]) continue;
            cost[neighbor] = candidate;
            parent[neighbor] = current;
            open[neighbor] = true;
        }
    }

    int reverse[Z_GAME_MAX_PATH_CELLS];
    int length = 0;
    for (int node = goal; node >= 0; node = parent[node]) {
        if (length >= count) z_fail(line, "Path reconstruction exceeded grid bounds");
        reverse[length++] = node;
        if (node == start) break;
    }
    if (reverse[length - 1] != start) return;
    path->length = length;
    for (int i = 0; i < length; ++i) {
        int node = reverse[length - 1 - i];
        path->x[i] = node % grid->width;
        path->y[i] = node / grid->width;
    }
    path->cursor = 0;
}

static uint32_t z_game_random(uint32_t *state) {
    uint32_t value = *state;
    if (value == 0) value = 0x9e3779b9u;
    value ^= value << 13;
    value ^= value >> 17;
    value ^= value << 5;
    *state = value;
    return value;
}

static void z_game_resolve_aabb(
    float *ax, float *ay, float aw, float ah, float inv_a,
    float *avx, float *avy, float a_restitution, float a_friction,
    float *bx, float *by, float bw, float bh, float inv_b,
    float *bvx, float *bvy, float b_restitution, float b_friction
) {
    float overlap_x = fminf(*ax + aw, *bx + bw) - fmaxf(*ax, *bx);
    float overlap_y = fminf(*ay + ah, *by + bh) - fmaxf(*ay, *by);
    if (overlap_x <= 0 || overlap_y <= 0) return;
    float inverse_mass = inv_a + inv_b;
    if (inverse_mass <= 0) return;
    float normal_x = 0, normal_y = 0, penetration;
    if (overlap_x < overlap_y) {
        normal_x = *ax + aw * 0.5f < *bx + bw * 0.5f ? 1.0f : -1.0f;
        penetration = overlap_x;
    } else {
        normal_y = *ay + ah * 0.5f < *by + bh * 0.5f ? 1.0f : -1.0f;
        penetration = overlap_y;
    }
    float correction = fmaxf(penetration - 0.001f, 0) * 0.8f / inverse_mass;
    *ax -= normal_x * correction * inv_a;
    *ay -= normal_y * correction * inv_a;
    *bx += normal_x * correction * inv_b;
    *by += normal_y * correction * inv_b;

    float relative_x = *bvx - *avx, relative_y = *bvy - *avy;
    float velocity_normal = relative_x * normal_x + relative_y * normal_y;
    if (velocity_normal >= 0) return;
    float restitution = fminf(a_restitution, b_restitution);
    float impulse = -(1 + restitution) * velocity_normal / inverse_mass;
    *avx -= impulse * inv_a * normal_x;
    *avy -= impulse * inv_a * normal_y;
    *bvx += impulse * inv_b * normal_x;
    *bvy += impulse * inv_b * normal_y;

    relative_x = *bvx - *avx;
    relative_y = *bvy - *avy;
    float tangent_x = relative_x - (relative_x * normal_x +
                                     relative_y * normal_y) * normal_x;
    float tangent_y = relative_y - (relative_x * normal_x +
                                     relative_y * normal_y) * normal_y;
    float tangent_length = sqrtf(tangent_x * tangent_x + tangent_y * tangent_y);
    if (tangent_length <= 0) return;
    tangent_x /= tangent_length;
    tangent_y /= tangent_length;
    float friction_impulse = -(relative_x * tangent_x + relative_y * tangent_y) /
                             inverse_mass;
    float friction = sqrtf(a_friction * b_friction);
    friction_impulse = fmaxf(-impulse * friction,
                             fminf(friction_impulse, impulse * friction));
    *avx -= friction_impulse * inv_a * tangent_x;
    *avy -= friction_impulse * inv_a * tangent_y;
    *bvx += friction_impulse * inv_b * tangent_x;
    *bvy += friction_impulse * inv_b * tangent_y;
}

static void z_game_resolve_box_3d(
    ZTransform *a_position, ZBoxCollider3D *a_collider, ZRigidBody *a_body,
    ZTransform *b_position, ZBoxCollider3D *b_collider, ZRigidBody *b_body
) {
    float *a_position_axis[3] = {
        &a_position->x, &a_position->y, &a_position->z
    };
    float *b_position_axis[3] = {
        &b_position->x, &b_position->y, &b_position->z
    };
    float a_size[3] = {
        a_collider->width, a_collider->height, a_collider->depth
    };
    float b_size[3] = {
        b_collider->width, b_collider->height, b_collider->depth
    };
    float a_velocity[3] = {
        a_body ? a_body->vx : 0, a_body ? a_body->vy : 0,
        a_body ? a_body->vz : 0
    };
    float b_velocity[3] = {
        b_body ? b_body->vx : 0, b_body ? b_body->vy : 0,
        b_body ? b_body->vz : 0
    };
    float inv_a = a_body && a_body->mass > 0 ? 1.0f / a_body->mass : 0;
    float inv_b = b_body && b_body->mass > 0 ? 1.0f / b_body->mass : 0;
    float inverse_mass = inv_a + inv_b;
    if (inverse_mass <= 0) return;

    float overlap[3];
    for (int axis = 0; axis < 3; ++axis) {
        float a_min = *a_position_axis[axis];
        float b_min = *b_position_axis[axis];
        overlap[axis] = fminf(a_min + a_size[axis], b_min + b_size[axis]) -
                        fmaxf(a_min, b_min);
        if (overlap[axis] <= 0) return;
    }

    int axis = overlap[0] <= overlap[1] && overlap[0] <= overlap[2] ? 0
             : overlap[1] <= overlap[2] ? 1 : 2;
    float normal = *a_position_axis[axis] + a_size[axis] * 0.5f <
                   *b_position_axis[axis] + b_size[axis] * 0.5f ? 1.0f : -1.0f;
    float correction = fmaxf(overlap[axis] - 0.001f, 0) *
                       0.8f / inverse_mass;
    *a_position_axis[axis] -= normal * correction * inv_a;
    *b_position_axis[axis] += normal * correction * inv_b;

    float relative[3] = {
        b_velocity[0] - a_velocity[0],
        b_velocity[1] - a_velocity[1],
        b_velocity[2] - a_velocity[2]
    };
    float velocity_normal = relative[axis] * normal;
    if (velocity_normal >= 0) return;
    float restitution = fminf(a_collider->restitution, b_collider->restitution);
    float impulse = -(1 + restitution) * velocity_normal / inverse_mass;
    a_velocity[axis] -= impulse * inv_a * normal;
    b_velocity[axis] += impulse * inv_b * normal;

    relative[0] = b_velocity[0] - a_velocity[0];
    relative[1] = b_velocity[1] - a_velocity[1];
    relative[2] = b_velocity[2] - a_velocity[2];
    float tangent[3] = { relative[0], relative[1], relative[2] };
    tangent[axis] = 0;
    float tangent_length = sqrtf(tangent[0] * tangent[0] +
                                 tangent[1] * tangent[1] +
                                 tangent[2] * tangent[2]);
    if (tangent_length > 0) {
        for (int i = 0; i < 3; ++i) tangent[i] /= tangent_length;
        float friction_impulse =
            -(relative[0] * tangent[0] + relative[1] * tangent[1] +
              relative[2] * tangent[2]) / inverse_mass;
        float friction = sqrtf(a_collider->friction * b_collider->friction);
        friction_impulse = fmaxf(-impulse * friction,
                                 fminf(friction_impulse, impulse * friction));
        for (int i = 0; i < 3; ++i) {
            a_velocity[i] -= friction_impulse * inv_a * tangent[i];
            b_velocity[i] += friction_impulse * inv_b * tangent[i];
        }
    }

    if (a_body) {
        a_body->vx = a_velocity[0];
        a_body->vy = a_velocity[1];
        a_body->vz = a_velocity[2];
    }
    if (b_body) {
        b_body->vx = b_velocity[0];
        b_body->vy = b_velocity[1];
        b_body->vz = b_velocity[2];
    }
}

static int z_game_status_effect(int combatant, const char *name) {
    for (int i = 0; i < Z_GAME_MAX_STATUS_EFFECTS; ++i) {
        if (z_combatants[combatant].effects[i].active &&
            TextIsEqual(z_combatants[combatant].effects[i].name, name)) return i;
    }
    return -1;
}

static void z_game_reset_animation(int animation) {
    z_animation_frame[animation] = 0;
    z_animation_elapsed[animation] = 0;
    z_animation_finished[animation] = false;
}

static void z_game_update_animation(int animation, double delta, int line) {
    if (!isfinite(delta) || delta < 0 || delta > 1)
        z_fail(line, "Animation delta must be between 0 and 1 second");
    if (z_animation_finished[animation]) return;
    z_animation_elapsed[animation] += delta;
    double frame_duration = 1.0 / z_animation_fps[animation];
    while (z_animation_elapsed[animation] >= frame_duration) {
        z_animation_elapsed[animation] -= frame_duration;
        if (z_animation_frame[animation] + 1 < z_animation_frame_count[animation]) {
            ++z_animation_frame[animation];
        } else if (z_animation_looping[animation]) {
            z_animation_frame[animation] = 0;
        } else {
            z_animation_finished[animation] = true;
            z_animation_elapsed[animation] = 0;
            break;
        }
    }
}

static void z_game_refresh_textures(void) {
    if (!z_asset_hot_reload) return;
    for (int i = 0; i < Z_GAME_MAX_HANDLES; ++i) {
        if (!z_texture_loaded[i] || !FileExists(z_texture_paths[i])) continue;
        long long modified = GetFileModTime(z_texture_paths[i]);
        if (modified <= z_texture_modified[i]) continue;
        Texture2D replacement = LoadTexture(z_texture_paths[i]);
        z_texture_modified[i] = modified;
        if (replacement.id == 0 || replacement.width <= 0 || replacement.height <= 0) {
            if (replacement.id != 0) UnloadTexture(replacement);
            fprintf(stderr, "Zelix warning: changed texture could not be reloaded: %s\n",
                    z_texture_paths[i]);
            continue;
        }
        bool compatible = true;
        for (int animation = 0; animation < Z_GAME_MAX_HANDLES; ++animation) {
            if (!z_animation_active[animation] || z_animation_texture[animation] != i) continue;
            int columns = replacement.width / z_animation_frame_width[animation];
            int rows = replacement.height / z_animation_frame_height[animation];
            if (columns * rows < z_animation_frame_count[animation]) compatible = false;
        }
        if (!compatible) {
            UnloadTexture(replacement);
            fprintf(stderr, "Zelix warning: changed texture no longer fits its animations: %s\n",
                    z_texture_paths[i]);
            continue;
        }
        UnloadTexture(z_textures[i]);
        z_textures[i] = replacement;
    }
}

static int z_game_animation_state(int machine, const char *name) {
    for (int i = 0; i < z_animation_machines[machine].state_count; ++i) {
        if (TextIsEqual(z_animation_machines[machine].states[i].name, name)) return i;
    }
    return -1;
}

static Color z_game_color(Value value, int line) {
    if (value.type != Z_STRING) z_fail(line, "Expected a named color as text");
    const char *name = value.string;
    if (TextIsEqual(name, "white")) return WHITE;
    if (TextIsEqual(name, "black")) return BLACK;
    if (TextIsEqual(name, "red")) return RED;
    if (TextIsEqual(name, "green")) return GREEN;
    if (TextIsEqual(name, "blue")) return BLUE;
    if (TextIsEqual(name, "yellow")) return YELLOW;
    if (TextIsEqual(name, "orange")) return ORANGE;
    if (TextIsEqual(name, "purple")) return PURPLE;
    if (TextIsEqual(name, "pink")) return PINK;
    if (TextIsEqual(name, "gold")) return GOLD;
    if (TextIsEqual(name, "brown")) return BROWN;
    if (TextIsEqual(name, "lime")) return LIME;
    if (TextIsEqual(name, "maroon")) return MAROON;
    if (TextIsEqual(name, "skyblue")) return SKYBLUE;
    if (TextIsEqual(name, "gray") || TextIsEqual(name, "grey")) return GRAY;
    if (TextIsEqual(name, "lightgray") || TextIsEqual(name, "lightgrey")) return LIGHTGRAY;
    if (TextIsEqual(name, "darkgray") || TextIsEqual(name, "darkgrey")) return DARKGRAY;
    if (TextIsEqual(name, "raywhite")) return RAYWHITE;
    if (TextIsEqual(name, "blank")) return BLANK;
    z_fail(line, "Unknown color name");
    return BLANK;
}

static int z_game_voxel_block(const ZCollection *blocks, int width, int height,
                              int depth, int x, int y, int z) {
    if (x < 0 || x >= width || y < 0 || y >= height || z < 0 || z >= depth)
        return 0;
    size_t index = (size_t)x + (size_t)width *
            ((size_t)z + (size_t)depth * (size_t)y);
    return (int)blocks->items[index].number;
}

static void z_game_voxel_face(float x, float y, float z, float half, int face) {
    Vector3 a, b, c, d;
    switch (face) {
        case 0:
            a = (Vector3){ x - half, y - half, z - half };
            b = (Vector3){ x - half, y - half, z + half };
            c = (Vector3){ x - half, y + half, z + half };
            d = (Vector3){ x - half, y + half, z - half };
            break;
        case 1:
            a = (Vector3){ x + half, y - half, z + half };
            b = (Vector3){ x + half, y - half, z - half };
            c = (Vector3){ x + half, y + half, z - half };
            d = (Vector3){ x + half, y + half, z + half };
            break;
        case 2:
            a = (Vector3){ x - half, y - half, z + half };
            b = (Vector3){ x + half, y - half, z + half };
            c = (Vector3){ x + half, y - half, z - half };
            d = (Vector3){ x - half, y - half, z - half };
            break;
        case 3:
            a = (Vector3){ x - half, y + half, z - half };
            b = (Vector3){ x + half, y + half, z - half };
            c = (Vector3){ x + half, y + half, z + half };
            d = (Vector3){ x - half, y + half, z + half };
            break;
        case 4:
            a = (Vector3){ x + half, y - half, z - half };
            b = (Vector3){ x - half, y - half, z - half };
            c = (Vector3){ x - half, y + half, z - half };
            d = (Vector3){ x + half, y + half, z - half };
            break;
        default:
            a = (Vector3){ x - half, y - half, z + half };
            b = (Vector3){ x + half, y - half, z + half };
            c = (Vector3){ x + half, y + half, z + half };
            d = (Vector3){ x - half, y + half, z + half };
            break;
    }
    rlVertex3f(a.x, a.y, a.z);
    rlVertex3f(b.x, b.y, b.z);
    rlVertex3f(c.x, c.y, c.z);
    rlVertex3f(a.x, a.y, a.z);
    rlVertex3f(c.x, c.y, c.z);
    rlVertex3f(d.x, d.y, d.z);
}

static int z_game_voxel_dimensions(double value, int line) {
    if (!isfinite(value) || floor(value) != value || value < 1 || value > 2147483647.0)
        z_fail(line, "Voxel world dimensions must be positive whole numbers");
    return (int)value;
}

static void z_game_draw_voxel_world(Value *args, int argc, int line) {
    if (argc != 8 || args[0].type != Z_LIST || !args[0].collection)
        z_fail(line, "draw_voxel_world expects a block list, dimensions, and four colors");
    int width = z_game_voxel_dimensions(z_game_num(args, 1, line), line);
    int height = z_game_voxel_dimensions(z_game_num(args, 2, line), line);
    int depth = z_game_voxel_dimensions(z_game_num(args, 3, line), line);
    if ((size_t)width > SIZE_MAX / (size_t)depth ||
            (size_t)width * (size_t)depth > SIZE_MAX / (size_t)height)
        z_fail(line, "Voxel world dimensions are too large");
    size_t count = (size_t)width * (size_t)depth * (size_t)height;
    ZCollection *blocks = args[0].collection;
    if (blocks->length != count)
        z_fail(line, "Voxel block list length does not match its dimensions");

    Color colors[5] = {
        BLANK,
        z_game_color(args[4], line),
        z_game_color(args[5], line),
        z_game_color(args[6], line),
        z_game_color(args[7], line)
    };
    for (size_t i = 0; i < count; ++i) {
        Value block = blocks->items[i];
        if (block.type != Z_NUMBER || !isfinite(block.number) ||
                floor(block.number) != block.number || block.number < 0 || block.number > 4)
            z_fail(line, "Voxel block IDs must be whole numbers from 0 to 4");
    }

    double render_distance_squared =
        z_voxel_render_distance * z_voxel_render_distance;
    rlBegin(RL_TRIANGLES);
    for (int y = 0; y < height; ++y) {
        for (int z = 0; z < depth; ++z) {
            for (int x = 0; x < width; ++x) {
                int block = z_game_voxel_block(blocks, width, height, depth, x, y, z);
                if (!block) continue;
                Color color = colors[block];
                float world_x = (float)x - (float)(width - 1) * 0.5f;
                float world_y = (float)y - (float)(height - 1) * 0.5f;
                float world_z = (float)z - (float)(depth - 1) * 0.5f;
                double dx = (double)world_x - z_camera.position.x;
                double dy = (double)world_y - z_camera.position.y;
                double dz = (double)world_z - z_camera.position.z;
                if (dx * dx + dy * dy + dz * dz > render_distance_squared)
                    continue;
                rlColor4ub(color.r, color.g, color.b, color.a);
                for (int face = 0; face < 6; ++face) {
                    int nx = x, ny = y, nz = z;
                    if (face == 0) --nx;
                    else if (face == 1) ++nx;
                    else if (face == 2) --ny;
                    else if (face == 3) ++ny;
                    else if (face == 4) --nz;
                    else ++nz;
                    if (!z_game_voxel_block(blocks, width, height, depth, nx, ny, nz))
                        z_game_voxel_face(world_x, world_y, world_z, 0.5f, face);
                }
            }
        }
    }
    rlEnd();
}

static int z_game_key(const char *name, int line) {
    if (TextIsEqual(name, "space")) return KEY_SPACE;
    if (TextIsEqual(name, "escape")) return KEY_ESCAPE;
    if (TextIsEqual(name, "enter")) return KEY_ENTER;
    if (TextIsEqual(name, "tab")) return KEY_TAB;
    if (TextIsEqual(name, "backspace")) return KEY_BACKSPACE;
    if (TextIsEqual(name, "left")) return KEY_LEFT;
    if (TextIsEqual(name, "right")) return KEY_RIGHT;
    if (TextIsEqual(name, "up")) return KEY_UP;
    if (TextIsEqual(name, "down")) return KEY_DOWN;
    if (TextIsEqual(name, "a")) return KEY_A;
    if (TextIsEqual(name, "b")) return KEY_B;
    if (TextIsEqual(name, "c")) return KEY_C;
    if (TextIsEqual(name, "d")) return KEY_D;
    if (TextIsEqual(name, "e")) return KEY_E;
    if (TextIsEqual(name, "f")) return KEY_F;
    if (TextIsEqual(name, "g")) return KEY_G;
    if (TextIsEqual(name, "h")) return KEY_H;
    if (TextIsEqual(name, "i")) return KEY_I;
    if (TextIsEqual(name, "j")) return KEY_J;
    if (TextIsEqual(name, "k")) return KEY_K;
    if (TextIsEqual(name, "l")) return KEY_L;
    if (TextIsEqual(name, "m")) return KEY_M;
    if (TextIsEqual(name, "n")) return KEY_N;
    if (TextIsEqual(name, "o")) return KEY_O;
    if (TextIsEqual(name, "p")) return KEY_P;
    if (TextIsEqual(name, "q")) return KEY_Q;
    if (TextIsEqual(name, "r")) return KEY_R;
    if (TextIsEqual(name, "s")) return KEY_S;
    if (TextIsEqual(name, "t")) return KEY_T;
    if (TextIsEqual(name, "u")) return KEY_U;
    if (TextIsEqual(name, "v")) return KEY_V;
    if (TextIsEqual(name, "w")) return KEY_W;
    if (TextIsEqual(name, "x")) return KEY_X;
    if (TextIsEqual(name, "y")) return KEY_Y;
    if (TextIsEqual(name, "z")) return KEY_Z;
    if (TextIsEqual(name, "0")) return KEY_ZERO;
    if (TextIsEqual(name, "1")) return KEY_ONE;
    if (TextIsEqual(name, "2")) return KEY_TWO;
    if (TextIsEqual(name, "3")) return KEY_THREE;
    if (TextIsEqual(name, "4")) return KEY_FOUR;
    if (TextIsEqual(name, "5")) return KEY_FIVE;
    if (TextIsEqual(name, "6")) return KEY_SIX;
    if (TextIsEqual(name, "7")) return KEY_SEVEN;
    if (TextIsEqual(name, "8")) return KEY_EIGHT;
    if (TextIsEqual(name, "9")) return KEY_NINE;
    z_fail(line, "Unknown key name");
    return KEY_NULL;
}

static int z_game_socket_handle(int line) {
    for (int i = 0; i < Z_GAME_MAX_HANDLES; ++i) {
        if (!z_socket_used[i]) return i;
    }
    z_fail(line, "Maximum number of game network sockets reached");
    return -1;
}

static Value z_game(int id, int argc, Value *args, int line) {
    switch (id) {
        case Z_GAME_INIT_WINDOW:
            if (z_window_open) z_fail(line, "A game window is already open");
            InitWindow((int)z_game_num(args, 0, line), (int)z_game_num(args, 1, line),
                       z_game_str(args, 2, line));
            z_window_open = true;
            SetTargetFPS(60);
            return z_none();
        case Z_GAME_CLOSE_WINDOW:
            if (z_window_open) {
                for (int i = 0; i < Z_GAME_MAX_HANDLES; ++i) {
                    if (z_texture_loaded[i]) {
                        UnloadTexture(z_textures[i]);
                        free(z_texture_paths[i]);
                        z_texture_paths[i] = NULL;
                        z_texture_loaded[i] = false;
                    }
                }
                CloseWindow();
                z_window_open = false;
            }
            return z_none();
        case Z_GAME_WINDOW_SHOULD_CLOSE:
            return z_bool(!z_window_open || WindowShouldClose());
        case Z_GAME_FRAME_TIME:
            return z_game_number(GetFrameTime());
        case Z_GAME_SET_TARGET_FPS:
            SetTargetFPS((int)z_game_num(args, 0, line));
            return z_none();
        case Z_GAME_BEGIN_DRAWING:
            z_game_refresh_textures();
            BeginDrawing();
            return z_none();
        case Z_GAME_END_DRAWING:
            EndDrawing();
            return z_none();
        case Z_GAME_CLEAR_BACKGROUND:
            ClearBackground(z_game_color(args[0], line));
            return z_none();
        case Z_GAME_DRAW_RECTANGLE:
            DrawRectangle((int)z_game_num(args, 0, line), (int)z_game_num(args, 1, line),
                          (int)z_game_num(args, 2, line), (int)z_game_num(args, 3, line),
                          z_game_color(args[4], line));
            return z_none();
        case Z_GAME_DRAW_CIRCLE:
            DrawCircle((int)z_game_num(args, 0, line), (int)z_game_num(args, 1, line),
                       (float)z_game_num(args, 2, line), z_game_color(args[3], line));
            return z_none();
        case Z_GAME_DRAW_LINE:
            DrawLine((int)z_game_num(args, 0, line), (int)z_game_num(args, 1, line),
                     (int)z_game_num(args, 2, line), (int)z_game_num(args, 3, line),
                     z_game_color(args[4], line));
            return z_none();
        case Z_GAME_DRAW_TEXT:
            DrawText(z_game_str(args, 0, line), (int)z_game_num(args, 1, line),
                     (int)z_game_num(args, 2, line), (int)z_game_num(args, 3, line),
                     z_game_color(args[4], line));
            return z_none();
        case Z_GAME_UI_PANEL: {
            double x = z_game_num(args, 0, line);
            double y = z_game_num(args, 1, line);
            double width = z_game_num(args, 2, line);
            double height = z_game_num(args, 3, line);
            if (!isfinite(x) || !isfinite(y) || !isfinite(width) ||
                !isfinite(height) || !isfinite((float)x) || !isfinite((float)y) ||
                !isfinite((float)width) || !isfinite((float)height) ||
                width <= 0 || height <= 0)
                z_fail(line, "UI panel geometry must be finite with positive dimensions");
            Rectangle bounds = { (float)x, (float)y, (float)width, (float)height };
            DrawRectangleRec(bounds, (Color){ 24, 28, 38, 235 });
            DrawRectangleLinesEx(bounds, 1, (Color){ 92, 104, 126, 255 });
            const char *title = z_game_str(args, 4, line);
            if (title[0]) DrawText(title, (int)x + 12, (int)y + 10, 20, RAYWHITE);
            return z_none();
        }
        case Z_GAME_UI_LABEL: {
            double x = z_game_num(args, 0, line);
            double y = z_game_num(args, 1, line);
            double raw_size = z_game_num(args, 3, line);
            if (!isfinite(x) || !isfinite(y) || !isfinite(raw_size) ||
                !isfinite((float)x) || !isfinite((float)y) ||
                raw_size < 1 || raw_size > 256)
                z_fail(line, "UI label position and font size are invalid");
            DrawText(z_game_str(args, 2, line), (int)x, (int)y, (int)raw_size,
                     z_game_color(args[4], line));
            return z_none();
        }
        case Z_GAME_UI_BUTTON: {
            double x = z_game_num(args, 0, line);
            double y = z_game_num(args, 1, line);
            double width = z_game_num(args, 2, line);
            double height = z_game_num(args, 3, line);
            if (!isfinite(x) || !isfinite(y) || !isfinite(width) ||
                !isfinite(height) || !isfinite((float)x) || !isfinite((float)y) ||
                !isfinite((float)width) || !isfinite((float)height) ||
                width <= 0 || height <= 0)
                z_fail(line, "UI button geometry must be finite with positive dimensions");
            Rectangle bounds = { (float)x, (float)y, (float)width, (float)height };
            bool hovered = CheckCollisionPointRec(GetMousePosition(), bounds);
            bool clicked = hovered && IsMouseButtonPressed(MOUSE_BUTTON_LEFT);
            DrawRectangleRec(bounds, clicked ? (Color){ 61, 110, 178, 255 }
                                  : hovered ? (Color){ 70, 82, 104, 255 }
                                            : (Color){ 48, 57, 74, 255 });
            DrawRectangleLinesEx(bounds, 1, hovered ? SKYBLUE : GRAY);
            const char *label = z_game_str(args, 4, line);
            int font_size = 18;
            int text_width = MeasureText(label, font_size);
            DrawText(label, (int)(x + fmax(8, (width - text_width) * 0.5)),
                     (int)(y + fmax(4, (height - font_size) * 0.5)),
                     font_size, RAYWHITE);
            return z_bool(clicked);
        }
        case Z_GAME_UI_CHECKBOX: {
            double x = z_game_num(args, 0, line);
            double y = z_game_num(args, 1, line);
            const char *label = z_game_str(args, 2, line);
            if (args[3].type != Z_BOOLEAN)
                z_fail(line, "UI checkbox state must be boolean");
            if (!isfinite(x) || !isfinite(y) ||
                !isfinite((float)x) || !isfinite((float)y))
                z_fail(line, "UI checkbox position must be finite");
            Rectangle bounds = { (float)x, (float)y, 22, 22 };
            bool hovered = CheckCollisionPointRec(GetMousePosition(), bounds);
            bool value = args[3].number != 0;
            bool clicked = hovered && IsMouseButtonPressed(MOUSE_BUTTON_LEFT);
            if (clicked) value = !value;
            DrawRectangleRec(bounds, value ? SKYBLUE : (Color){ 48, 57, 74, 255 });
            DrawRectangleLinesEx(bounds, 1, hovered ? RAYWHITE : GRAY);
            DrawText(label, (int)x + 32, (int)y + 2, 18, RAYWHITE);
            return z_bool(value);
        }
        case Z_GAME_UI_PROGRESS_BAR: {
            double x = z_game_num(args, 0, line);
            double y = z_game_num(args, 1, line);
            double width = z_game_num(args, 2, line);
            double height = z_game_num(args, 3, line);
            double value = z_game_num(args, 4, line);
            double maximum = z_game_num(args, 5, line);
            if (!isfinite(x) || !isfinite(y) || !isfinite(width) ||
                !isfinite(height) || !isfinite(value) || !isfinite(maximum) ||
                !isfinite((float)x) || !isfinite((float)y) ||
                !isfinite((float)width) || !isfinite((float)height) ||
                width <= 0 || height <= 0 || maximum <= 0)
                z_fail(line, "UI progress-bar geometry and maximum must be finite and positive");
            Rectangle bounds = { (float)x, (float)y, (float)width, (float)height };
            DrawRectangleRec(bounds, (Color){ 48, 57, 74, 255 });
            float ratio = (float)fmax(0, fmin(1, value / maximum));
            if (ratio > 0) {
                Rectangle fill = bounds;
                fill.width *= ratio;
                DrawRectangleRec(fill, z_game_color(args[6], line));
            }
            DrawRectangleLinesEx(bounds, 1, GRAY);
            return z_none();
        }
        case Z_GAME_SET_CAMERA_3D: {
            double values[6];
            for (int i = 0; i < 6; ++i) {
                values[i] = z_game_num(args, i, line);
                if (!isfinite(values[i]) || !isfinite((float)values[i]))
                    z_fail(line, "3D camera coordinates must be finite");
            }
            z_camera.position = (Vector3){
                (float)values[0], (float)values[1], (float)values[2]
            };
            z_camera.target = (Vector3){
                (float)values[3], (float)values[4], (float)values[5]
            };
            z_camera.up = (Vector3){ 0.0f, 1.0f, 0.0f };
            z_camera.fovy = 45.0f;
            z_camera.projection = CAMERA_PERSPECTIVE;
            z_camera_3d_initialized = true;
            return z_none();
        }
        case Z_GAME_BEGIN_3D:
            if (!z_camera_3d_initialized) {
                z_camera.position = (Vector3){ 8.0f, 8.0f, 8.0f };
                z_camera.target = (Vector3){ 0.0f, 0.0f, 0.0f };
                z_camera.up = (Vector3){ 0.0f, 1.0f, 0.0f };
                z_camera.fovy = 45.0f;
                z_camera.projection = CAMERA_PERSPECTIVE;
                z_camera_3d_initialized = true;
            }
            BeginMode3D(z_camera);
            return z_none();
        case Z_GAME_END_3D:
            EndMode3D();
            return z_none();
        case Z_GAME_DRAW_CUBE: {
            Vector3 position = {
                (float)z_game_num(args, 0, line), (float)z_game_num(args, 1, line),
                (float)z_game_num(args, 2, line)
            };
            float size = (float)z_game_num(args, 3, line);
            DrawCube(position, size, size, size, z_game_color(args[4], line));
            return z_none();
        }
        case Z_GAME_DRAW_VOXEL_FACE: {
            float x = (float)z_game_num(args, 0, line);
            float y = (float)z_game_num(args, 1, line);
            float z = (float)z_game_num(args, 2, line);
            float half = (float)z_game_num(args, 3, line) * 0.5f;
            const char *face = z_game_str(args, 4, line);
            Vector3 a, b, c, d;
            if (TextIsEqual(face, "top")) {
                a = (Vector3){ x - half, y + half, z - half };
                b = (Vector3){ x + half, y + half, z - half };
                c = (Vector3){ x + half, y + half, z + half };
                d = (Vector3){ x - half, y + half, z + half };
            } else if (TextIsEqual(face, "bottom")) {
                a = (Vector3){ x - half, y - half, z + half };
                b = (Vector3){ x + half, y - half, z + half };
                c = (Vector3){ x + half, y - half, z - half };
                d = (Vector3){ x - half, y - half, z - half };
            } else if (TextIsEqual(face, "left")) {
                a = (Vector3){ x - half, y - half, z - half };
                b = (Vector3){ x - half, y - half, z + half };
                c = (Vector3){ x - half, y + half, z + half };
                d = (Vector3){ x - half, y + half, z - half };
            } else if (TextIsEqual(face, "right")) {
                a = (Vector3){ x + half, y - half, z + half };
                b = (Vector3){ x + half, y - half, z - half };
                c = (Vector3){ x + half, y + half, z - half };
                d = (Vector3){ x + half, y + half, z + half };
            } else if (TextIsEqual(face, "front")) {
                a = (Vector3){ x - half, y - half, z + half };
                b = (Vector3){ x + half, y - half, z + half };
                c = (Vector3){ x + half, y + half, z + half };
                d = (Vector3){ x - half, y + half, z + half };
            } else if (TextIsEqual(face, "back")) {
                a = (Vector3){ x + half, y - half, z - half };
                b = (Vector3){ x - half, y - half, z - half };
                c = (Vector3){ x - half, y + half, z - half };
                d = (Vector3){ x + half, y + half, z - half };
            } else {
                z_fail(line, "Voxel face must be top, bottom, left, right, front, or back");
                return z_none();
            }
            Color color = z_game_color(args[5], line);
            DrawTriangle3D(a, b, c, color);
            DrawTriangle3D(a, c, d, color);
            return z_none();
        }
        case Z_GAME_DRAW_VOXEL_WORLD:
            z_game_draw_voxel_world(args, argc, line);
            return z_none();
        case Z_GAME_SET_VOXEL_RENDER_DISTANCE: {
            double distance = z_game_num(args, 0, line);
            if (!isfinite(distance) || distance <= 0 || distance > 4096)
                z_fail(line, "Voxel render distance must be finite and between 0 and 4096");
            z_voxel_render_distance = distance;
            return z_none();
        }
        case Z_GAME_DISTANCE_3D: {
            double dx = z_game_num(args, 0, line) - z_game_num(args, 3, line);
            double dy = z_game_num(args, 1, line) - z_game_num(args, 4, line);
            double dz = z_game_num(args, 2, line) - z_game_num(args, 5, line);
            double distance = sqrt(dx * dx + dy * dy + dz * dz);
            if (!isfinite(distance)) z_fail(line, "3D distance is not finite");
            return z_game_number(distance);
        }
        case Z_GAME_DRAW_SPHERE:
            DrawSphere((Vector3){ (float)z_game_num(args, 0, line),
                                  (float)z_game_num(args, 1, line),
                                  (float)z_game_num(args, 2, line) },
                       (float)z_game_num(args, 3, line), z_game_color(args[4], line));
            return z_none();
        case Z_GAME_KEY_PRESSED:
            return z_bool(IsKeyPressed(z_game_key(z_game_str(args, 0, line), line)));
        case Z_GAME_KEY_DOWN:
            return z_bool(IsKeyDown(z_game_key(z_game_str(args, 0, line), line)));
        case Z_GAME_KEY_RELEASED:
            return z_bool(IsKeyReleased(z_game_key(z_game_str(args, 0, line), line)));
        case Z_GAME_MOUSE_X:
            return z_game_number(GetMouseX());
        case Z_GAME_MOUSE_Y:
            return z_game_number(GetMouseY());
        case Z_GAME_MOUSE_BUTTON_PRESSED: {
            const char *name = z_game_str(args, 0, line);
            int button = MOUSE_BUTTON_LEFT;
            if (TextIsEqual(name, "right")) button = MOUSE_BUTTON_RIGHT;
            else if (TextIsEqual(name, "middle")) button = MOUSE_BUTTON_MIDDLE;
            else if (TextIsEqual(name, "left")) button = MOUSE_BUTTON_LEFT;
            else z_fail(line, "Unknown mouse button");
            return z_bool(IsMouseButtonPressed(button));
        }
        case Z_GAME_MOUSE_WHEEL:
            return z_game_number(GetMouseWheelMove());
        case Z_GAME_MOUSE_BUTTON_DOWN:
        case Z_GAME_MOUSE_BUTTON_RELEASED: {
            const char *name = z_game_str(args, 0, line);
            int button = MOUSE_BUTTON_LEFT;
            if (TextIsEqual(name, "right")) button = MOUSE_BUTTON_RIGHT;
            else if (TextIsEqual(name, "middle")) button = MOUSE_BUTTON_MIDDLE;
            else if (!TextIsEqual(name, "left")) z_fail(line, "Unknown mouse button");
            return z_bool(id == Z_GAME_MOUSE_BUTTON_DOWN
                ? IsMouseButtonDown(button) : IsMouseButtonReleased(button));
        }
        case Z_GAME_MOUSE_WORLD_X:
        case Z_GAME_MOUSE_WORLD_Y: {
            Vector2 mouse = GetScreenToWorld2D(GetMousePosition(), z_camera_2d);
            return z_game_number(id == Z_GAME_MOUSE_WORLD_X ? mouse.x : mouse.y);
        }
        case Z_GAME_SET_CAMERA_2D:
            z_camera_2d.target = (Vector2){
                (float)z_game_num(args, 0, line), (float)z_game_num(args, 1, line)
            };
            z_camera_2d.offset = (Vector2){
                (float)z_game_num(args, 2, line), (float)z_game_num(args, 3, line)
            };
            z_camera_2d.zoom = (float)z_game_num(args, 4, line);
            z_camera_2d.rotation = (float)z_game_num(args, 5, line);
            if (!isfinite(z_camera_2d.zoom) || z_camera_2d.zoom <= 0)
                z_fail(line, "2D camera zoom must be positive");
            return z_none();
        case Z_GAME_BEGIN_CAMERA_2D:
            if (z_camera_2d_active) z_fail(line, "A 2D camera is already active");
            BeginMode2D(z_camera_2d);
            z_camera_2d_active = true;
            return z_none();
        case Z_GAME_END_CAMERA_2D:
            if (!z_camera_2d_active) z_fail(line, "No 2D camera is active");
            EndMode2D();
            z_camera_2d_active = false;
            return z_none();
        case Z_GAME_LOAD_TEXTURE: {
            const char *path = z_game_asset_path(z_game_str(args, 0, line), line);
            for (int i = 0; i < Z_GAME_MAX_HANDLES; ++i) {
                if (!z_texture_loaded[i]) {
                    Texture2D texture = LoadTexture(path);
                    if (texture.id == 0 || texture.width <= 0 || texture.height <= 0)
                        z_fail(line, "Could not load texture asset");
                    z_textures[i] = texture;
                    z_texture_paths[i] = z_copy(path);
                    z_texture_modified[i] = GetFileModTime(path);
                    z_texture_loaded[i] = true;
                    return z_game_number(i);
                }
            }
            z_fail(line, "Maximum number of loaded textures reached");
            return z_none();
        }
        case Z_GAME_UNLOAD_TEXTURE: {
            int handle = z_game_texture_handle(args, 0, line);
            UnloadTexture(z_textures[handle]);
            free(z_texture_paths[handle]);
            z_texture_paths[handle] = NULL;
            z_texture_loaded[handle] = false;
            return z_none();
        }
        case Z_GAME_DRAW_SPRITE: {
            int handle = z_game_texture_handle(args, 0, line);
            DrawTexture(z_textures[handle], (int)z_game_num(args, 1, line),
                        (int)z_game_num(args, 2, line), WHITE);
            return z_none();
        }
        case Z_GAME_DRAW_SPRITE_EX: {
            int handle = z_game_texture_handle(args, 0, line);
            float scale = (float)z_game_num(args, 4, line);
            double alpha = z_game_num(args, 5, line);
            if (!isfinite(scale) || scale <= 0) z_fail(line, "Sprite scale must be positive");
            if (!isfinite(alpha) || alpha < 0 || alpha > 255)
                z_fail(line, "Sprite alpha must be between 0 and 255");
            DrawTextureEx(z_textures[handle],
                (Vector2){ (float)z_game_num(args, 1, line), (float)z_game_num(args, 2, line) },
                (float)z_game_num(args, 3, line), scale,
                (Color){ 255, 255, 255, (unsigned char)alpha });
            return z_none();
        }
        case Z_GAME_TEXTURE_WIDTH:
        case Z_GAME_TEXTURE_HEIGHT: {
            int handle = z_game_texture_handle(args, 0, line);
            return z_game_number(id == Z_GAME_TEXTURE_WIDTH
                ? z_textures[handle].width : z_textures[handle].height);
        }
        case Z_GAME_ENABLE_ASSET_HOT_RELOAD:
            z_asset_hot_reload = true;
            return z_none();
        case Z_GAME_CREATE_ANIMATION: {
            int texture = z_game_texture_handle(args, 0, line);
            double width_value = z_game_num(args, 1, line);
            double height_value = z_game_num(args, 2, line);
            double count_value = z_game_num(args, 3, line);
            double fps = z_game_num(args, 4, line);
            if (!isfinite(width_value) || !isfinite(height_value) ||
                !isfinite(count_value) || !isfinite(fps) ||
                floor(width_value) != width_value || floor(height_value) != height_value ||
                floor(count_value) != count_value || width_value <= 0 ||
                height_value <= 0 || count_value <= 0 || fps <= 0 || fps > 1000 ||
                width_value > z_textures[texture].width ||
                height_value > z_textures[texture].height ||
                count_value > (double)z_textures[texture].width * z_textures[texture].height)
                z_fail(line, "Animation parameters must fit the sprite sheet and use a valid FPS");
            int width = (int)width_value;
            int height = (int)height_value;
            int frame_count = (int)count_value;
            int columns = z_textures[texture].width / width;
            int rows = z_textures[texture].height / height;
            if (columns * rows < frame_count)
                z_fail(line, "Animation frames exceed the texture sprite sheet");
            for (int i = 0; i < Z_GAME_MAX_HANDLES; ++i) {
                if (!z_animation_active[i]) {
                    z_animation_active[i] = true;
                    z_animation_texture[i] = texture;
                    z_animation_frame_width[i] = width;
                    z_animation_frame_height[i] = height;
                    z_animation_frame_count[i] = frame_count;
                    z_animation_fps[i] = fps;
                    z_animation_looping[i] = true;
                    z_game_reset_animation(i);
                    return z_game_number(i);
                }
            }
            z_fail(line, "Maximum number of animations reached");
            return z_none();
        }
        case Z_GAME_UPDATE_ANIMATION: {
            int animation = z_game_animation_handle(args, 0, line);
            z_game_update_animation(animation, z_game_num(args, 1, line), line);
            return z_none();
        }
        case Z_GAME_DRAW_ANIMATION: {
            int animation = z_game_animation_handle(args, 0, line);
            int texture = z_animation_texture[animation];
            int columns = z_textures[texture].width / z_animation_frame_width[animation];
            int frame = z_animation_frame[animation];
            Rectangle source = {
                (float)((frame % columns) * z_animation_frame_width[animation]),
                (float)((frame / columns) * z_animation_frame_height[animation]),
                (float)z_animation_frame_width[animation],
                (float)z_animation_frame_height[animation]
            };
            float scale = (float)z_game_num(args, 3, line);
            if (!isfinite(scale) || scale <= 0) z_fail(line, "Animation scale must be positive");
            Rectangle destination = {
                (float)z_game_num(args, 1, line), (float)z_game_num(args, 2, line),
                source.width * scale, source.height * scale
            };
            DrawTexturePro(z_textures[texture], source, destination,
                (Vector2){ 0, 0 }, 0, WHITE);
            return z_none();
        }
        case Z_GAME_SET_ANIMATION_LOOPING: {
            int animation = z_game_animation_handle(args, 0, line);
            z_animation_looping[animation] = z_game_num(args, 1, line) != 0;
            return z_none();
        }
        case Z_GAME_ANIMATION_FRAME: {
            int animation = z_game_animation_handle(args, 0, line);
            return z_game_number(z_animation_frame[animation]);
        }
        case Z_GAME_CREATE_ANIMATION_MACHINE:
            for (int i = 0; i < Z_GAME_MAX_HANDLES; ++i) {
                if (!z_animation_machines[i].active) {
                    memset(&z_animation_machines[i], 0, sizeof z_animation_machines[i]);
                    z_animation_machines[i].active = true;
                    z_animation_machines[i].active_state = -1;
                    return z_game_number(i);
                }
            }
            z_fail(line, "Maximum number of animation machines reached");
            return z_none();
        case Z_GAME_ADD_ANIMATION_STATE: {
            int machine = z_game_machine_handle(args, 0, line);
            const char *name = z_game_str(args, 1, line);
            int animation = z_game_animation_handle(args, 2, line);
            ZAnimationMachine *value = &z_animation_machines[machine];
            if (!name[0] || strlen(name) >= sizeof value->states[0].name)
                z_fail(line, "Animation state names must contain 1 to 63 characters");
            if (z_game_animation_state(machine, name) >= 0)
                z_fail(line, "Animation state already exists");
            if (value->state_count == Z_GAME_MAX_ANIMATION_STATES)
                z_fail(line, "Animation machine has too many states");
            ZAnimationState *state = &value->states[value->state_count++];
            strcpy(state->name, name);
            state->animation = animation;
            if (value->active_state < 0) value->active_state = 0;
            return z_none();
        }
        case Z_GAME_ADD_ANIMATION_TRANSITION: {
            int machine = z_game_machine_handle(args, 0, line);
            const char *from = z_game_str(args, 1, line);
            const char *event = z_game_str(args, 2, line);
            const char *to = z_game_str(args, 3, line);
            ZAnimationMachine *value = &z_animation_machines[machine];
            if (z_game_animation_state(machine, from) < 0 ||
                z_game_animation_state(machine, to) < 0)
                z_fail(line, "Animation transition refers to an unknown state");
            if (!event[0] || strlen(from) >= 64 || strlen(event) >= 64 || strlen(to) >= 64)
                z_fail(line, "Animation state and event names must contain 1 to 63 characters");
            if (value->transition_count == Z_GAME_MAX_ANIMATION_TRANSITIONS)
                z_fail(line, "Animation machine has too many transitions");
            for (int i = 0; i < value->transition_count; ++i) {
                ZAnimationTransition *existing = &value->transitions[i];
                if (TextIsEqual(existing->from, from) && TextIsEqual(existing->event, event))
                    z_fail(line, "Animation transition already exists");
            }
            ZAnimationTransition *transition = &value->transitions[value->transition_count++];
            strcpy(transition->from, from);
            strcpy(transition->event, event);
            strcpy(transition->to, to);
            return z_none();
        }
        case Z_GAME_SET_ANIMATION_STATE: {
            int machine = z_game_machine_handle(args, 0, line);
            int state = z_game_animation_state(machine, z_game_str(args, 1, line));
            if (state < 0) z_fail(line, "Unknown animation state");
            ZAnimationMachine *value = &z_animation_machines[machine];
            value->active_state = state;
            z_game_reset_animation(value->states[state].animation);
            return z_none();
        }
        case Z_GAME_TRIGGER_ANIMATION_EVENT: {
            int machine = z_game_machine_handle(args, 0, line);
            const char *event = z_game_str(args, 1, line);
            ZAnimationMachine *value = &z_animation_machines[machine];
            if (value->active_state < 0) z_fail(line, "Animation machine has no active state");
            const char *current = value->states[value->active_state].name;
            for (int i = 0; i < value->transition_count; ++i) {
                ZAnimationTransition *transition = &value->transitions[i];
                if (TextIsEqual(transition->from, current) &&
                    TextIsEqual(transition->event, event)) {
                    value->active_state = z_game_animation_state(machine, transition->to);
                    z_game_reset_animation(value->states[value->active_state].animation);
                    return z_bool(true);
                }
            }
            return z_bool(false);
        }
        case Z_GAME_UPDATE_ANIMATION_MACHINE: {
            int machine = z_game_machine_handle(args, 0, line);
            ZAnimationMachine *value = &z_animation_machines[machine];
            if (value->active_state < 0) z_fail(line, "Animation machine has no active state");
            z_game_update_animation(
                value->states[value->active_state].animation,
                z_game_num(args, 1, line), line);
            return z_none();
        }
        case Z_GAME_DRAW_ANIMATION_MACHINE: {
            int machine = z_game_machine_handle(args, 0, line);
            ZAnimationMachine *value = &z_animation_machines[machine];
            if (value->active_state < 0) z_fail(line, "Animation machine has no active state");
            Value animation_args[1] = {
                z_game_number(value->states[value->active_state].animation)
            };
            int animation = z_game_animation_handle(animation_args, 0, line);
            int texture = z_animation_texture[animation];
            int columns = z_textures[texture].width / z_animation_frame_width[animation];
            int frame = z_animation_frame[animation];
            Rectangle source = {
                (float)((frame % columns) * z_animation_frame_width[animation]),
                (float)((frame / columns) * z_animation_frame_height[animation]),
                (float)z_animation_frame_width[animation],
                (float)z_animation_frame_height[animation]
            };
            float scale = (float)z_game_num(args, 3, line);
            if (!isfinite(scale) || scale <= 0) z_fail(line, "Animation scale must be positive");
            Rectangle destination = {
                (float)z_game_num(args, 1, line), (float)z_game_num(args, 2, line),
                source.width * scale, source.height * scale
            };
            DrawTexturePro(z_textures[texture], source, destination,
                (Vector2){ 0, 0 }, 0, WHITE);
            return z_none();
        }
        case Z_GAME_INIT_AUDIO:
            if (!z_audio_open) {
                InitAudioDevice();
                if (!IsAudioDeviceReady()) z_fail(line, "Could not initialize audio");
                z_audio_open = true;
            }
            return z_none();
        case Z_GAME_LOAD_SOUND: {
            if (!z_audio_open) z_fail(line, "Call init_audio before loading sounds");
            for (int i = 0; i < Z_GAME_MAX_HANDLES; ++i) {
                if (!z_sound_loaded[i]) {
                    const char *path = z_game_asset_path(z_game_str(args, 0, line), line);
                    Sound sound = LoadSound(path);
                    if (sound.frameCount == 0) z_fail(line, "Could not load sound file");
                    z_sounds[i] = sound;
                    z_sound_loaded[i] = true;
                    return z_game_number(i);
                }
            }
            z_fail(line, "Maximum number of loaded sounds reached");
            return z_none();
        }
        case Z_GAME_PLAY_SOUND: {
            int handle = z_game_handle(args, 0, Z_GAME_MAX_HANDLES, line, "Invalid sound handle");
            if (!z_sound_loaded[handle]) z_fail(line, "Sound handle is not loaded");
            PlaySound(z_sounds[handle]);
            return z_none();
        }
        case Z_GAME_UNLOAD_SOUND: {
            int handle = z_game_handle(args, 0, Z_GAME_MAX_HANDLES, line, "Invalid sound handle");
            if (!z_sound_loaded[handle]) z_fail(line, "Sound handle is not loaded");
            UnloadSound(z_sounds[handle]);
            z_sound_loaded[handle] = false;
            return z_none();
        }
        case Z_GAME_CLOSE_AUDIO:
            for (int i = 0; i < Z_GAME_MAX_HANDLES; ++i) {
                if (z_sound_loaded[i]) { UnloadSound(z_sounds[i]); z_sound_loaded[i] = false; }
            }
            if (z_audio_open) { CloseAudioDevice(); z_audio_open = false; }
            return z_none();
        case Z_GAME_CREATE_SCENE:
            for (int i = 0; i < Z_GAME_MAX_SCENES; ++i) {
                if (!z_scenes[i].active) {
                    z_scenes[i].active = true;
                    z_scenes[i].count = 0;
                    return z_game_number(i);
                }
            }
            z_fail(line, "Maximum number of scenes reached");
            return z_none();
        case Z_GAME_ACTIVATE_SCENE: {
            int scene = z_game_handle(args, 0, Z_GAME_MAX_SCENES, line, "Invalid scene handle");
            if (!z_scenes[scene].active) z_fail(line, "Scene does not exist");
            z_active_scene = scene;
            return z_none();
        }
        case Z_GAME_CREATE_OBJECT:
            for (int i = 0; i < Z_GAME_MAX_OBJECTS; ++i) {
                if (!z_objects[i].active) {
                    z_objects[i].active = true;
                    z_objects[i].x = (float)z_game_num(args, 0, line);
                    z_objects[i].y = (float)z_game_num(args, 1, line);
                    z_objects[i].width = (float)z_game_num(args, 2, line);
                    z_objects[i].height = (float)z_game_num(args, 3, line);
                    z_objects[i].color = z_game_color(args[4], line);
                    return z_game_number(i);
                }
            }
            z_fail(line, "Maximum number of game objects reached");
            return z_none();
        case Z_GAME_ADD_OBJECT: {
            int scene = z_game_handle(args, 0, Z_GAME_MAX_SCENES, line, "Invalid scene handle");
            int object = z_game_handle(args, 1, Z_GAME_MAX_OBJECTS, line, "Invalid object handle");
            if (!z_scenes[scene].active || !z_objects[object].active)
                z_fail(line, "Cannot add an invalid scene or game object");
            if (z_scenes[scene].count == Z_GAME_MAX_OBJECTS)
                z_fail(line, "Scene is full");
            z_scenes[scene].objects[z_scenes[scene].count++] = object;
            return z_none();
        }
        case Z_GAME_MOVE_OBJECT: {
            int object = z_game_handle(args, 0, Z_GAME_MAX_OBJECTS, line, "Invalid object handle");
            if (!z_objects[object].active) z_fail(line, "Game object does not exist");
            z_objects[object].x += (float)z_game_num(args, 1, line);
            z_objects[object].y += (float)z_game_num(args, 2, line);
            return z_none();
        }
        case Z_GAME_SET_OBJECT_POSITION: {
            int object = z_game_handle(args, 0, Z_GAME_MAX_OBJECTS, line, "Invalid object handle");
            if (!z_objects[object].active) z_fail(line, "Game object does not exist");
            z_objects[object].x = (float)z_game_num(args, 1, line);
            z_objects[object].y = (float)z_game_num(args, 2, line);
            return z_none();
        }
        case Z_GAME_DRAW_SCENE:
            if (z_active_scene < 0 || !z_scenes[z_active_scene].active)
                z_fail(line, "Activate a scene before drawing");
            for (int i = 0; i < z_scenes[z_active_scene].count; ++i) {
                ZGameObject *object = &z_objects[z_scenes[z_active_scene].objects[i]];
                if (object->active) DrawRectangle((int)object->x, (int)object->y,
                    (int)object->width, (int)object->height, object->color);
            }
            return z_none();
        case Z_GAME_CLEAR_SCENE: {
            int scene = z_game_handle(args, 0, Z_GAME_MAX_SCENES, line, "Invalid scene handle");
            if (!z_scenes[scene].active) z_fail(line, "Scene does not exist");
            for (int i = 0; i < z_scenes[scene].count; ++i)
                z_objects[z_scenes[scene].objects[i]].active = false;
            z_scenes[scene].count = 0;
            return z_none();
        }
        case Z_GAME_CREATE_BODY:
            for (int i = 0; i < Z_GAME_MAX_OBJECTS; ++i) {
                if (!z_bodies[i].active) {
                    double x = z_game_num(args, 0, line);
                    double y = z_game_num(args, 1, line);
                    double width = z_game_num(args, 2, line);
                    double height = z_game_num(args, 3, line);
                    double mass = z_game_num(args, 4, line);
                    if (!isfinite(x) || !isfinite(y) || !isfinite(width) ||
                        !isfinite(height) || !isfinite((float)x) ||
                        !isfinite((float)y) || !isfinite((float)width) ||
                        !isfinite((float)height) || width <= 0 || height <= 0)
                        z_fail(line, "Physics body position and dimensions must be finite; dimensions must be positive");
                    if (!isfinite(mass) || !isfinite((float)mass) || mass <= 0)
                        z_fail(line, "Physics body mass must be finite and positive");
                    z_bodies[i] = (ZPhysicsBody){
                        true, (float)x, (float)y, (float)width, (float)height,
                        (float)mass, 0, 0, 0, 0.2f
                    };
                    return z_game_number(i);
                }
            }
            z_fail(line, "Maximum number of physics bodies reached");
            return z_none();
        case Z_GAME_PHYSICS_SET_GRAVITY: {
            double gravity = z_game_num(args, 0, line);
            if (!isfinite(gravity) || !isfinite((float)gravity))
                z_fail(line, "Gravity must be finite");
            z_gravity = (float)gravity;
            z_gravity_3d = (Vector3){ 0, (float)gravity, 0 };
            return z_none();
        }
        case Z_GAME_PHYSICS_SET_GRAVITY_3D: {
            double x = z_game_num(args, 0, line);
            double y = z_game_num(args, 1, line);
            double z = z_game_num(args, 2, line);
            if (!isfinite(x) || !isfinite(y) || !isfinite(z) ||
                !isfinite((float)x) || !isfinite((float)y) ||
                !isfinite((float)z))
                z_fail(line, "3D gravity must be finite");
            z_gravity_3d = (Vector3){ (float)x, (float)y, (float)z };
            return z_none();
        }
        case Z_GAME_PHYSICS_UPDATE: {
            float delta = (float)z_game_num(args, 0, line);
            if (!isfinite(delta) || delta < 0 || delta > 0.25f)
                z_fail(line, "Physics delta must be between 0 and 0.25 seconds");
            int steps = (int)ceilf(delta * 120.0f);
            if (steps < 1) steps = 1;
            float step = delta / (float)steps;
            for (int substep = 0; substep < steps; ++substep) {
                for (int i = 0; i < Z_GAME_MAX_OBJECTS; ++i) {
                    if (!z_bodies[i].active) continue;
                    ZPhysicsBody *body = &z_bodies[i];
                    body->vy += z_gravity * step;
                    body->x += body->vx * step;
                    body->y += body->vy * step;
                }
                for (int i = 0; i < Z_GAME_MAX_OBJECTS; ++i) {
                    if (!z_bodies[i].active) continue;
                    for (int j = i + 1; j < Z_GAME_MAX_OBJECTS; ++j) {
                        if (!z_bodies[j].active) continue;
                        ZPhysicsBody *a = &z_bodies[i], *b = &z_bodies[j];
                        float inv_a = 1.0f / a->mass, inv_b = 1.0f / b->mass;
                        z_game_resolve_aabb(
                            &a->x, &a->y, a->width, a->height, inv_a,
                            &a->vx, &a->vy, a->restitution, a->friction,
                            &b->x, &b->y, b->width, b->height, inv_b,
                            &b->vx, &b->vy, b->restitution, b->friction);
                    }
                }
                for (int i = 0; i < Z_GAME_MAX_ENTITIES; ++i) {
                    if (!z_entities[i].active || !z_transforms[i].active ||
                        !z_rigid_bodies[i].active) continue;
                    ZRigidBody *body = &z_rigid_bodies[i];
                    if (body->mass > 0) {
                        if (z_transforms[i].three_dimensional) {
                            body->vx += (z_gravity_3d.x +
                                         body->force_x / body->mass) * step;
                            body->vy += (z_gravity_3d.y +
                                         body->force_y / body->mass) * step;
                            body->vz += (z_gravity_3d.z +
                                         body->force_z / body->mass) * step;
                        } else {
                            body->vx += (body->force_x / body->mass) * step;
                            body->vy += (z_gravity +
                                         body->force_y / body->mass) * step;
                        }
                        z_transforms[i].x += body->vx * step;
                        z_transforms[i].y += body->vy * step;
                        z_transforms[i].z += body->vz * step;
                    }
                }
                for (int i = 0; i < Z_GAME_MAX_ENTITIES; ++i) {
                    if (!z_entities[i].active || !z_transforms[i].active ||
                        !z_box_colliders[i].active) continue;
                    for (int j = i + 1; j < Z_GAME_MAX_ENTITIES; ++j) {
                        if (!z_entities[j].active || !z_transforms[j].active ||
                            !z_box_colliders[j].active) continue;
                        ZRigidBody *a_body = &z_rigid_bodies[i];
                        ZRigidBody *b_body = &z_rigid_bodies[j];
                        float zero_a_x = 0, zero_a_y = 0, zero_b_x = 0, zero_b_y = 0;
                        float *a_vx = a_body->active ? &a_body->vx : &zero_a_x;
                        float *a_vy = a_body->active ? &a_body->vy : &zero_a_y;
                        float *b_vx = b_body->active ? &b_body->vx : &zero_b_x;
                        float *b_vy = b_body->active ? &b_body->vy : &zero_b_y;
                        float inv_a = a_body->active && a_body->mass > 0
                            ? 1.0f / a_body->mass : 0;
                        float inv_b = b_body->active && b_body->mass > 0
                            ? 1.0f / b_body->mass : 0;
                        ZBoxCollider *a_collider = &z_box_colliders[i];
                        ZBoxCollider *b_collider = &z_box_colliders[j];
                        z_game_resolve_aabb(
                            &z_transforms[i].x, &z_transforms[i].y,
                            a_collider->width, a_collider->height, inv_a,
                            a_vx, a_vy, a_collider->restitution, a_collider->friction,
                            &z_transforms[j].x, &z_transforms[j].y,
                            b_collider->width, b_collider->height, inv_b,
                            b_vx, b_vy, b_collider->restitution, b_collider->friction);
                    }
                }
                for (int i = 0; i < Z_GAME_MAX_ENTITIES; ++i) {
                    if (!z_entities[i].active || !z_transforms[i].active ||
                        !z_box_colliders_3d[i].active) continue;
                    for (int j = i + 1; j < Z_GAME_MAX_ENTITIES; ++j) {
                        if (!z_entities[j].active || !z_transforms[j].active ||
                            !z_box_colliders_3d[j].active) continue;
                        ZRigidBody *a_body = z_rigid_bodies[i].active
                            ? &z_rigid_bodies[i] : NULL;
                        ZRigidBody *b_body = z_rigid_bodies[j].active
                            ? &z_rigid_bodies[j] : NULL;
                        z_game_resolve_box_3d(
                            &z_transforms[i], &z_box_colliders_3d[i], a_body,
                            &z_transforms[j], &z_box_colliders_3d[j], b_body);
                    }
                }
            }
            for (int i = 0; i < Z_GAME_MAX_ENTITIES; ++i) {
                z_rigid_bodies[i].force_x = 0;
                z_rigid_bodies[i].force_y = 0;
                z_rigid_bodies[i].force_z = 0;
            }
            return z_none();
        }
        case Z_GAME_BODY_SET_VELOCITY:
        case Z_GAME_BODY_APPLY_FORCE: {
            int body = z_game_handle(args, 0, Z_GAME_MAX_OBJECTS, line, "Invalid physics body handle");
            if (!z_bodies[body].active) z_fail(line, "Physics body does not exist");
            double raw_x = z_game_num(args, 1, line);
            double raw_y = z_game_num(args, 2, line);
            if (!isfinite(raw_x) || !isfinite(raw_y) ||
                !isfinite((float)raw_x) || !isfinite((float)raw_y))
                z_fail(line, "Physics velocity and force must be finite");
            float x = (float)raw_x;
            float y = (float)raw_y;
            if (id == Z_GAME_BODY_SET_VELOCITY) { z_bodies[body].vx = x; z_bodies[body].vy = y; }
            else { z_bodies[body].vx += x / z_bodies[body].mass; z_bodies[body].vy += y / z_bodies[body].mass; }
            return z_none();
        }
        case Z_GAME_BODY_X:
        case Z_GAME_BODY_Y: {
            int body = z_game_handle(args, 0, Z_GAME_MAX_OBJECTS, line, "Invalid physics body handle");
            if (!z_bodies[body].active) z_fail(line, "Physics body does not exist");
            return z_game_number(id == Z_GAME_BODY_X ? z_bodies[body].x : z_bodies[body].y);
        }
        case Z_GAME_BODY_COLLIDES: {
            int a = z_game_handle(args, 0, Z_GAME_MAX_OBJECTS, line, "Invalid physics body handle");
            int b = z_game_handle(args, 1, Z_GAME_MAX_OBJECTS, line, "Invalid physics body handle");
            if (!z_bodies[a].active || !z_bodies[b].active) z_fail(line, "Physics body does not exist");
            ZPhysicsBody x = z_bodies[a], y = z_bodies[b];
            return z_bool(x.x < y.x + y.width && x.x + x.width > y.x &&
                          x.y < y.y + y.height && x.y + x.height > y.y);
        }
        case Z_GAME_CREATE_ENTITY: {
            for (int i = 0; i < Z_GAME_MAX_ENTITIES; ++i) {
                if (!z_entities[i].active &&
                    z_entities[i].generation < UINT32_MAX) {
                    uint32_t generation = z_entities[i].generation + 1;
                    memset(&z_transforms[i], 0, sizeof z_transforms[i]);
                    memset(&z_rigid_bodies[i], 0, sizeof z_rigid_bodies[i]);
                    memset(&z_box_colliders[i], 0, sizeof z_box_colliders[i]);
                    memset(&z_box_colliders_3d[i], 0, sizeof z_box_colliders_3d[i]);
                    z_entities[i].generation = generation;
                    z_entities[i].active = true;
                    uint64_t token = (uint64_t)generation *
                                     Z_GAME_MAX_ENTITIES + (uint64_t)i;
                    return z_game_number((double)token);
                }
            }
            z_fail(line, "Maximum number of entities reached");
            return z_none();
        }
        case Z_GAME_DESTROY_ENTITY: {
            int entity = z_game_entity_handle(args, 0, line);
            z_entities[entity].active = false;
            memset(&z_transforms[entity], 0, sizeof z_transforms[entity]);
            memset(&z_rigid_bodies[entity], 0, sizeof z_rigid_bodies[entity]);
            memset(&z_box_colliders[entity], 0, sizeof z_box_colliders[entity]);
            memset(&z_box_colliders_3d[entity], 0, sizeof z_box_colliders_3d[entity]);
            return z_none();
        }
        case Z_GAME_ADD_TRANSFORM: {
            int entity = z_game_entity_handle(args, 0, line);
            double x = z_game_num(args, 1, line), y = z_game_num(args, 2, line);
            if (z_transforms[entity].active) z_fail(line, "Entity already has a transform");
            if (!isfinite(x) || !isfinite(y) ||
                !isfinite((float)x) || !isfinite((float)y))
                z_fail(line, "Transform position must be finite");
            z_transforms[entity] = (ZTransform){
                true, false, (float)x, (float)y, 0
            };
            return z_none();
        }
        case Z_GAME_ADD_TRANSFORM_3D: {
            int entity = z_game_entity_handle(args, 0, line);
            double x = z_game_num(args, 1, line);
            double y = z_game_num(args, 2, line);
            double z = z_game_num(args, 3, line);
            if (z_transforms[entity].active)
                z_fail(line, "Entity already has a transform");
            if (!isfinite(x) || !isfinite(y) || !isfinite(z) ||
                !isfinite((float)x) || !isfinite((float)y) ||
                !isfinite((float)z))
                z_fail(line, "Transform position must be finite");
            z_transforms[entity] = (ZTransform){
                true, true, (float)x, (float)y, (float)z
            };
            return z_none();
        }
        case Z_GAME_ENTITY_X:
        case Z_GAME_ENTITY_Y:
        case Z_GAME_ENTITY_Z:
        case Z_GAME_ENTITY_VELOCITY_X:
        case Z_GAME_ENTITY_VELOCITY_Y:
        case Z_GAME_ENTITY_VELOCITY_Z: {
            int entity = z_game_entity_handle(args, 0, line);
            if (id == Z_GAME_ENTITY_X || id == Z_GAME_ENTITY_Y) {
                if (!z_transforms[entity].active)
                    z_fail(line, "Entity does not have a transform");
                if (id == Z_GAME_ENTITY_X) return z_game_number(z_transforms[entity].x);
                if (id == Z_GAME_ENTITY_Y) return z_game_number(z_transforms[entity].y);
                return z_game_number(z_transforms[entity].z);
            }
            if (id == Z_GAME_ENTITY_Z &&
                !z_transforms[entity].three_dimensional)
                z_fail(line, "Entity does not have a 3D transform");
            if (!z_rigid_bodies[entity].active)
                z_fail(line, "Entity does not have a rigidbody");
            if (id == Z_GAME_ENTITY_VELOCITY_Z &&
                !z_transforms[entity].three_dimensional)
                z_fail(line, "Entity does not have a 3D transform");
            if (id == Z_GAME_ENTITY_VELOCITY_X)
                return z_game_number(z_rigid_bodies[entity].vx);
            if (id == Z_GAME_ENTITY_VELOCITY_Y)
                return z_game_number(z_rigid_bodies[entity].vy);
            return z_game_number(z_rigid_bodies[entity].vz);
        }
        case Z_GAME_SET_ENTITY_POSITION: {
            int entity = z_game_entity_handle(args, 0, line);
            if (!z_transforms[entity].active)
                z_fail(line, "Entity does not have a transform");
            double x = z_game_num(args, 1, line), y = z_game_num(args, 2, line);
            if (!isfinite(x) || !isfinite(y) ||
                !isfinite((float)x) || !isfinite((float)y))
                z_fail(line, "Transform position must be finite");
            z_transforms[entity].x = (float)x;
            z_transforms[entity].y = (float)y;
            return z_none();
        }
        case Z_GAME_SET_ENTITY_POSITION_3D: {
            int entity = z_game_entity_handle(args, 0, line);
            if (!z_transforms[entity].active)
                z_fail(line, "Entity does not have a transform");
            if (!z_transforms[entity].three_dimensional)
                z_fail(line, "Entity does not have a 3D transform");
            double x = z_game_num(args, 1, line);
            double y = z_game_num(args, 2, line);
            double z = z_game_num(args, 3, line);
            if (!isfinite(x) || !isfinite(y) || !isfinite(z) ||
                !isfinite((float)x) || !isfinite((float)y) ||
                !isfinite((float)z))
                z_fail(line, "Transform position must be finite");
            z_transforms[entity].x = (float)x;
            z_transforms[entity].y = (float)y;
            z_transforms[entity].z = (float)z;
            return z_none();
        }
        case Z_GAME_ADD_RIGIDBODY: {
            int entity = z_game_entity_handle(args, 0, line);
            double mass = z_game_num(args, 1, line);
            if (!z_transforms[entity].active)
                z_fail(line, "Add a transform before adding a rigidbody");
            if (z_rigid_bodies[entity].active)
                z_fail(line, "Entity already has a rigidbody");
            if (!isfinite(mass) || mass < 0 ||
                (mass > 0 && !isfinite((float)mass)))
                z_fail(line, "Rigidbody mass must be finite and non-negative");
            z_rigid_bodies[entity] = (ZRigidBody){ true, (float)mass, 0, 0, 0, 0 };
            return z_none();
        }
        case Z_GAME_ENTITY_SET_VELOCITY:
        case Z_GAME_ENTITY_APPLY_FORCE: {
            int entity = z_game_entity_handle(args, 0, line);
            if (!z_rigid_bodies[entity].active)
                z_fail(line, "Entity does not have a rigidbody");
            ZRigidBody *body = &z_rigid_bodies[entity];
            if (body->mass == 0) z_fail(line, "Static rigidbodies cannot be moved");
            double x = z_game_num(args, 1, line), y = z_game_num(args, 2, line);
            if (!isfinite(x) || !isfinite(y) ||
                !isfinite((float)x) || !isfinite((float)y))
                z_fail(line, "Velocity and force must be finite");
            if (id == Z_GAME_ENTITY_SET_VELOCITY) {
                body->vx = (float)x;
                body->vy = (float)y;
            } else {
                float force_x = body->force_x + (float)x;
                float force_y = body->force_y + (float)y;
                if (!isfinite(force_x) || !isfinite(force_y))
                    z_fail(line, "Accumulated force must be finite");
                body->force_x = force_x;
                body->force_y = force_y;
            }
            return z_none();
        }
        case Z_GAME_ENTITY_SET_VELOCITY_3D:
        case Z_GAME_ENTITY_APPLY_FORCE_3D: {
            int entity = z_game_entity_handle(args, 0, line);
            if (!z_rigid_bodies[entity].active)
                z_fail(line, "Entity does not have a rigidbody");
            if (!z_transforms[entity].three_dimensional)
                z_fail(line, "Entity does not have a 3D transform");
            ZRigidBody *body = &z_rigid_bodies[entity];
            if (body->mass == 0) z_fail(line, "Static rigidbodies cannot be moved");
            double x = z_game_num(args, 1, line);
            double y = z_game_num(args, 2, line);
            double z = z_game_num(args, 3, line);
            if (!isfinite(x) || !isfinite(y) || !isfinite(z) ||
                !isfinite((float)x) || !isfinite((float)y) ||
                !isfinite((float)z))
                z_fail(line, "Velocity and force must be finite");
            if (id == Z_GAME_ENTITY_SET_VELOCITY_3D) {
                body->vx = (float)x;
                body->vy = (float)y;
                body->vz = (float)z;
            } else {
                float force_x = body->force_x + (float)x;
                float force_y = body->force_y + (float)y;
                float force_z = body->force_z + (float)z;
                if (!isfinite(force_x) || !isfinite(force_y) ||
                    !isfinite(force_z))
                    z_fail(line, "Accumulated force must be finite");
                body->force_x = force_x;
                body->force_y = force_y;
                body->force_z = force_z;
            }
            return z_none();
        }
        case Z_GAME_ADD_BOX_COLLIDER: {
            int entity = z_game_entity_handle(args, 0, line);
            if (!z_transforms[entity].active)
                z_fail(line, "Add a transform before adding a box collider");
            if (z_transforms[entity].three_dimensional)
                z_fail(line, "Use a 3D box collider with a 3D transform");
            if (z_box_colliders[entity].active)
                z_fail(line, "Entity already has a box collider");
            if (z_box_colliders_3d[entity].active)
                z_fail(line, "Entity already has a 3D box collider");
            double width = z_game_num(args, 1, line);
            double height = z_game_num(args, 2, line);
            double restitution = z_game_num(args, 3, line);
            double friction = z_game_num(args, 4, line);
            if (!isfinite(width) || !isfinite(height) ||
                !isfinite((float)width) || !isfinite((float)height) ||
                width <= 0 || height <= 0)
                z_fail(line, "Box collider dimensions must be finite and positive");
            if (!isfinite(restitution) || restitution < 0 || restitution > 1)
                z_fail(line, "Restitution must be between 0 and 1");
            if (!isfinite(friction) || friction < 0 || friction > 1)
                z_fail(line, "Friction must be between 0 and 1");
            z_box_colliders[entity] = (ZBoxCollider){
                true, (float)width, (float)height,
                (float)restitution, (float)friction
            };
            return z_none();
        }
        case Z_GAME_ADD_BOX_COLLIDER_3D: {
            int entity = z_game_entity_handle(args, 0, line);
            if (!z_transforms[entity].active)
                z_fail(line, "Add a 3D transform before adding a box collider");
            if (!z_transforms[entity].three_dimensional)
                z_fail(line, "Add a 3D transform before adding a 3D box collider");
            if (z_box_colliders_3d[entity].active)
                z_fail(line, "Entity already has a 3D box collider");
            if (z_box_colliders[entity].active)
                z_fail(line, "Entity already has a 2D box collider");
            double width = z_game_num(args, 1, line);
            double height = z_game_num(args, 2, line);
            double depth = z_game_num(args, 3, line);
            double restitution = z_game_num(args, 4, line);
            double friction = z_game_num(args, 5, line);
            if (!isfinite(width) || !isfinite(height) || !isfinite(depth) ||
                !isfinite((float)width) || !isfinite((float)height) ||
                !isfinite((float)depth) || width <= 0 || height <= 0 || depth <= 0)
                z_fail(line, "3D box collider dimensions must be finite and positive");
            if (!isfinite(restitution) || restitution < 0 || restitution > 1)
                z_fail(line, "Restitution must be between 0 and 1");
            if (!isfinite(friction) || friction < 0 || friction > 1)
                z_fail(line, "Friction must be between 0 and 1");
            z_box_colliders_3d[entity] = (ZBoxCollider3D){
                true, (float)width, (float)height, (float)depth,
                (float)restitution, (float)friction
            };
            return z_none();
        }
        case Z_GAME_ENTITY_COLLIDES: {
            int a = z_game_entity_handle(args, 0, line);
            int b = z_game_entity_handle(args, 1, line);
            if (!z_box_colliders[a].active || !z_box_colliders[b].active ||
                !z_transforms[a].active || !z_transforms[b].active ||
                z_transforms[a].three_dimensional ||
                z_transforms[b].three_dimensional)
                z_fail(line, "Both entities need transforms and box colliders");
            ZBoxCollider *x = &z_box_colliders[a], *y = &z_box_colliders[b];
            return z_bool(
                z_transforms[a].x < z_transforms[b].x + y->width &&
                z_transforms[a].x + x->width > z_transforms[b].x &&
                z_transforms[a].y < z_transforms[b].y + y->height &&
                z_transforms[a].y + x->height > z_transforms[b].y);
        }
        case Z_GAME_ENTITY_COLLIDES_3D: {
            int a = z_game_entity_handle(args, 0, line);
            int b = z_game_entity_handle(args, 1, line);
            if (!z_box_colliders_3d[a].active || !z_box_colliders_3d[b].active ||
                !z_transforms[a].active || !z_transforms[b].active ||
                !z_transforms[a].three_dimensional ||
                !z_transforms[b].three_dimensional)
                z_fail(line, "Both entities need transforms and 3D box colliders");
            ZBoxCollider3D *x = &z_box_colliders_3d[a];
            ZBoxCollider3D *y = &z_box_colliders_3d[b];
            return z_bool(
                z_transforms[a].x < z_transforms[b].x + y->width &&
                z_transforms[a].x + x->width > z_transforms[b].x &&
                z_transforms[a].y < z_transforms[b].y + y->height &&
                z_transforms[a].y + x->height > z_transforms[b].y &&
                z_transforms[a].z < z_transforms[b].z + y->depth &&
                z_transforms[a].z + x->depth > z_transforms[b].z);
        }
        case Z_GAME_CREATE_PATH_GRID: {
            double raw_width = z_game_num(args, 0, line);
            double raw_height = z_game_num(args, 1, line);
            double cell_size = z_game_num(args, 2, line);
            if (!isfinite(raw_width) || floor(raw_width) != raw_width ||
                raw_width < 1 || raw_width > 64 ||
                !isfinite(raw_height) || floor(raw_height) != raw_height ||
                raw_height < 1 || raw_height > 64)
                z_fail(line, "Path-grid dimensions must be whole numbers from 1 to 64");
            if (!isfinite(cell_size) || !isfinite((float)cell_size) ||
                cell_size <= 0 || cell_size > FLT_MAX / 64)
                z_fail(line, "Path-grid cell size must be finite and positive");
            for (int i = 0; i < Z_GAME_MAX_PATH_GRIDS; ++i) {
                if (!z_path_grids[i].active &&
                    z_path_grids[i].generation < UINT32_MAX) {
                    uint32_t generation = z_path_grids[i].generation + 1;
                    memset(z_path_grids[i].blocked, 0,
                           sizeof z_path_grids[i].blocked);
                    z_path_grids[i].generation = generation;
                    z_path_grids[i].width = (int)raw_width;
                    z_path_grids[i].height = (int)raw_height;
                    z_path_grids[i].cell_size = (float)cell_size;
                    z_path_grids[i].active = true;
                    uint64_t token = (uint64_t)generation *
                                     Z_GAME_MAX_PATH_GRIDS + (uint64_t)i;
                    return z_game_number((double)token);
                }
            }
            z_fail(line, "Maximum number of path grids reached");
            return z_none();
        }
        case Z_GAME_DESTROY_PATH_GRID: {
            int grid = z_game_path_grid_handle(args, 0, line);
            z_path_grids[grid].active = false;
            for (int i = 0; i < Z_GAME_MAX_PATHS; ++i) {
                if (z_paths[i].active && z_paths[i].grid_index == grid &&
                    z_paths[i].grid_generation == z_path_grids[grid].generation)
                    z_paths[i].active = false;
            }
            return z_none();
        }
        case Z_GAME_SET_PATH_BLOCKED: {
            int grid = z_game_path_grid_handle(args, 0, line);
            double raw_x = z_game_num(args, 1, line);
            double raw_y = z_game_num(args, 2, line);
            if (!isfinite(raw_x) || floor(raw_x) != raw_x ||
                !isfinite(raw_y) || floor(raw_y) != raw_y)
                z_fail(line, "Path-grid coordinates must be whole numbers");
            int x = (int)raw_x, y = (int)raw_y;
            if (x < 0 || y < 0 ||
                x >= z_path_grids[grid].width || y >= z_path_grids[grid].height)
                z_fail(line, "Path-grid coordinate is outside the grid");
            if (args[3].type != Z_BOOLEAN)
                z_fail(line, "Blocked state must be boolean");
            int cell = y * z_path_grids[grid].width + x;
            bool blocked = args[3].number != 0;
            if (z_path_grids[grid].blocked[cell] != blocked) {
                z_path_grids[grid].blocked[cell] = blocked;
                for (int i = 0; i < Z_GAME_MAX_PATHS; ++i) {
                    if (z_paths[i].active && z_paths[i].grid_index == grid &&
                        z_paths[i].grid_generation ==
                            z_path_grids[grid].generation)
                        z_paths[i].active = false;
                }
            }
            return z_none();
        }
        case Z_GAME_FIND_PATH: {
            int grid = z_game_path_grid_handle(args, 0, line);
            double raw[4] = {
                z_game_num(args, 1, line), z_game_num(args, 2, line),
                z_game_num(args, 3, line), z_game_num(args, 4, line)
            };
            for (int i = 0; i < 4; ++i) {
                if (!isfinite(raw[i]) || floor(raw[i]) != raw[i] ||
                    raw[i] < INT_MIN || raw[i] > INT_MAX)
                    z_fail(line, "Path coordinates must be whole numbers");
            }
            int path_index = -1;
            for (int i = 0; i < Z_GAME_MAX_PATHS; ++i) {
                if (!z_paths[i].active &&
                    z_paths[i].generation < UINT32_MAX) {
                    path_index = i;
                    break;
                }
            }
            if (path_index < 0) z_fail(line, "Maximum number of paths reached");
            ZPath *path = &z_paths[path_index];
            uint32_t generation = path->generation + 1;
            path->active = true;
            path->generation = generation;
            path->grid_index = grid;
            path->grid_generation = z_path_grids[grid].generation;
            path->entity_index = -1;
            z_game_find_path(&z_path_grids[grid], path, (int)raw[0], (int)raw[1],
                             (int)raw[2], (int)raw[3], line);
            uint64_t token = (uint64_t)generation *
                             Z_GAME_MAX_PATHS + (uint64_t)path_index;
            return z_game_number((double)token);
        }
        case Z_GAME_DESTROY_PATH: {
            int path = z_game_path_handle(args, 0, line);
            z_paths[path].active = false;
            return z_none();
        }
        case Z_GAME_PATH_LENGTH: {
            int path = z_game_path_handle(args, 0, line);
            return z_game_number(z_paths[path].length);
        }
        case Z_GAME_PATH_X:
        case Z_GAME_PATH_Y: {
            int path = z_game_path_handle(args, 0, line);
            double raw_index = z_game_num(args, 1, line);
            if (!isfinite(raw_index) || floor(raw_index) != raw_index ||
                raw_index < 0 || raw_index >= z_paths[path].length)
                z_fail(line, "Path index is outside the path");
            int index = (int)raw_index;
            return z_game_number(id == Z_GAME_PATH_X
                ? z_paths[path].x[index] : z_paths[path].y[index]);
        }
        case Z_GAME_FOLLOW_PATH: {
            int path_index = z_game_path_handle(args, 0, line);
            int entity = z_game_entity_handle(args, 1, line);
            ZPath *path = &z_paths[path_index];
            if (!z_transforms[entity].active ||
                z_transforms[entity].three_dimensional)
                z_fail(line, "Path following requires an entity with a 2D transform");
            double speed = z_game_num(args, 2, line);
            double delta = z_game_num(args, 3, line);
            if (!isfinite(speed) || speed <= 0 ||
                !isfinite((float)speed))
                z_fail(line, "Path-follow speed must be finite and positive");
            if (!isfinite(delta) || delta < 0 || delta > 0.25)
                z_fail(line, "Path-follow delta must be between 0 and 0.25 seconds");
            if (!isfinite((float)(speed * delta)))
                z_fail(line, "Path-follow movement must be finite");
            if (path->entity_index < 0) {
                path->entity_index = entity;
                path->entity_generation = z_entities[entity].generation;
            } else if (path->entity_index != entity ||
                       path->entity_generation != z_entities[entity].generation) {
                z_fail(line, "A path can only be followed by its bound entity");
            }
            if (path->length == 0) return z_bool(false);
            float remaining = (float)(speed * delta);
            while (path->cursor < path->length) {
                int cell = path->cursor;
                float target_x =
                    ((float)path->x[cell] + 0.5f) *
                    z_path_grids[path->grid_index].cell_size;
                float target_y =
                    ((float)path->y[cell] + 0.5f) *
                    z_path_grids[path->grid_index].cell_size;
                float dx = target_x - z_transforms[entity].x;
                float dy = target_y - z_transforms[entity].y;
                float distance = sqrtf(dx * dx + dy * dy);
                if (distance <= remaining || distance <= 0.0001f) {
                    z_transforms[entity].x = target_x;
                    z_transforms[entity].y = target_y;
                    remaining = fmaxf(0, remaining - distance);
                    ++path->cursor;
                    continue;
                }
                if (remaining > 0) {
                    z_transforms[entity].x += dx / distance * remaining;
                    z_transforms[entity].y += dy / distance * remaining;
                }
                break;
            }
            return z_bool(path->cursor >= path->length);
        }
        case Z_GAME_CREATE_PARTICLE_EMITTER: {
            double raw_capacity = z_game_num(args, 0, line);
            if (!isfinite(raw_capacity) || floor(raw_capacity) != raw_capacity ||
                raw_capacity < 1 || raw_capacity > Z_GAME_MAX_PARTICLES)
                z_fail(line, "Particle capacity must be a whole number from 1 to 256");
            for (int i = 0; i < Z_GAME_MAX_PARTICLE_EMITTERS; ++i) {
                if (!z_particle_emitters[i].active &&
                    z_particle_emitters[i].generation < UINT32_MAX) {
                    uint32_t generation = z_particle_emitters[i].generation + 1;
                    memset(z_particle_emitters[i].particles, 0,
                           sizeof z_particle_emitters[i].particles);
                    z_particle_emitters[i].generation = generation;
                    z_particle_emitters[i].capacity = (int)raw_capacity;
                    z_particle_emitters[i].gravity = 200;
                    z_particle_emitters[i].random_state =
                        generation ^ ((uint32_t)i + 1u) * 0x85ebca6bu;
                    z_particle_emitters[i].active = true;
                    uint64_t token = (uint64_t)generation *
                                     Z_GAME_MAX_PARTICLE_EMITTERS + (uint64_t)i;
                    return z_game_number((double)token);
                }
            }
            z_fail(line, "Maximum number of particle emitters reached");
            return z_none();
        }
        case Z_GAME_DESTROY_PARTICLE_EMITTER: {
            int emitter = z_game_particle_emitter_handle(args, 0, line);
            z_particle_emitters[emitter].active = false;
            return z_none();
        }
        case Z_GAME_EMIT_PARTICLES: {
            int emitter_index = z_game_particle_emitter_handle(args, 0, line);
            ZParticleEmitter *emitter = &z_particle_emitters[emitter_index];
            double x = z_game_num(args, 1, line);
            double y = z_game_num(args, 2, line);
            double raw_count = z_game_num(args, 3, line);
            double lifetime = z_game_num(args, 4, line);
            double speed = z_game_num(args, 5, line);
            Color color = z_game_color(args[6], line);
            if (!isfinite(x) || !isfinite(y) ||
                !isfinite((float)x) || !isfinite((float)y))
                z_fail(line, "Particle position must be finite");
            if (!isfinite(raw_count) || floor(raw_count) != raw_count ||
                raw_count < 1 || raw_count > Z_GAME_MAX_PARTICLES)
                z_fail(line, "Particle count must be a whole number from 1 to 256");
            if (!isfinite(lifetime) || lifetime <= 0 ||
                !isfinite(speed) || speed < 0 ||
                !isfinite((float)lifetime) || !isfinite((float)speed))
                z_fail(line, "Particle lifetime must be positive and speed non-negative");
            int spawned = 0;
            for (int i = 0; i < emitter->capacity && spawned < (int)raw_count; ++i) {
                if (emitter->particles[i].active) continue;
                float angle = (float)((double)z_game_random(&emitter->random_state) /
                                      4294967296.0 * 6.283185307179586);
                emitter->particles[i] = (ZParticle){
                    true, (float)x, (float)y, cosf(angle) * (float)speed,
                    sinf(angle) * (float)speed, (float)lifetime, 3, color
                };
                ++spawned;
            }
            return z_game_number(spawned);
        }
        case Z_GAME_UPDATE_PARTICLE_EMITTER: {
            int emitter = z_game_particle_emitter_handle(args, 0, line);
            double raw_delta = z_game_num(args, 1, line);
            if (!isfinite(raw_delta) || raw_delta < 0 || raw_delta > 0.25)
                z_fail(line, "Particle delta must be between 0 and 0.25 seconds");
            float delta = (float)raw_delta;
            for (int i = 0; i < z_particle_emitters[emitter].capacity; ++i) {
                ZParticle *particle = &z_particle_emitters[emitter].particles[i];
                if (!particle->active) continue;
                particle->remaining -= delta;
                if (particle->remaining <= 0) {
                    particle->active = false;
                    continue;
                }
                particle->vy += z_particle_emitters[emitter].gravity * delta;
                particle->x += particle->vx * delta;
                particle->y += particle->vy * delta;
            }
            return z_none();
        }
        case Z_GAME_SET_PARTICLE_GRAVITY: {
            int emitter = z_game_particle_emitter_handle(args, 0, line);
            double gravity = z_game_num(args, 1, line);
            if (!isfinite(gravity) || !isfinite((float)gravity))
                z_fail(line, "Particle gravity must be finite");
            z_particle_emitters[emitter].gravity = (float)gravity;
            return z_none();
        }
        case Z_GAME_DRAW_PARTICLE_EMITTER: {
            int emitter = z_game_particle_emitter_handle(args, 0, line);
            for (int i = 0; i < z_particle_emitters[emitter].capacity; ++i) {
                ZParticle *particle = &z_particle_emitters[emitter].particles[i];
                if (particle->active)
                    DrawCircleV((Vector2){ particle->x, particle->y },
                                particle->radius, particle->color);
            }
            return z_none();
        }
        case Z_GAME_PARTICLE_COUNT: {
            int emitter = z_game_particle_emitter_handle(args, 0, line);
            int count = 0;
            for (int i = 0; i < z_particle_emitters[emitter].capacity; ++i)
                if (z_particle_emitters[emitter].particles[i].active) ++count;
            return z_game_number(count);
        }
        case Z_GAME_CLEAR_PARTICLE_EMITTER: {
            int emitter = z_game_particle_emitter_handle(args, 0, line);
            memset(z_particle_emitters[emitter].particles, 0,
                   sizeof z_particle_emitters[emitter].particles);
            return z_none();
        }
        case Z_GAME_CREATE_COMBATANT: {
            double max_health = z_game_num(args, 0, line);
            double armor = z_game_num(args, 1, line);
            if (!isfinite(max_health) || max_health <= 0)
                z_fail(line, "Maximum health must be finite and greater than zero");
            if (!isfinite(armor) || armor < 0)
                z_fail(line, "Armor must be finite and non-negative");
            for (int i = 0; i < Z_GAME_MAX_COMBATANTS; ++i) {
                if (!z_combatants[i].active &&
                    z_combatants[i].generation < UINT32_MAX) {
                    uint32_t generation = z_combatants[i].generation + 1;
                    memset(&z_combatants[i], 0, sizeof z_combatants[i]);
                    z_combatants[i].active = true;
                    z_combatants[i].generation = generation;
                    z_combatants[i].health = max_health;
                    z_combatants[i].max_health = max_health;
                    z_combatants[i].armor = armor;
                    uint64_t token = (uint64_t)generation *
                                     Z_GAME_MAX_COMBATANTS + (uint64_t)i;
                    return z_game_number((double)token);
                }
            }
            z_fail(line, "Maximum number of combatants reached");
            return z_none();
        }
        case Z_GAME_DESTROY_COMBATANT: {
            int combatant = z_game_combatant_handle(args, 0, line);
            z_combatants[combatant].active = false;
            memset(z_combatants[combatant].effects, 0,
                   sizeof z_combatants[combatant].effects);
            return z_none();
        }
        case Z_GAME_COMBATANT_HEALTH:
        case Z_GAME_COMBATANT_MAX_HEALTH:
        case Z_GAME_COMBATANT_ARMOR: {
            int combatant = z_game_combatant_handle(args, 0, line);
            if (id == Z_GAME_COMBATANT_HEALTH)
                return z_game_number(z_combatants[combatant].health);
            if (id == Z_GAME_COMBATANT_MAX_HEALTH)
                return z_game_number(z_combatants[combatant].max_health);
            return z_game_number(z_combatants[combatant].armor);
        }
        case Z_GAME_SET_COMBATANT_ARMOR: {
            int combatant = z_game_combatant_handle(args, 0, line);
            double armor = z_game_num(args, 1, line);
            if (!isfinite(armor) || armor < 0)
                z_fail(line, "Armor must be finite and non-negative");
            z_combatants[combatant].armor = armor;
            return z_none();
        }
        case Z_GAME_APPLY_DAMAGE: {
            int combatant = z_game_combatant_handle(args, 0, line);
            double amount = z_game_num(args, 1, line);
            if (!isfinite(amount) || amount < 0)
                z_fail(line, "Damage must be finite and non-negative");
            double health = z_combatants[combatant].health;
            double damage = fmax(0, amount - z_combatants[combatant].armor);
            double applied = fmin(health, damage);
            z_combatants[combatant].health -= applied;
            return z_game_number(applied);
        }
        case Z_GAME_HEAL_COMBATANT: {
            int combatant = z_game_combatant_handle(args, 0, line);
            double amount = z_game_num(args, 1, line);
            if (!isfinite(amount) || amount < 0)
                z_fail(line, "Healing must be finite and non-negative");
            double missing = z_combatants[combatant].max_health -
                             z_combatants[combatant].health;
            double healed = fmin(missing, amount);
            z_combatants[combatant].health += healed;
            return z_game_number(healed);
        }
        case Z_GAME_IS_COMBATANT_ALIVE: {
            int combatant = z_game_combatant_handle(args, 0, line);
            return z_bool(z_combatants[combatant].health > 0);
        }
        case Z_GAME_APPLY_STATUS_EFFECT: {
            int combatant = z_game_combatant_handle(args, 0, line);
            const char *name = z_game_str(args, 1, line);
            double duration = z_game_num(args, 2, line);
            double strength = z_game_num(args, 3, line);
            if (!TextIsEqual(name, "poison") && !TextIsEqual(name, "burning") &&
                !TextIsEqual(name, "regeneration"))
                z_fail(line, "Unknown status effect (use poison, burning, or regeneration)");
            if (!isfinite(duration) || duration <= 0)
                z_fail(line, "Status effect duration must be finite and greater than zero");
            if (!isfinite(strength) || strength <= 0)
                z_fail(line, "Status effect strength must be finite and greater than zero");
            if (z_combatants[combatant].health <= 0)
                z_fail(line, "Cannot apply a status effect to a defeated combatant");
            int effect = z_game_status_effect(combatant, name);
            if (effect < 0) {
                for (int i = 0; i < Z_GAME_MAX_STATUS_EFFECTS; ++i) {
                    if (!z_combatants[combatant].effects[i].active) {
                        effect = i;
                        break;
                    }
                }
            }
            if (effect < 0) z_fail(line, "Maximum number of status effects reached");
            ZStatusEffect *slot = &z_combatants[combatant].effects[effect];
            slot->active = true;
            snprintf(slot->name, sizeof slot->name, "%s", name);
            slot->remaining = duration;
            slot->strength = strength;
            return z_none();
        }
        case Z_GAME_REMOVE_STATUS_EFFECT:
        case Z_GAME_HAS_STATUS_EFFECT:
        case Z_GAME_STATUS_EFFECT_REMAINING: {
            int combatant = z_game_combatant_handle(args, 0, line);
            const char *name = z_game_str(args, 1, line);
            int effect = z_game_status_effect(combatant, name);
            if (id == Z_GAME_HAS_STATUS_EFFECT) return z_bool(effect >= 0);
            if (id == Z_GAME_STATUS_EFFECT_REMAINING)
                return z_game_number(effect >= 0
                    ? z_combatants[combatant].effects[effect].remaining : 0);
            if (effect >= 0)
                memset(&z_combatants[combatant].effects[effect], 0,
                       sizeof z_combatants[combatant].effects[effect]);
            return z_bool(effect >= 0);
        }
        case Z_GAME_UPDATE_STATUS_EFFECTS: {
            int combatant = z_game_combatant_handle(args, 0, line);
            double delta = z_game_num(args, 1, line);
            if (!isfinite(delta) || delta < 0)
                z_fail(line, "Status-effect delta must be finite and non-negative");
            ZCombatant *target = &z_combatants[combatant];
            for (int i = 0; i < Z_GAME_MAX_STATUS_EFFECTS; ++i) {
                ZStatusEffect *effect = &target->effects[i];
                if (!effect->active) continue;
                double elapsed = fmin(delta, effect->remaining);
                if (target->health > 0 && TextIsEqual(effect->name, "regeneration")) {
                    target->health = fmin(target->max_health,
                                          target->health + effect->strength * elapsed);
                } else if (target->health > 0 &&
                           (TextIsEqual(effect->name, "poison") ||
                            TextIsEqual(effect->name, "burning"))) {
                    target->health = fmax(0, target->health - effect->strength * elapsed);
                }
                effect->remaining -= elapsed;
                if (effect->remaining <= 0)
                    memset(effect, 0, sizeof *effect);
            }
            return z_none();
        }
        case Z_GAME_CLEAR_STATUS_EFFECTS: {
            int combatant = z_game_combatant_handle(args, 0, line);
            memset(z_combatants[combatant].effects, 0,
                   sizeof z_combatants[combatant].effects);
            return z_none();
        }
#ifdef _WIN32
        case Z_GAME_NETWORK_START: {
            double port = z_game_num(args, 0, line);
            if (port < 1 || port > 65535 || floor(port) != port)
                z_fail(line, "Network port must be a whole number from 1 to 65535");
            if (!z_winsock_open) {
                WSADATA data;
                if (WSAStartup(MAKEWORD(2, 2), &data) != 0) z_fail(line, "Could not initialize Windows networking");
                z_winsock_open = true;
            }
            int handle = z_game_socket_handle(line);
            SOCKET socket_handle = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
            if (socket_handle == INVALID_SOCKET) z_fail(line, "Could not create UDP socket");
            u_long nonblocking = 1;
            ioctlsocket(socket_handle, FIONBIO, &nonblocking);
            struct sockaddr_in address = { 0 };
            address.sin_family = AF_INET;
            address.sin_addr.s_addr = htonl(INADDR_ANY);
            address.sin_port = htons((u_short)port);
            if (bind(socket_handle, (struct sockaddr *)&address, sizeof(address)) == SOCKET_ERROR) {
                closesocket(socket_handle); z_fail(line, "Could not bind UDP port");
            }
            z_sockets[handle] = socket_handle;
            z_socket_used[handle] = true;
            return z_game_number(handle);
        }
#else
        case Z_GAME_NETWORK_START: {
            double port = z_game_num(args, 0, line);
            if (port < 1 || port > 65535 || floor(port) != port)
                z_fail(line, "Network port must be a whole number from 1 to 65535");
            int handle = z_game_socket_handle(line);
            int socket_handle = socket(AF_INET, SOCK_DGRAM, 0);
            if (socket_handle < 0) z_fail(line, "Could not create UDP socket");
            int flags = fcntl(socket_handle, F_GETFL, 0);
            if (flags >= 0) fcntl(socket_handle, F_SETFL, flags | O_NONBLOCK);
            struct sockaddr_in address = { 0 };
            address.sin_family = AF_INET;
            address.sin_addr.s_addr = htonl(INADDR_ANY);
            address.sin_port = htons((uint16_t)port);
            if (bind(socket_handle, (struct sockaddr *)&address, sizeof(address)) < 0) {
                close(socket_handle); z_fail(line, "Could not bind UDP port");
            }
            z_sockets[handle] = socket_handle;
            z_socket_used[handle] = true;
            return z_game_number(handle);
        }
#endif
        case Z_GAME_NETWORK_SEND: {
            int handle = z_game_handle(args, 0, Z_GAME_MAX_HANDLES, line, "Invalid network handle");
            if (!z_socket_used[handle]) z_fail(line, "Network socket is not open");
            double port = z_game_num(args, 2, line);
            if (port < 1 || port > 65535 || floor(port) != port)
                z_fail(line, "Network port must be a whole number from 1 to 65535");
            const char *host = z_game_str(args, 1, line);
            const char *message = z_game_str(args, 3, line);
            struct sockaddr_in address = { 0 };
            address.sin_family = AF_INET;
            address.sin_port = htons((uint16_t)port);
            if (inet_pton(AF_INET, host, &address.sin_addr) != 1)
                z_fail(line, "Network host must be an IPv4 address");
            int result = (int)sendto(z_sockets[handle], message, (int)strlen(message), 0,
                                     (struct sockaddr *)&address, sizeof(address));
            if (result < 0) z_fail(line, "Could not send network message");
            return z_game_number(result);
        }
        case Z_GAME_NETWORK_RECEIVE: {
            int handle = z_game_handle(args, 0, Z_GAME_MAX_HANDLES, line, "Invalid network handle");
            if (!z_socket_used[handle]) z_fail(line, "Network socket is not open");
            char buffer[2048];
            int received = (int)recvfrom(z_sockets[handle], buffer, sizeof(buffer) - 1, 0, NULL, NULL);
            if (received < 0) {
#ifdef _WIN32
                if (WSAGetLastError() == WSAEWOULDBLOCK) return z_game_string("");
#else
                if (errno == EAGAIN || errno == EWOULDBLOCK) return z_game_string("");
#endif
                z_fail(line, "Could not receive network message");
            }
            buffer[received] = '\0';
            return z_game_string(z_copy(buffer));
        }
        case Z_GAME_NETWORK_CLOSE: {
            int handle = z_game_handle(args, 0, Z_GAME_MAX_HANDLES, line, "Invalid network handle");
            if (z_socket_used[handle]) {
#ifdef _WIN32
                closesocket(z_sockets[handle]);
#else
                close(z_sockets[handle]);
#endif
                z_socket_used[handle] = false;
            }
            return z_none();
        }
        case Z_GAME_SAVE_NUMBER: {
            double value = z_game_num(args, 2, line);
            if (!isfinite(value)) z_fail(line, "Saved number must be finite");
            char encoded[64];
            int length = snprintf(encoded, sizeof encoded, "%.17g", value);
            if (length < 0 || (size_t)length >= sizeof encoded)
                z_fail(line, "Could not encode saved number");
            z_game_save_value(z_game_str(args, 0, line), z_game_str(args, 1, line),
                              'n', encoded, line);
            return z_none();
        }
        case Z_GAME_LOAD_NUMBER: {
            char value[128];
            if (!z_game_load_value(z_game_str(args, 0, line),
                                   z_game_str(args, 1, line), 'n',
                                   value, sizeof value, line))
                return z_game_number(z_game_num(args, 2, line));
            errno = 0;
            char *end = NULL;
            double parsed = strtod(value, &end);
            if (errno == ERANGE || end == value || *end != '\0' || !isfinite(parsed))
                z_fail(line, "Malformed saved number");
            return z_game_number(parsed);
        }
        case Z_GAME_SAVE_TEXT: {
            char encoded[12288];
            z_game_encode_save_text(z_game_str(args, 2, line), encoded,
                                    sizeof encoded, line);
            z_game_save_value(z_game_str(args, 0, line), z_game_str(args, 1, line),
                              's', encoded, line);
            return z_none();
        }
        case Z_GAME_LOAD_TEXT: {
            char value[4096];
            if (!z_game_load_value(z_game_str(args, 0, line),
                                   z_game_str(args, 1, line), 's',
                                   value, sizeof value, line))
                return z_game_string(z_copy(z_game_str(args, 2, line)));
            return z_game_string(z_copy(value));
        }
        case Z_GAME_SAVE_BOOLEAN: {
            if (args[2].type != Z_BOOLEAN)
                z_fail(line, "Saved boolean value must be boolean");
            z_game_save_value(z_game_str(args, 0, line), z_game_str(args, 1, line),
                              'b', args[2].number != 0 ? "true" : "false", line);
            return z_none();
        }
        case Z_GAME_LOAD_BOOLEAN: {
            char value[16];
            if (!z_game_load_value(z_game_str(args, 0, line),
                                   z_game_str(args, 1, line), 'b',
                                   value, sizeof value, line))
                return z_bool(args[2].number != 0);
            if (strcmp(value, "true") == 0) return z_bool(true);
            if (strcmp(value, "false") == 0) return z_bool(false);
            z_fail(line, "Malformed saved boolean");
            return z_bool(false);
        }
    }
    z_fail(line, "Unknown game API function");
    return z_none();
}

static void z_game_shutdown(void) {
    for (int i = 0; i < Z_GAME_MAX_HANDLES; ++i) {
        if (z_sound_loaded[i]) {
            UnloadSound(z_sounds[i]);
            z_sound_loaded[i] = false;
        }
        if (z_texture_loaded[i]) {
            UnloadTexture(z_textures[i]);
            free(z_texture_paths[i]);
            z_texture_paths[i] = NULL;
            z_texture_loaded[i] = false;
        }
        if (z_socket_used[i]) {
#ifdef _WIN32
            closesocket(z_sockets[i]);
#else
            close(z_sockets[i]);
#endif
            z_socket_used[i] = false;
        }
    }
    if (z_audio_open) {
        CloseAudioDevice();
        z_audio_open = false;
    }
    if (z_window_open) {
        CloseWindow();
        z_window_open = false;
    }
#ifdef _WIN32
    if (z_winsock_open) {
        WSACleanup();
        z_winsock_open = false;
    }
#endif
}
'''

GAME_RUNTIME_C = GAME_RUNTIME_C.replace(
    "    __GAME_FUNCTION_ENUM__",
    ",\n".join(
        f"    Z_GAME_{name.upper()} = {identifier}"
        for name, identifier in GAME_FUNCTION_IDS.items()
    ),
)
