# Discover generated overlay parts after their dispatcher has been generated.
# A configure-time glob cannot see the first build's parts (nor safely handle
# parts removed during that build). Fixed wrapper outputs make the build graph
# complete before code generation, while retaining parallel C compilation.
if(PSX_STAGE_STATIC_OVERLAY_PARTS)
    get_filename_component(_dir "${PSX_OVERLAY_DISPATCH}" DIRECTORY)
    get_filename_component(_stem "${PSX_OVERLAY_DISPATCH}" NAME_WE)
    file(GLOB _candidates "${_dir}/${_stem}_[0-9][0-9][0-9][0-9]*.c")
    set(_parts)
    string(LENGTH "${_stem}_" _prefix_length)
    foreach(_candidate IN LISTS _candidates)
        get_filename_component(_name "${_candidate}" NAME)
        string(SUBSTRING "${_name}" ${_prefix_length} -1 _suffix)
        if(_suffix MATCHES "^[0-9][0-9][0-9][0-9][0-9]*\\.c$")
            list(APPEND _parts "${_candidate}")
        endif()
    endforeach()
    list(SORT _parts)
    math(EXPR _last "${PSX_OVERLAY_PART_GROUPS} - 1")
    foreach(_index RANGE 0 ${_last})
        set(_text_${_index} "/* Generated static overlay compilation group. */\ntypedef int psx_overlay_nonempty_translation_unit;\n")
    endforeach()
    set(_index 0)
    foreach(_part IN LISTS _parts)
        file(TO_CMAKE_PATH "${_part}" _include)
        # Include a content identity so build-tool restat cannot cancel this
        # group's compilation when codegen changed a part during this build.
        file(SHA256 "${_part}" _hash)
        string(APPEND _text_${_index} "/* ${_hash} */\n#include \"${_include}\"\n")
        math(EXPR _index "(${_index} + 1) % ${PSX_OVERLAY_PART_GROUPS}")
    endforeach()
    file(MAKE_DIRECTORY "${PSX_OVERLAY_GROUP_DIR}")
    foreach(_index RANGE 0 ${_last})
        set(_path "${PSX_OVERLAY_GROUP_DIR}/part_${_index}.c")
        set(_previous "")
        if(EXISTS "${_path}")
            file(READ "${_path}" _previous)
        endif()
        if(NOT _previous STREQUAL _text_${_index})
            file(WRITE "${_path}" "${_text_${_index}}")
        endif()
    endforeach()
    return()
endif()

function(psxrecomp_static_overlay_parts out_var target dispatcher)
    set(_groups 32)
    set(_dir "${CMAKE_CURRENT_BINARY_DIR}/psx_static_overlay_parts/${target}")
    set(_sources)
    math(EXPR _last "${_groups} - 1")
    foreach(_index RANGE 0 ${_last})
        list(APPEND _sources "${_dir}/part_${_index}.c")
    endforeach()
    set(_script "${CMAKE_CURRENT_FUNCTION_LIST_FILE}")
    add_custom_command(OUTPUT ${_sources}
        COMMAND "${CMAKE_COMMAND}"
            "-DPSX_STAGE_STATIC_OVERLAY_PARTS=ON"
            "-DPSX_OVERLAY_DISPATCH=${dispatcher}"
            "-DPSX_OVERLAY_PART_GROUPS=${_groups}"
            "-DPSX_OVERLAY_GROUP_DIR=${_dir}"
            -P "${_script}"
        DEPENDS "${dispatcher}" "${_script}"
        COMMENT "Preparing generated static overlay compilation groups"
        VERBATIM)
    set(${out_var} ${_sources} PARENT_SCOPE)
endfunction()
