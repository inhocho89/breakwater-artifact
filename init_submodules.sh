#!/bin/sh

set -e

# Initialize submodules
git submodule init
git submodule update --init

# Cloudlab patches to Shenango
echo Applying patch to Shenango
cd shenango
git cherry-pick e3e92a9c2d85b0c6779744ec5042c6f9a641d51f
git apply ../cloudlab_xl170.patch
git apply ../connectx-4.patch
cd ..

echo Done.
