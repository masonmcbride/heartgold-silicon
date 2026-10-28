#include <nitro/mi/uncompress.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>

#define CHECK(e) do { if (!(e)) { fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #e); exit(1); } } while (0)

/* Independently hand-encoded: literals C,B,A; length-18/distance-3 match;
 * length-3/distance-3 match. The expected 24 bytes are eight copies of ABC.
 * Flag 0x18 is consumed MSB first; the final three flag bits are unused. */
static const uint8_t abc_blz[] = {
    0x00,0x00,0x00,0xf0,0x41,0x42,0x43,0x18,
    0x10,0x00,0x00,0x08,0x08,0x00,0x00,0x00
};
static const uint8_t abc_raw[] = "ABCABCABCABCABCABCABCABC";

static void reference(const char *tool, const uint8_t *encoded, size_t encoded_size,
                      const uint8_t *expected, size_t expected_size)
{
    char path[] = "blz-reference-XXXXXX";
    int fd = mkstemp(path);
    CHECK(fd >= 0);
    FILE *file = fdopen(fd, "wb");
    CHECK(file && fwrite(encoded, 1, encoded_size, file) == encoded_size);
    CHECK(fclose(file) == 0);
    char size[32];
    snprintf(size, sizeof(size), "%zu", encoded_size);
    pid_t child = fork();
    CHECK(child >= 0);
    if (!child) { execl(tool, tool, path, "0", size, (char *)NULL); _exit(127); }
    int status;
    CHECK(waitpid(child, &status, 0) == child && WIFEXITED(status) && WEXITSTATUS(status) == 0);
    file = fopen(path, "rb");
    CHECK(file);
    for (size_t i = 0; i < expected_size; ++i) CHECK(fgetc(file) == expected[i]);
    CHECK(fgetc(file) == EOF);
    CHECK(fclose(file) == 0 && unlink(path) == 0);
}

static void check_image(const uint8_t *encoded, size_t encoded_size,
                        const uint8_t *expected, size_t expected_size)
{
    CHECK(encoded_size <= expected_size);
    /* Exercise every address residue within a DS cache line, including unaligned
     * native footer loads. Canaries surround the exact caller-owned image. */
    for (unsigned offset = 0; offset < 32; ++offset) {
        size_t guard = 32 + offset;
        uint8_t *allocation = malloc(guard + expected_size + 32);
        CHECK(allocation && (uintptr_t)allocation > UINT32_MAX);
        memset(allocation, 0xa5, guard + expected_size + 32);
        uint8_t *image = allocation + guard;
        memcpy(image, encoded, encoded_size);
        MIi_UncompressBackward(image + encoded_size);
        CHECK(memcmp(image, expected, expected_size) == 0);
        for (size_t i = 0; i < guard; ++i) CHECK(allocation[i] == 0xa5);
        for (size_t i = 0; i < 32; ++i) CHECK(image[expected_size + i] == 0xa5);
        free(allocation);
    }
}

static void le32(uint8_t *p, uint32_t word)
{
    for (unsigned i = 0; i < 4; ++i) p[i] = (uint8_t)(word >> (8 * i));
}
struct Token { unsigned literal, length, distance; };

/* This fixture writer serializes explicitly supplied tokens. It performs no
 * compression search and contains no decoder; expected bytes are supplied
 * independently by the tests below. */
static size_t encode(const struct Token *tokens, size_t count, size_t raw_size,
                     unsigned prefix, unsigned padding, uint8_t *encoded)
{
    uint8_t read_order[32768];
    size_t used = 0;
    for (size_t first = 0; first < count; first += 8) {
        size_t flags = used++;
        read_order[flags] = 0;
        for (unsigned bit = 0; bit < 8 && first + bit < count; ++bit) {
            const struct Token *token = &tokens[first + bit];
            if (!token->length) {
                read_order[used++] = (uint8_t)token->literal;
            } else {
                CHECK(token->length >= 3 && token->length <= 18);
                CHECK(token->distance >= 3 && token->distance <= 4098);
                read_order[flags] |= 0x80 >> bit;
                unsigned code = ((token->length - 3) << 12) | (token->distance - 3);
                read_order[used++] = code >> 8;
                read_order[used++] = code;
            }
        }
    }
    CHECK(used < sizeof(read_order));
    unsigned header = 8 + padding;
    size_t span = used + header;
    CHECK(raw_size >= span && span <= 0xffffff && header <= 255);
    for (unsigned i = 0; i < prefix; ++i) encoded[i] = (uint8_t)(0xd0 + i);
    for (size_t i = 0; i < used; ++i) encoded[prefix + i] = read_order[used - 1 - i];
    memset(encoded + prefix + used, 0xff, padding);
    le32(encoded + prefix + used + padding, (uint32_t)span | ((uint32_t)header << 24));
    le32(encoded + prefix + used + padding + 4, (uint32_t)(raw_size - span));
    return prefix + span;
}

