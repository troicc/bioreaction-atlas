#!/bin/zsh
# Open the precomputed offline map; no server or model inference is needed.
set -eu
atlas_root="${0:A:h}"
atlas_map="$atlas_root/outputs/bioreaction_atlas_v02/reference_demo/map/reaction_map.html"
if [[ ! -f "$atlas_map" ]]; then
  print -u2 -- "找不到地图：$atlas_map"
  print -u2 -- "请按照项目 README 中的公开数据演示步骤生成地图。"
  exit 1
fi
exec /usr/bin/open "$atlas_map"
