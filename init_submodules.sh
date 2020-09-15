#!/bin/sh

set -e

# Initialize submodules
git submodule init
git submodule update --init

# Cloudlab patches to Shenango
echo Applying patch to Shenango
cd shenango
git apply ../cloudlab_xl170.patch
git apply ../connectx-4.patch
cd ..

echo Done.
