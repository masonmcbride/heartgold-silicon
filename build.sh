#!/bin/bash
# Bootstrap only; the managed interpreter owns progress, logging and validation.
set -eu
source_dir=$(cd -- "$(dirname -- "$0")" && pwd)
binary_dir="$source_dir/build/native"
verbose=0
while [ "$#" -gt 0 ]; do
    case "$1" in
        --build-dir) binary_dir=${2:?--build-dir requires a path}; shift 2 ;;
        --verbose) verbose=1; shift ;;
        --help) echo 'Usage: ./build.sh [--build-dir PATH] [--verbose]'; exit 0 ;;
        *) echo "Unknown argument: $1" >&2; exit 2 ;;
    esac
done
fail() { echo "Error: $*" >&2; exit 1; }
echo 'HeartGold Silicon — ARM64 Build'
echo "Host: $(uname -s) $(uname -m)"
[ "$(uname -s)/$(uname -m)" = Darwin/arm64 ] || fail 'Native macOS ARM64 is required.'
command -v brew >/dev/null || fail 'Homebrew is required. Install it from https://brew.sh, then rerun ./build.sh.'
command -v git >/dev/null || fail 'Git is required. Install Xcode Command Line Tools with xcode-select --install.'
cc=$(xcrun --find clang 2>/dev/null) || fail 'Install Xcode Command Line Tools: xcode-select --install'
cxx=$(xcrun --find clang++ 2>/dev/null) || fail 'Install Xcode Command Line Tools: xcode-select --install'
"$cc" --version | head -1 | grep -q 'Apple clang' || fail 'Apple Clang is required.'
"$cxx" --version >/dev/null || fail 'Apple Clang++ is unusable; run xcode-select --install.'
export SDKROOT=$(xcrun --sdk macosx --show-sdk-path)
[ -d "$SDKROOT" ] || fail 'The macOS SDK is unavailable; run xcode-select --install.'
echo "Toolchain: $("$cc" --version | head -1)"
mkdir -p "$binary_dir"
binary_dir=$(cd -- "$binary_dir" && pwd)
export UV_CACHE_DIR="$binary_dir/bootstrap/cache"
export UV_PYTHON_INSTALL_DIR="$binary_dir/bootstrap/python"
export UV_PYTHON_BIN_DIR="$binary_dir/bootstrap/bin"
mkdir -p "$binary_dir/logs" "$binary_dir/bootstrap/bin"
log="$binary_dir/logs/bootstrap.log"
: > "$log"
child=''
cleanup() { [ -z "$child" ] || kill "$child" 2>/dev/null || :; }
trap 'cleanup; exit 130' INT
trap 'cleanup; exit 143' TERM
run() {
    local label=$1 status=0 tick=0 start=$SECONDS
    shift
    echo "$label"
    if [ "$verbose" = 1 ]; then
        set +e
        "$@" 2>&1 | tee -a "$log"
        status=${PIPESTATUS[0]}
        set -e
        [ "$status" = 0 ] || exit "$status"
        return
    fi
    "$@" >>"$log" 2>&1 & child=$!
    while kill -0 "$child" 2>/dev/null; do
        if [ -t 1 ] && [ "$verbose" = 0 ]; then
            printf '\r\033[2K%s %s | %ss elapsed' "$label" "${spinner:tick%4:1}" "$((SECONDS-start))"
        fi
        tick=$((tick+1)); sleep 0.2
    done
    wait "$child" || status=$?
    child=''
    if [ -t 1 ]; then printf '\r\033[2K'; fi
    echo "$label: exit $status ($((SECONDS-start))s)"
    if [ "$status" -ne 0 ]; then tail -30 "$log" >&2; echo "Full log: $log" >&2; exit "$status"; fi
}
spinner='|/-\'
# Numeric minimums avoid reinstalling compatible tools.
compatible() {
    command -v "$1" >/dev/null || return 1
    local version major minor
    version=$("$1" --version | head -1 | sed -E 's/[^0-9]*([0-9]+\.[0-9]+).*/\1/')
    major=${version%%.*}; minor=${version#*.}
    [ "$major" -gt "$2" ] || { [ "$major" -eq "$2" ] && [ "$minor" -ge "$3" ]; }
}
missing=()
compatible cmake 3 30 || missing+=(cmake)
compatible ninja 1 10 || missing+=(ninja)
if [ "${#missing[@]}" -gt 0 ]; then run 'Native tools' brew install "${missing[@]}"; fi
compatible cmake 3 30 && compatible ninja 1 10 || fail 'CMake >=3.30 and Ninja >=1.10 must be on PATH.'
echo "Tools: $(cmake --version | head -1), Ninja $(ninja --version)"
# LLVM supplies object utilities for original assets, never the host compiler.
llvm_prefix=$(brew --prefix llvm 2>/dev/null || :)
if ! { command -v llvm-objcopy >/dev/null && command -v llvm-readelf >/dev/null; } &&
   ! { [ -x "$llvm_prefix/bin/llvm-objcopy" ] && [ -x "$llvm_prefix/bin/llvm-readelf" ]; }; then
    run 'Asset object tools' brew install llvm
fi
png_prefix=$(brew --prefix libpng 2>/dev/null || :)
if [ ! -f "$png_prefix/include/png.h" ]; then run 'PNG asset tools' brew install libpng; fi
uv_tool=$(command -v uv || :)
if ! compatible "${uv_tool:-uv}" 0 9; then uv_tool="$binary_dir/bootstrap/bin/uv"; fi
if ! compatible "$uv_tool" 0 9; then
    run 'Download uv installer' curl --fail --location --silent --show-error https://astral.sh/uv/0.9.5/install.sh -o "$binary_dir/bootstrap/install-uv.sh"
    run 'Install uv' env UV_UNMANAGED_INSTALL="$binary_dir/bootstrap/bin" sh "$binary_dir/bootstrap/install-uv.sh"
    uv_tool="$binary_dir/bootstrap/bin/uv"
fi
"$uv_tool" --version || fail 'uv installation failed.'
run 'CPython 3.12.12' "$uv_tool" python install 3.12.12
python=$("$uv_tool" python find --managed-python 3.12.12)
[ "$("$python" -c 'import platform; print(platform.python_version())')" = 3.12.12 ] || fail 'Unexpected managed Python version.'
echo "Python: $python"
trap - INT TERM
export HEARTGOLD_BOOTSTRAP_SECONDS=$SECONDS
exec "$python" -B "$source_dir/tools/profile_build.py" --build "$binary_dir" --compiler "$cc" --cxx "$cxx" --verbose "$verbose"
