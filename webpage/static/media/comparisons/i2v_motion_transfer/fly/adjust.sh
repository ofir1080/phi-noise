# 1. Grab the very first MOV in the folder
FIRST_VID=$(ls *.mov | head -n 1)

# 2. Extract the Master File's duration, width, and height
TARGET_DUR=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$FIRST_VID")
TARGET_W=$(ffprobe -v error -select_streams v:0 -show_entries stream=width -of default=noprint_wrappers=1:nokey=1 "$FIRST_VID")
TARGET_H=$(ffprobe -v error -select_streams v:0 -show_entries stream=height -of default=noprint_wrappers=1:nokey=1 "$FIRST_VID")

# 3. Loop through all videos and apply the Master File's properties
for f in *.mov; do
    DUR=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$f")
    RATIO=$(awk "BEGIN {print $TARGET_DUR / $DUR}")
    
    ffmpeg -i "$f" -filter:v "scale=${TARGET_W}:${TARGET_H}:flags=bilinear,setsar=1,setpts=${RATIO}*PTS" -an -c:v libvpx-vp9 -crf 30 -b:v 0 "matched_${f%.*}.webm"
done