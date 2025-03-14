git clone https://github.com/tdlib/td
pushd td
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake -G"Unix Makefiles" ../src
make -j "$(($(nproc)-1))" 
cp libtdjson.so  ../../
popd
