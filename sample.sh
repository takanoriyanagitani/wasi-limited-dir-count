#!/bin/bash

create_testdata(){
	mkdir -p ./test.d
	cd ./test.d

	mkdir -p 2022
	cd 2022

	printf '%02d\n' $( seq 1 12 ) |
	  while read month; do
		  seq 1 31 |
		    xargs printf ${month}/'%02d\n' |
			xargs mkdir -p
	  done
	rmdir --verbose ./0[2469]/31
	rmdir --verbose ./11/31
	rmdir --verbose ./02/{29,30}
}

run_find(){
	time find \
	  test.d \
	    -maxdepth 2 \
		-mindepth 2 \
		-type d |
      wc --lines
}

run_wasmtime(){
	time wasmtime \
	  run \
		--mapdir /guest.d::"${PWD}/test.d" \
		--env ENV_BASE_PATH=/guest.d \
	    ./target/wasm32-wasi/release-wasi/wasi_limited_dir_count.wasm \
		--invoke \
		  count_ymd \
		    2022
}

run_all(){
	pwd
}

run(){
	case $1 in
	  create)
	    create_testdata;;
	  find)
	    run_find;;
	  wasmtime)
	    run_wasmtime;;
      *)
	    run_all;;
	esac
}

run $1
