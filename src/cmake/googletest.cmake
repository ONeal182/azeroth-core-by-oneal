# the following code to fetch googletest
# is inspired by and adapted after https://crascit.com/2015/07/25/cmake-gtest/
# download and unpack googletest at configure time

macro(fetch_googletest _download_module_path _download_root)
    set(GOOGLETEST_DOWNLOAD_ROOT ${_download_root})
    configure_file(
            ${_download_module_path}/googletest-download.cmake
            ${_download_root}/CMakeLists.txt
            @ONLY
    )
    unset(GOOGLETEST_DOWNLOAD_ROOT)

    # Google Test defaults to linking its own static (/MT) CRT on MSVC regardless of the parent
    # project's setting, which this project never overrides elsewhere either - so without this,
    # every gtest-based target (unit_tests, and any module's standalone test executable) fails to
    # link with LNK2038 "RuntimeLibrary mismatch" against game/modules (built with the CMake/MSVC
    # default dynamic CRT, /MD). This is Google Test's own documented fix for exactly this scenario.
    if (MSVC)
        set(gtest_force_shared_crt ON CACHE BOOL "Use shared (DLL) run-time lib even when Google Test is built as static lib" FORCE)
    endif()

    execute_process(
            COMMAND
            "${CMAKE_COMMAND}" -G "${CMAKE_GENERATOR}" .
            WORKING_DIRECTORY
            ${_download_root}
    )
    execute_process(
            COMMAND
            "${CMAKE_COMMAND}" --build .
            WORKING_DIRECTORY
            ${_download_root}
    )

    # adds the targers: gtest, gtest_main, gmock, gmock_main
    add_subdirectory(
            ${_download_root}/googletest-src
            ${_download_root}/googletest-build
    )
endmacro()
