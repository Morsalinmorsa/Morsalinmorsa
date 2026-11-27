cd /tmp/claude-0/-home-user-Morsalinmorsa/256700c8-01bb-53a3-ac0b-4bdd57d2caa1/scratchpad/mc2
for k in 3 5 6 8; do s=$(date +%s); RESUME=1 blender -b --factory-startup -P mc.py -- $k /tmp/claude-0/-home-user-Morsalinmorsa/256700c8-01bb-53a3-ac0b-4bdd57d2caa1/scratchpad/mc2/v3/out_$k 720 2>&1 | grep -E "SCENE_DONE|Traceback"; echo "scene $k took $(($(date +%s)-s))s frames=$(ls /tmp/claude-0/-home-user-Morsalinmorsa/256700c8-01bb-53a3-ac0b-4bdd57d2caa1/scratchpad/mc2/v3/out_$k|wc -l)" >> v3/render.log; done
echo ALL_DONE
for k in 3 5 6 8; do RESUME=1 BTS=1 blender -b --factory-startup -P mc.py -- $k /tmp/claude-0/-home-user-Morsalinmorsa/256700c8-01bb-53a3-ac0b-4bdd57d2caa1/scratchpad/mc2/v3/view_$k 540 2>&1 | grep -E "SCENE_DONE|Traceback"; done
echo VIEWS_DONE
