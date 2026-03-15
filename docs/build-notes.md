# Veil Build Notes

Status for this note: `2026-03-14`, Linux x86_64 workspace build attempt.

## Upstream source

- Source acquisition method: pinned GitHub codeload archive
- Upstream commit: `16a7dee3ca6fb0967cd84314393ad1d2e213e4a6`
- Working source tree: `upstream/firefox`

## Local toolchain staging

This environment could not complete a reliable Firefox checkout-and-build flow using the default system compiler plus a blobless clone. Veil currently stages a local toolchain under `upstream/toolchain/root` using locally available Arch packages and extracted WASI support files.

Key staged tools used by the current configure/build flow:

- `clang`, `clang++`
- `llvm-objdump`, `llvm-ar`, `llvm-nm`, `llvm-strip`
- `cbindgen`
- `nasm`
- WASI sysroot and compiler runtime libraries

## Reproducible configure command

```bash
PATH=/home/null2ud/Projects/Veil/upstream/toolchain/root/usr/bin:$PATH \
CC=/home/null2ud/Projects/Veil/upstream/toolchain/root/usr/bin/clang \
CXX=/home/null2ud/Projects/Veil/upstream/toolchain/root/usr/bin/clang++ \
WASM_CC=/home/null2ud/Projects/Veil/upstream/toolchain/root/usr/bin/clang \
WASM_CXX=/home/null2ud/Projects/Veil/upstream/toolchain/root/usr/bin/clang++ \
LLVM_OBJDUMP=/home/null2ud/Projects/Veil/upstream/toolchain/root/usr/bin/llvm-objdump \
WASI_SYSROOT=/home/null2ud/Projects/Veil/upstream/toolchain/root/usr/share/wasi-sysroot \
CFLAGS='-Wno-error=implicit-int-conversion-on-negation' \
CXXFLAGS='-Wno-error=implicit-int-conversion-on-negation' \
MOZCONFIG=browser/config/mozconfigs/linux64/veil \
./mach configure
```

## Build issues addressed in this run

1. System `clang` found the staged WASI headers but still linked against `/usr/lib/clang/21/...` builtins. Staging a matching local `clang` package under `upstream/toolchain/root` resolved the configure-time WASI probe failure.
2. `glslopt` failed on current glibc headers because its bundled C11 threads shim redefined `once_flag` and `call_once`. Veil now carries `VEIL-0150`, which path-patches the vendored `glslopt` crate and guards the conflicting definitions.
3. Clang 21 promoted `-Wimplicit-int-conversion-on-negation` to an error for generated Servo style constants in this environment. A compiler-flag-only workaround was not sufficient because Firefox also passes `-Werror=implicit-int-conversion` for the affected compile.
4. Veil now carries `VEIL-0160`, which patches `servo/ports/geckolib/cbindgen.toml` so `ShadowCascadeOrder()` is emitted with an explicit signed cast. An isolated compile of `dom/canvas/DrawTargetWebgl.cpp` succeeded after regenerating `ServoStyleConsts.h`.
5. The current build invocation still includes `CFLAGS` and `CXXFLAGS` with `-Wno-error=implicit-int-conversion-on-negation` while this Linux toolchain path is being proven end to end.

## Current evidence

- `obj-veil/config.status.json` records:
  - `MOZ_DATA_REPORTING=1`
  - the extra Clang 21 warning suppression in both `OS_CFLAGS` and `OS_CXXFLAGS`
- `obj-veil/.mozconfig.json` records the Veil mozconfig path and the current configure environment additions.
- `scripts/verify_telemetry_runtime.py upstream/firefox/obj-veil` currently passes objdir-backed checks for:
  - explicit `MOZ_TELEMETRY_REPORTING=` in the Veil mozconfig
  - absence of `MOZ_TELEMETRY_REPORTING`, `MOZ_SERVICES_HEALTHREPORT`, and `MOZ_NORMANDY` defines in `config.status.json`
  - explicit warning that `MOZ_DATA_REPORTING` remains defined
- The same verification run warns that packaged `firefox.js`, `greprefs.js`, and the preprocessed preferences UI were not present yet, so the current evidence is stronger than source-only but still not a completed runtime proof.

## Build result

- `2026-03-14`: `./mach build` completed successfully for the Veil Linux x86_64 objdir.
- Built runtime path:
  - `upstream/firefox/obj-veil/dist/bin/firefox`
  - `upstream/firefox/obj-veil/dist/bin/firefox-bin`
  - `upstream/firefox/obj-veil/dist/bin/libxul.so`
  - `upstream/firefox/obj-veil/dist/bin/xpcshell`
- Direct runtime invocation from the objdir currently uses:

```bash
cd /home/null2ud/Projects/Veil/upstream/firefox/obj-veil/dist/bin
LD_LIBRARY_PATH=$PWD ./firefox --version
```

- Observed result:

```text
Mozilla Firefox 150.0a1
```

## Post-build fix

- Build-backed verification showed that `Normandy.init` was compiled out of the installed `BrowserComponents.manifest`, but `Normandy.uninit` was still present.
- Veil now folds that manifest guard into `VEIL-0100` and refreshes `browser/components` with:

```bash
PATH=/home/null2ud/Projects/Veil/upstream/toolchain/root/usr/bin:$PATH \
CC=/home/null2ud/Projects/Veil/upstream/toolchain/root/usr/bin/clang \
CXX=/home/null2ud/Projects/Veil/upstream/toolchain/root/usr/bin/clang++ \
WASM_CC=/home/null2ud/Projects/Veil/upstream/toolchain/root/usr/bin/clang \
WASM_CXX=/home/null2ud/Projects/Veil/upstream/toolchain/root/usr/bin/clang++ \
LLVM_OBJDUMP=/home/null2ud/Projects/Veil/upstream/toolchain/root/usr/bin/llvm-objdump \
WASI_SYSROOT=/home/null2ud/Projects/Veil/upstream/toolchain/root/usr/share/wasi-sysroot \
CFLAGS='-Wno-error=implicit-int-conversion-on-negation' \
CXXFLAGS='-Wno-error=implicit-int-conversion-on-negation' \
MOZCONFIG=browser/config/mozconfigs/linux64/veil \
./mach build --allow-subdirectory-build browser/components
```

## Verified post-build state

- `scripts/verify_telemetry_runtime.py upstream/firefox/obj-veil` now passes against the finished build with these caveats:
  - `MOZ_DATA_REPORTING` remains enabled because crashreporter still contributes to the upstream aggregate flag.
  - The finished package exposes built `firefox.js`, `greprefs.js`, `BrowserComponents.manifest`, and a usable `xpcshell` AppConstants probe.
  - The verification script still warns that `privacy.inc.xhtml` was not found as a standalone installed artifact.
- Clean-profile headless startup works, but it writes telemetry- and experiment-related local state. That means the current Veil milestone is build-backed and measurable, not a finished zero-telemetry product claim.
