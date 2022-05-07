import functools
import operator
import os

import wasmtime

import wasmer
import wasmer_compiler_cranelift

getenv_or_alt = lambda key, alt: os.getenv(key) or alt

get_data_dir    = functools.partial(getenv_or_alt, "ENV_BASE_PATH",  "./test.d"   )
get_module_path = functools.partial(getenv_or_alt, "ENV_MODULE_LOC", "./test.wasm")
get_year        = functools.partial(getenv_or_alt, "ENV_YEAR",       "2022"       )

def new_fs_counter_wasi_wasmtime(mpath):
  engine = wasmtime.Engine()
  linker = wasmtime.Linker(engine)
  linker.define_wasi()
  module = wasmtime.Module.from_file(engine, mpath)
  store = wasmtime.Store(engine)
  cfg = wasmtime.WasiConfig()
  return lambda dat_root: functools.reduce(
    lambda state, f: f(state),
	[
	  lambda _: cfg.preopen_dir(dat_root, "/guest.d"),
	  lambda _: store.set_wasi(cfg),
	  lambda _: linker.instantiate(store, module),
	  lambda instance: instance.exports(store)["count_ymd"],
	  lambda counter: functools.partial(counter, store),
	],
	None
  )

def path2bytes(loc):
  with open(loc, "rb") as f:
    return f.read()

def new_fs_counter_wasi_wasmer(mpath):
  compiler = wasmer_compiler_cranelift.Compiler
  engine = wasmer.engine.Universal(compiler)
  store = wasmer.Store(engine)
  module = wasmer.Module(store, path2bytes(mpath))
  wver = wasmer.wasi.get_version(module, strict=True)
  return lambda dat_root: functools.reduce(
    lambda state, f: f(state),
	[
	  lambda _: wasmer.wasi.StateBuilder("counter"),
	  lambda builder: builder.map_directory("/guest.d", dat_root),
	  lambda builder: builder.finalize(),
	  lambda wenv: wenv.generate_import_object(store, wver),
	  lambda obj: wasmer.Instance(module, obj),
	  lambda instance: instance.exports.count_ymd,
	  lambda counter: counter,
	],
	None
  )

def print_count(year, counter):
  cnt = counter(year)
  print(cnt)

def main():
  mpath = get_module_path()
  droot = get_data_dir()
  year = int(get_year())

  fs_counter_builder_wasmer = new_fs_counter_wasi_wasmer(mpath)
  fs_counter_wasmer = fs_counter_builder_wasmer(droot)

  fs_counter_builder_wasmtime = new_fs_counter_wasi_wasmtime(mpath)
  fs_counter_wasmtime = fs_counter_builder_wasmtime(droot)

  print_count(year, fs_counter_wasmtime)
  print_count(year, fs_counter_wasmer)

main()
