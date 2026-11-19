/* Reuse Nitroarc's original index writer, without reading member payloads.
 * The included source retains its LGPL-3.0-or-later copyright and notices. */
#include "nitroarc/src/opmode_create.c"

int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "usage: nitroarc-index archive-path ordered-member-list\n");
        return EXIT_FAILURE;
    }
    char *data = NULL;
    size_t size = 0;
    if (load_file(argv[2], &data, &size)) return EXIT_FAILURE;
    strvec_t files = {.data = malloc(64 * sizeof(char *)), .cap = 64};
    char *cursor = data;
    int status = EXIT_FAILURE;
    if (!files.data || strlen(data) != size) goto done;
    while (*cursor) {
        char *name = cursor;
        char *end = strchr(cursor, '\n');
        if (end) { *end = 0; cursor = end + 1; }
        else cursor += strlen(cursor);
        /* All callers supply original flat, ordered archive member names. */
        if (!*name || strchr(name, '/') || strchr(name, '\\') ||
            strchr(name, '\r') || strvec_has(&files, name)) goto done;
        if (strvec_push(&files, name)) goto done;
    }
    if (!files.size) goto done;
    status = write_index(argv[1], true, true, &files);
done:
    free(files.data);
    free(data);
    return status;
}
