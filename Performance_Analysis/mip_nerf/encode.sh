# [폴더 먼저 생성]
mkdir -p /mnt/c/Users/PC012/Desktop/dataset/recon
mkdir -p /mnt/c/Users/PC012/Desktop/dataset/bitstream
mkdir -p /mnt/c/Users/PC012/Desktop/dataset/coding_log

# 설정
qps=(27 32 37 42)
inputs=(
"stump 126 622 413"
"bonsai 292 390 260"
"kitchen 279 389 260"
"counter 240 389 260"
"room 311 389 259"
"garden 185 648 420"
"bicycle 195 618 411"
"flowers 173 628 414"
"treehill 141 634 416"
)
encoder="/root/HM/bin/umake/gcc-11.4/x86_64/release/TAppEncoder"
cfg="/root/HM/cfg/encoder_randomaccess_main.cfg"

# 시스템 코어 수 자동 감지
n_cores=$(nproc)
core_list=($(seq 0 $((n_cores-1))))

task_count=0

for input_info in "${inputs[@]}"; do
    name=$(echo "$input_info" | awk '{print $1}')
    frames=$(echo "$input_info" | awk '{print $2}')
    width=$(echo "$input_info" | awk '{print $3}')
    height=$(echo "$input_info" | awk '{print $4}')

    for idx in "${!qps[@]}"; do
        qp=${qps[$idx]}

        input="/mnt/c/Users/PC012/Desktop/dataset/yuv/${name}.yuv"
        recon="/mnt/c/Users/PC012/Desktop/dataset/recon/${name}_qp${qp}.yuv"
        bin="/mnt/c/Users/PC012/Desktop/dataset/bitstream/${name}_qp${qp}.bin"
        log="/mnt/c/Users/PC012/Desktop/dataset/coding_log/${name}_qp${qp}.log"

        # 할당할 코어 번호 계산
        core_idx=$((task_count % n_cores))
        core=${core_list[$core_idx]}

        # 개별 작업 실행 + 로그 저장
        {
            echo "=== $(date) START name=${name} qp=${qp} (idx=${idx}) core=${core} frames=${frames} ==="
            taskset -c "$core" "$encoder" \
                -c "$cfg" \
                -i "$input" -o "$recon" -wdt "$width" -hgt "$height" \
                -b "$bin" -q "$qp" -fr 30 -f "$frames"
            ret=$?
            echo "=== $(date) END name=${name} qp=${qp} status=${ret} ==="
        } > "$log" 2>&1 &

        ((task_count++))

        # 동시에 n_cores개까지만 실행되도록 제어
        if (( $(jobs -r | wc -l) >= n_cores )); then
            wait -n
        fi
    done
done

# 남은 모든 작업 기다림
wait
echo "모든 인코딩 작업이 완료되었습니다."
