#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -n "${VEIL_SRC_DIR:-}" ]]; then
  src_dir="$VEIL_SRC_DIR"
else
  mapfile -t candidates < <(
    find "$repo_root/upstream" -maxdepth 1 -mindepth 1 -type d -name 'firefox*' \
      ! -name 'firefox.incomplete-*' | sort
  )

  src_dir=""
  for candidate in "${candidates[@]}"; do
    if [[ -f "$candidate/browser/config/mozconfigs/linux64/veil" && -x "$candidate/mach" ]]; then
      src_dir="$candidate"
      break
    fi
  done

  if [[ -z "$src_dir" ]]; then
    printf 'No Veil Firefox source tree found under %s/upstream\n' "$repo_root" >&2
    exit 1
  fi
fi

toolchain_root="$repo_root/upstream/toolchain/root"
resource_dir="$(clang --print-resource-dir)"
overlay_dir="$repo_root/upstream/toolchain/local-clang-resource"
wrapper_dir="$repo_root/upstream/toolchain/local-bin"
tmp_root="$repo_root/.tmp-build"
sysroot="$toolchain_root/usr/share/wasi-sysroot"
libclang_path="/usr/lib"
llvm_tool_root="${VEIL_LLVM_TOOL_ROOT:-$HOME/.mozbuild/clang/bin}"
llvm_ar="$llvm_tool_root/llvm-ar"
llvm_nm="$llvm_tool_root/llvm-nm"
llvm_ranlib="$llvm_tool_root/llvm-ranlib"
llvm_objdump="$llvm_tool_root/llvm-objdump"
system_wasi_builtins="$resource_dir/lib/wasm32-unknown-wasi/libclang_rt.builtins.a"
fallback_wasi_builtins="$toolchain_root/usr/lib/clang/21/lib/wasi/libclang_rt.builtins-wasm32.a"

if [[ -f "$system_wasi_builtins" ]]; then
  wasi_builtins="$system_wasi_builtins"
elif [[ -f "$fallback_wasi_builtins" ]]; then
  wasi_builtins="$fallback_wasi_builtins"
else
  printf 'No usable WASI compiler runtime found.\n' >&2
  printf 'Checked:\n  %s\n  %s\n' "$system_wasi_builtins" "$fallback_wasi_builtins" >&2
  exit 1
fi

for tool in "$llvm_ar" "$llvm_nm" "$llvm_ranlib" "$llvm_objdump"; do
  if [[ ! -x "$tool" ]]; then
    printf 'Required LLVM tool not found: %s\n' "$tool" >&2
    exit 1
  fi
done

mkdir -p "$overlay_dir/lib/wasm32-unknown-wasi" "$wrapper_dir" "$tmp_root"
ln -sfn "$resource_dir/include" "$overlay_dir/include"
mkdir -p "$overlay_dir/lib"
if [[ -d "$resource_dir/lib/linux" ]]; then
  ln -sfn "$resource_dir/lib/linux" "$overlay_dir/lib/linux"
fi
ln -sfn "$wasi_builtins" "$overlay_dir/lib/wasm32-unknown-wasi/libclang_rt.builtins.a"

cat > "$wrapper_dir/clang" <<EOF
#!/usr/bin/env bash
set -euo pipefail
extra_flags=()
for arg in "\$@"; do
  if [[ "\$arg" == "--target=wasm32-wasi" ]]; then
    extra_flags+=(-Wno-error=deprecated)
    break
  fi
done
exec /usr/bin/clang -resource-dir=$overlay_dir "\${extra_flags[@]}" "\$@"
EOF

cat > "$wrapper_dir/clang++" <<EOF
#!/usr/bin/env bash
set -euo pipefail
extra_flags=()
for arg in "\$@"; do
  if [[ "\$arg" == "--target=wasm32-wasi" ]]; then
    extra_flags+=(-Wno-error=deprecated)
    break
  fi
done
exec /usr/bin/clang++ -resource-dir=$overlay_dir "\${extra_flags[@]}" "\$@"
EOF

chmod +x "$wrapper_dir/clang" "$wrapper_dir/clang++"

cd "$src_dir"

export PATH="$wrapper_dir:$PATH"
export CC="$wrapper_dir/clang"
export CXX="$wrapper_dir/clang++"
export WASM_CC="$wrapper_dir/clang"
export WASM_CXX="$wrapper_dir/clang++"
export AR="$llvm_ar"
export HOST_AR="$llvm_ar"
export NM="$llvm_nm"
export RANLIB="$llvm_ranlib"
export LLVM_OBJDUMP="$llvm_objdump"
export WASI_SYSROOT="$sysroot"
export CFLAGS="${CFLAGS:--Wno-error=implicit-int-conversion-on-negation}"
export CXXFLAGS="${CXXFLAGS:--Wno-error=implicit-int-conversion-on-negation}"
export MOZCONFIG="$src_dir/browser/config/mozconfigs/linux64/veil"
export TMPDIR="$tmp_root"

printf 'Using source tree: %s\n' "$src_dir"
printf 'Using clang resource dir: %s\n' "$overlay_dir"
printf 'Using WASI builtins: %s\n' "$wasi_builtins"
printf 'Using WASI sysroot: %s\n' "$sysroot"
printf 'Using libclang path: %s\n' "$libclang_path"
printf 'Using LLVM tools from: %s\n' "$llvm_tool_root"

./mach clobber
./mach configure --with-libclang-path="$libclang_path"
./mach build
