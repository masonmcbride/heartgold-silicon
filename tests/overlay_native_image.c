/* Synthetic native-image fixture, never linked into the game. */
int overlay_initialized = 0x12345678;
int overlay_bss;
static void (*observer)(void);

static void initialize(void)
{
    ++overlay_bss;
    if (observer) observer();
}

__attribute__((used, section("__DATA,__ntr_sinit")))
static void (*initializers[])(void) = { initialize };

void overlay_set_observer(void (*callback)(void)) { observer = callback; }
void overlay_destructor(void *object) { (void)object; if (observer) observer(); }
int overlay_callback(void) { return overlay_initialized + overlay_bss; }
const struct { int (*callback)(void); } overlay_template = { overlay_callback };

#ifdef UNSUPPORTED_CONSTRUCTOR
__attribute__((constructor)) static void automatic_initialize(void) { ++overlay_bss; }
#endif
