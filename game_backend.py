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
    "draw_cube": 5,
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
}

GAME_FUNCTION_IDS = {name: index for index, name in enumerate(GAME_FUNCTIONS)}


GAME_RUNTIME_C = r'''
#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#endif
#include "raylib.h"
#include <errno.h>
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
#define Z_GAME_MAX_ANIMATION_STATES 32
#define Z_GAME_MAX_ANIMATION_TRANSITIONS 64

enum {
    __GAME_FUNCTION_ENUM__
};

static bool z_window_open = false;
static bool z_audio_open = false;
static Camera3D z_camera = { 0 };
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
    float x, y, width, height, mass, vx, vy;
} ZPhysicsBody;

static ZGameObject z_objects[Z_GAME_MAX_OBJECTS];
static ZGameScene z_scenes[Z_GAME_MAX_SCENES];
static ZPhysicsBody z_bodies[Z_GAME_MAX_OBJECTS];
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
            if (z_window_open) { CloseWindow(); z_window_open = false; }
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
        case Z_GAME_BEGIN_3D:
            z_camera.position = (Vector3){ 8.0f, 8.0f, 8.0f };
            z_camera.target = (Vector3){ 0.0f, 0.0f, 0.0f };
            z_camera.up = (Vector3){ 0.0f, 1.0f, 0.0f };
            z_camera.fovy = 45.0f;
            z_camera.projection = CAMERA_PERSPECTIVE;
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
            if (z_sound_loaded[handle]) { UnloadSound(z_sounds[handle]); z_sound_loaded[handle] = false; }
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
                    z_bodies[i].active = true;
                    z_bodies[i].x = (float)z_game_num(args, 0, line);
                    z_bodies[i].y = (float)z_game_num(args, 1, line);
                    z_bodies[i].width = (float)z_game_num(args, 2, line);
                    z_bodies[i].height = (float)z_game_num(args, 3, line);
                    z_bodies[i].mass = (float)z_game_num(args, 4, line);
                    if (z_bodies[i].mass <= 0) z_fail(line, "Physics body mass must be positive");
                    z_bodies[i].vx = 0;
                    z_bodies[i].vy = 0;
                    return z_game_number(i);
                }
            }
            z_fail(line, "Maximum number of physics bodies reached");
            return z_none();
        case Z_GAME_PHYSICS_SET_GRAVITY:
            z_gravity = (float)z_game_num(args, 0, line);
            return z_none();
        case Z_GAME_PHYSICS_UPDATE: {
            float delta = (float)z_game_num(args, 0, line);
            if (delta < 0 || delta > 0.25f) z_fail(line, "Physics delta must be between 0 and 0.25 seconds");
            for (int i = 0; i < Z_GAME_MAX_OBJECTS; ++i) {
                if (z_bodies[i].active) {
                    z_bodies[i].vy += z_gravity * delta;
                    z_bodies[i].x += z_bodies[i].vx * delta;
                    z_bodies[i].y += z_bodies[i].vy * delta;
                }
            }
            return z_none();
        }
        case Z_GAME_BODY_SET_VELOCITY:
        case Z_GAME_BODY_APPLY_FORCE: {
            int body = z_game_handle(args, 0, Z_GAME_MAX_OBJECTS, line, "Invalid physics body handle");
            if (!z_bodies[body].active) z_fail(line, "Physics body does not exist");
            float x = (float)z_game_num(args, 1, line);
            float y = (float)z_game_num(args, 2, line);
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
    }
    z_fail(line, "Unknown game API function");
    return z_none();
}

static void z_game_shutdown(void) {
    for (int i = 0; i < Z_GAME_MAX_HANDLES; ++i) {
        if (z_sound_loaded[i]) UnloadSound(z_sounds[i]);
        if (z_texture_loaded[i]) {
            UnloadTexture(z_textures[i]);
            free(z_texture_paths[i]);
        }
        if (z_socket_used[i]) {
#ifdef _WIN32
            closesocket(z_sockets[i]);
#else
            close(z_sockets[i]);
#endif
        }
    }
    if (z_audio_open) CloseAudioDevice();
    if (z_window_open) CloseWindow();
#ifdef _WIN32
    if (z_winsock_open) WSACleanup();
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