int main(int argc, char **argv)
{
    CHECK(argc == 2);
    MIi_UncompressBackward(NULL);
    check_image(abc_blz, sizeof(abc_blz), abc_raw, sizeof(abc_raw) - 1);
    reference(argv[1], abc_blz, sizeof(abc_blz), abc_raw, sizeof(abc_raw) - 1);

    struct Token tokens[5000] = {0};
    uint8_t encoded[32768], expected[32768];
    /* Full flag groups plus a partial final group, a nonperiodic 4098-byte seed,
     * and the maximum encoded distance/length. Known expected bytes follow the
     * seed's explicit 4098-byte period, rather than another decompressor. */
    for (unsigned i = 0; i < 4098; ++i) tokens[i].literal = i % 251;
    for (unsigned i = 4098; i < 4162; ++i) tokens[i] = (struct Token){ .length = 18, .distance = 4098 };
    const size_t raw_size = 4098 + 64 * 18;
    for (unsigned padding = 0; padding <= 3; ++padding) {
        unsigned prefix = 7;
        size_t size = encode(tokens, 4162, raw_size, prefix, padding, encoded);
        for (unsigned i = 0; i < prefix; ++i) expected[i] = (uint8_t)(0xd0 + i);
        for (size_t i = 0; i < raw_size; ++i) expected[prefix + raw_size - 1 - i] = (i % 4098) % 251;
        check_image(encoded, size, expected, prefix + raw_size);
        reference(argv[1], encoded, size, expected, prefix + raw_size);
    }

    /* All eight flag bits set, consecutive overlapping matches (distance 3),
     * and alternating flag-byte boundaries with a single repeated symbol. */
    memset(tokens, 0, sizeof(tokens));
    for (unsigned i = 0; i < 3; ++i) tokens[i].literal = 'Q';
    for (unsigned i = 3; i < 35; ++i) tokens[i] = (struct Token){ .length = 18, .distance = 3 };
    size_t size = encode(tokens, 35, 3 + 32 * 18, 0, 2, encoded);
    memset(expected, 'Q', 3 + 32 * 18);
    check_image(encoded, size, expected, 3 + 32 * 18);
    reference(argv[1], encoded, size, expected, 3 + 32 * 18);

    /* Header-only images and a maximum 8-bit header length: no decode writes. */
    for (unsigned header = 8; header <= 255; header += header == 8 ? 247 : 1) {
        memset(encoded, 0xff, header);
        le32(encoded + header - 8, header | (header << 24));
        le32(encoded + header - 4, 0);
        memcpy(expected, encoded, header);
        check_image(encoded, header, expected, header);
    }
    /* This SDK API does NOT have the file utilities' extraSize==0 shortcut. */
    const uint8_t zero_growth[] = { 'Z',0, 10,0,0,8, 0,0,0,0 };
    memcpy(expected, zero_growth, sizeof(zero_growth));
    expected[sizeof(zero_growth) - 1] = 'Z';
    check_image(zero_growth, sizeof(zero_growth), expected, sizeof(zero_growth));

    /* Input exhaustion, not the output cursor, terminates the assembly. */
    const uint8_t partial[] = { 'R',0, 10,0,0,8, 4,0,0,0 };
    memcpy(expected, partial, sizeof(partial));
    memset(expected + sizeof(partial), 0xa5, 4);
    expected[13] = 'R';
    check_image(partial, sizeof(partial), expected, 14);
    puts("Backward decompression: PASS (known bytes, reference tool, overlap, 3..18-byte matches, distance 4098, flags, padding, prefix, unaligned/native pointers, SDK boundaries)");
    return 0;
}
