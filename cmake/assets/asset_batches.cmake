# Bound recipe groups to 32 members; an edit rebuilds at most one group.
function(hg_asset_json_string result value)
    string(REPLACE "\\" "\\\\" value "${value}")
    string(REPLACE "\"" "\\\"" value "${value}")
    string(REPLACE "\n" "\\n" value "${value}")
    string(REPLACE "\r" "\\r" value "${value}")
    string(REPLACE "\t" "\\t" value "${value}")
    set(${result} "\"${value}\"" PARENT_SCOPE)
endfunction()

function(hg_asset_batches target kind work output_dir sources)
    set(common)
    foreach(argument IN LISTS ARGN)
        hg_asset_json_string(quoted "${argument}")
        list(APPEND common "${quoted}")
    endforeach()
    list(JOIN common "," common)
    hg_asset_json_string(work_json "${work}")
    hg_asset_json_string(output_json "${output_dir}")
    list(LENGTH sources total)
    set(index 0)
    set(batch 0)
    set(inputs)
    set(outputs)
    set(byproducts)
    set(source_json)
    foreach(source IN LISTS sources)
        get_filename_component(stem "${source}" NAME_WE)
        list(APPEND inputs "${source}")
        list(APPEND outputs "${output_dir}/${stem}.bin")
        list(APPEND byproducts "${work}/${stem}.o" "${work}/${stem}.d")
        if(kind STREQUAL "zone")
            list(APPEND byproducts "${work}/${stem}.s")
        endif()
        hg_asset_json_string(quoted "${source}")
        list(APPEND source_json "${quoted}")
        math(EXPR index "${index}+1")
        list(LENGTH inputs count)
        if(count EQUAL 32 OR index EQUAL total)
            set(manifest "${work}/batch-${batch}.json")
            set(batch_dep "${work}/batch-${batch}.d")
            list(JOIN source_json "," source_json)
            file(GENERATE OUTPUT "${manifest}" CONTENT
                "{\"kind\":\"${kind}\",\"work\":${work_json},\"output\":${output_json},\"common\":[${common}],\"sources\":[${source_json}]}\n")
            add_custom_command(OUTPUT ${outputs}
                BYPRODUCTS ${byproducts} "${batch_dep}"
                COMMAND "${Python3_EXECUTABLE}" -B "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/build_asset_batch.py"
                    --manifest "${manifest}" --depfile "${batch_dep}"
                DEPENDS ${inputs} "${manifest}" ${hg_asset_batch_dependencies}
                    "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/build_asset_batch.py"
                    "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/build_heartgold_script.py"
                    "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/build_zone_event.py"
                DEPFILE "${batch_dep}"
                COMMENT "Generating ${target}: batch ${batch} (${count} original recipes)"
                VERBATIM)
            math(EXPR batch "${batch}+1")
            set(inputs)
            set(outputs)
            set(byproducts)
            set(source_json)
        endif()
    endforeach()
endfunction()
