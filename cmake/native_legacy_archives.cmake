# Temporary bridge for six historical WM/WVR/DWC archives.
# These archives are NOT built from source by the current CMake graph.
# Keep the precise original link order while source-owning their providers.
# Do not copy the archives into the source tree or call this reproducible.

set(_hg_wm_archive_dir "${PROJECT_BINARY_DIR}/wm-39-package")
set(_hg_dwc_archive_dir "${PROJECT_BINARY_DIR}/dwc-9-storage")
set(_hg_legacy_archives
    "${_hg_wm_archive_dir}/libheartgold_wm_core_native_original.a"
    "${_hg_wm_archive_dir}/libheartgold_wm_native_candidates.a"
    "${_hg_wm_archive_dir}/libheartgold_wvr_original.a"
    "${_hg_wm_archive_dir}/libheartgold_wm_original_work_storage.a"
    "${_hg_wm_archive_dir}/libheartgold_wm_original_scalar_storage.a"
    "${_hg_dwc_archive_dir}/libheartgold_dwc_original_typed_storage.a"
)

# A missing legacy input is an incomplete build graph, not an excuse to
# silently omit the symbol provider or fall back to an old executable.
foreach(_hg_archive IN LISTS _hg_legacy_archives)
    if(NOT EXISTS "${_hg_archive}")
        message(FATAL_ERROR
            "Native overlay integration requires an undeclared historical archive:\n"
            "  ${_hg_archive}\n"
            "This build path is not yet reproducible from an empty build directory.\n"
            "Migrate its original source owner into a declared CMake target; "
            "do not copy a checkpoint archive. See docs/BUILD_GRAPH.md.")
    endif()
endforeach()

# The original archive order remains unchanged during the migration.
target_link_libraries(heartgold PRIVATE
    "${_hg_wm_archive_dir}/libheartgold_wm_core_native_original.a"
    "${_hg_wm_archive_dir}/libheartgold_wm_native_candidates.a"
    "${_hg_wm_archive_dir}/libheartgold_wvr_original.a"
)

# Original native gWmWork owner must remain exported from this image.
target_link_options(hg_wm_arm9 PRIVATE "LINKER:-exported_symbol,_gWmWork")
target_link_libraries(heartgold PRIVATE
    "${_hg_wm_archive_dir}/libheartgold_wm_original_work_storage.a"
    "${_hg_wm_archive_dir}/libheartgold_wm_original_scalar_storage.a"
)

target_link_libraries(heartgold PRIVATE
    "${_hg_dwc_archive_dir}/libheartgold_dwc_original_typed_storage.a"
)

unset(_hg_wm_archive_dir)
unset(_hg_dwc_archive_dir)
unset(_hg_legacy_archives)
unset(_hg_archive)
