#!/bin/bash
# v2 render: resumable (keeps finished frames), then BTS views
M=/tmp/claude-0/-home-user-Morsalinmorsa/256700c8-01bb-53a3-ac0b-4bdd57d2caa1/scratchpad/mc2
cd $M; mkdir -p v2
for k in 1 2 3 4 5 6 7 8; do
  start=$(date +%s)
  RESUME=1 blender -b --factory-startup -P mc.py -- $k $M/v2/out_$k 720 2>&1 | grep -E "SCENE_DONE|Traceback" 
  echo "scene $k took $(( $(date +%s) - start ))s frames=$(ls v2/out_$k | wc -l)" >> v2/render.log
done
echo ALL_DONE >> v2/render.log
for k in 1 2 3 4 5 6 7 8; do RESUME=1 BTS=1 blender -b --factory-startup -P mc.py -- $k $M/v2/view_$k 540 2>&1 | grep -E "SCENE_DONE|Traceback"; done
echo VIEWS_DONE >> v2/render.log
