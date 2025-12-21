$baseRoot = "C:\Users\user\Desktop\3DGS실험"
$jpegLevels = @("10", "30", "50", "70", "90")

$scenes = @(
    "1_bicycle",
    "2_bonsai",
    "3_counter",
    "4_flowers",
    "5_garden",
    "6_kitchen",
    "7_room",
    "8_stump",
    "9_treehill"
)

foreach ($qf in $jpegLevels) {

    Write-Host "`n================ JPEG_$qf ================"

    $results = @()

    foreach ($scene in $scenes) {
        $path = Join-Path $baseRoot "JPEG_$qf\$scene\ours_30000\gt\*.png"
        $files = Get-ChildItem $path

        $avgBytes = ($files | Measure-Object Length -Average).Average
        $avgKB = $avgBytes / 1024

        $results += [PSCustomObject]@{
            Scene = $scene
            Avg_KB_per_frame = [Math]::Round($avgKB, 2)
            Num_Frames = $files.Count
        }
    }

    # scene별 결과 출력
    $results | Format-Table -AutoSize

    # 전체 평균
    $overallAvg = ($results | Measure-Object Avg_KB_per_frame -Average).Average
    Write-Host ("Overall Average (JPEG_{0}): {1:N2} KB/frame" -f $qf, $overallAvg)
}

$baseRoot = "C:\Users\user\Desktop\3DGS실험"
$hevcLevels = @(
    "HEVC_27",
    "HEVC_32",
    "HEVC_37",
    "HEVC_42",
    "original_HEVC"
)

$scenes = @(
    "1_bicycle",
    "2_bonsai",
    "3_counter",
    "4_flowers",
    "5_garden",
    "6_kitchen",
    "7_room",
    "8_stump",
    "9_treehill"
)

foreach ($level in $hevcLevels) {

    Write-Host "`n================ $level ================"

    $results = @()

    foreach ($scene in $scenes) {
        $path = Join-Path $baseRoot "$level\$scene\test\ours_30000\*.png"
        $files = Get-ChildItem $path

        $avgBytes = ($files | Measure-Object Length -Average).Average
        $avgKB = $avgBytes / 1024

        $results += [PSCustomObject]@{
            Scene = $scene
            Avg_KB_per_frame = [Math]::Round($avgKB, 2)
            Num_Frames = $files.Count
        }
    }

    # scene별 결과 출력
    $results | Format-Table -AutoSize

    # 전체 평균
    $overallAvg = ($results | Measure-Object Avg_KB_per_frame -Average).Average
    Write-Host ("Overall Average ({0}): {1:N2} KB/frame" -f $level, $overallAvg)
}
