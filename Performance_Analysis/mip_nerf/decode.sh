videos=(
"1_bicycle bicycle 618 411"
"2_bonsai bonsai 390 260"
"3_counter counter 389 260"
"4_flowers flowers 628 414"
"5_garden garden 648 420"
"6_kitchen kitchen 389 260"
"7_room room 389 259"
"8_stump stump 622 413"
"9_treehill treehill 634 416"
)

qps=(27 32 37 42)

for v in "${videos[@]}"; do
    folder=$(echo $v | awk '{print $1}')  # 1_bicycle
    file=$(echo $v | awk '{print $2}')    # bicycle
    width=$(echo $v | awk '{print $3}')
    height=$(echo $v | awk '{print $4}')

    for qp in "${qps[@]}"; do
        mkdir -p /mnt/c/Users/PC012/Desktop/dataset/${qp}/${folder}/images

        ffmpeg -f rawvideo -pix_fmt yuv444p -s ${width}x${height} \
            -i /mnt/c/Users/PC012/Desktop/dataset/recon/${file}_qp${qp}.yuv \
            /mnt/c/Users/PC012/Desktop/dataset/${qp}/${folder}/images/img_%06d.png
    done
done
